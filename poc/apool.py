import asyncio
from contextlib import asynccontextmanager
from time import monotonic
from weakref import ReferenceType, ref

from pysqlx_engine import PySQLXEngine

from .base import BaseConnInfo, BaseMonitor, BasePool, Worker, logger
from .errors import PoolAlreadyStarted, PoolTimeout
from .util import asleep, aspawn


### Async Pool
class ConnInfo(BaseConnInfo):
	async def close(self) -> None:
		return await super()._aclose()


class Monitor(BaseMonitor):
	pool: ReferenceType["PySQLXEnginePool"]

	async def run(self) -> None:
		while True:
			pool = self.pool()
			if pool._opened and pool._size > 0 and not pool._lock.locked():
				async with pool._lock:
					for _ in range(len(pool._pool)):
						conn = pool._pool.popleft()
						if conn.healthy is False:
							logger.debug(f"Connection: {conn} is unhealthy, closing.")
							await pool._del_conn(conn=conn)

						elif (pool._min_size > pool._size < pool._max_size) or pool._size > pool._max_size:
							# close the connection
							logger.debug(f"Connection: {conn} health, but pool is full, closing.")
							await pool._del_conn(conn=conn)

						elif conn.expires:
							# reuse the connection
							logger.debug(f"Connection: {conn} health, renewing.")
							conn.renew_expire_at()
							await pool._put_conn(conn=conn)

						else:
							# reuse the connection
							logger.debug(f"Connection: {conn} health, reusing.")
							await pool._put_conn(conn=conn)
			else:
				logger.debug("Pool is closed, waiting for the next check.")

			logger.debug(f"Sleeping for {pool._check_interval} seconds")
			await asleep(pool._check_interval)


class PySQLXEnginePool(BasePool):
	def __init__(
		self,
		uri: str,
		min_size: int,
		max_size: int = None,
		conn_timeout: float = 30.0,
		keep_alive: float = 60 * 15,
		check_interval: float = 5.0,
	):
		super().__init__(
			uri=uri,
			min_size=min_size,
			max_size=max_size,
			conn_timeout=conn_timeout,
			keep_alive=keep_alive,
			check_interval=check_interval,
		)
		self._lock: asyncio.Lock = asyncio.Lock()

		task_worker = aspawn(self._start_workers)
		self._workers.append(Worker(task_worker))

	def __del__(self) -> None:
		if getattr(self, "_pool", None):
			asyncio.run(self.stop())

		if getattr(self, "_workers", None):
			for worker in self._workers:
				worker.finish()

	async def _new_conn(self) -> BaseConnInfo:
		conn = PySQLXEngine(uri=self.uri)
		await conn.connect()
		conn_info = ConnInfo(conn=conn, keep_alive=self._keep_alive)
		logger.debug(f"Connection: {conn_info} created.")
		return conn_info

	async def _del_conn(self, conn: BaseConnInfo) -> None:
		logger.debug(f"Connection: {conn} closing.")
		await conn.close()
		self._size -= 1

	async def _put_conn(self, conn: BaseConnInfo) -> None:
		self._check_closed()
		if not conn.reusable:
			logger.debug(f"Connection: {conn} is not reusable, closing.")
			await self._del_conn(conn)
			logger.debug("Creating a new connection.")
			conn = await self._new_conn()

		self._pool.append(conn)
		self._size += 1

	async def _get_ready_conn(self) -> BaseConnInfo:
		logger.debug("Getting a ready connection.")
		if self._pool:
			logger.debug("Getting for a ready connection.")
			conn = self._pool.popleft()
			return conn

		if self._size < self._max_size:
			logger.debug("Creating a new connection.")
			conn = await self._new_conn()
			return conn

	async def _get_conn(self) -> BaseConnInfo:
		self._check_closed()
		deadline = monotonic() + self._conn_timeout

		while True:
			timeout = deadline - monotonic()

			if timeout < 0.0:
				raise PoolTimeout("Timeout waiting for a connection")

			conn = await self._get_ready_conn()
			if conn:
				return conn

			await asleep(0.1)

	async def _start(self) -> None:
		if self._size > 0 and self._opened:
			raise PoolAlreadyStarted("Pool is already started")

		self._opening = True
		logger.debug("Starting the pool.")
		async with self._lock:
			for _ in range(self._min_size):
				conn = await self._new_conn()
				await self._put_conn(conn)
			self._opened = True

		logger.debug(f"Pool started with {self._min_size} connections.")
		self._opening = False

	async def _start_workers(self) -> None:
		if self._opened and self._size > 0:
			return

		logger.debug("Starting the pool workers.")
		task_start = aspawn(self._start)
		task_monitor = aspawn(Monitor(pool=ref(self)).run)

		self._workers.append(Worker(task_start))
		self._workers.append(Worker(task_monitor))

	@asynccontextmanager
	async def connection(self):
		conn = await self._get_conn()
		try:
			yield conn.conn
		finally:
			await self._put_conn(conn)

	async def stop(self) -> None:
		async with self._lock:
			self._opened = False
			while self._pool:
				conn = self._pool.popleft()
				await self._del_conn(conn)
