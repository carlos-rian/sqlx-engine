import json
from os import getenv

from pygments import highlight
from pygments.formatters import TerminalFormatter
from pygments.lexers import JsonLexer, PythonLexer


def _colorizer_py_code_message(message: str):
    return highlight(message, PythonLexer(), TerminalFormatter())


def _colorizer_json_message(dumps: str):
    return highlight(dumps, JsonLexer(), TerminalFormatter())


def fe_py(message: str) -> str:
    """create a error message format for python code"""
    if getenv("PYSQLX_ERROR_COLORIZE", "0") == "1":
        return _colorizer_py_code_message(message)
    return message


def fe_json(data: dict) -> str:
    """create a error message format for python code"""
    dumps = json.dumps(data, indent=2)
    if getenv("PYSQLX_ENGINE_COLORIZE", "0") == "1":
        return "\n" + _colorizer_json_message(dumps)
    return "\n" + dumps


def isolation_error_message():
    return f"""
    the isolation_level must be a valid value.

    possible values:
        >> ReadUncommitted
        >> ReadCommitted
        >> RepeatableRead
        >> Snapshot
        >> Serializable

    example of use:
        >> {fe_py('isolation_level = "ReadUncommitted"')}
    """


def not_connected_error_message():
    return f"""
        not connected to the database.

        before using the methods, you must connect to the database.
            
        example of use:
            Async:
                {fe_py('''uri = "postgresql://user:pass@host:port/db?schema=sample"
                db = PySQLXEngine(uri=uri)
                await db.connect()
                ''')}
            Sync:
                {fe_py('''uri = "postgresql://user:pass@host:port/db?schema=sample"
                db = PySQLXEngineSync(uri=uri)
                db.connect()
                ''')}
    """


def model_parameter_error_message():
    return f"""
        model parameter must be a subclass of BaseRow

        try importing the BaseRow class from the pysqlx_engine package.

        example of use:
            {fe_py('''
            
            # import the BaseRow class
            from pysqlx_engine import BaseRow

            class MyModel(BaseRow): # <- subclass of BaseRow
                id: int
                name: str
    
            # async
            db = PySQLXEngine(uri="postgresql://user:pass@host:port/db?schema=sample")
            await db.connect()
            await db.query(query="SELECT 1 AS id, 'Rian' AS name", model=MyModel) # <- using how model parameter

            # sync
            db = PySQLXEngineSync(uri="postgresql://user:pass@host:port/db?schema=sample")
            db.connect()
            db.query(query="SELECT 1 AS id, 'Rian' AS name", model=MyModel) # <- using how model parameter
            ''')
            }
        """
