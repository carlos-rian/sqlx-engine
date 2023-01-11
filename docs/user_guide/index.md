# Introduction

The PySQLXEngine is a library that allows you to connect to a database and execute queries in a simple way.

So you can use it to create, read, update and delete data in your database.

Since the beginning PySQLXEngine was created and thinking to be a totally `async` engine. 
Although Python has supported asynchronous programming since version `3.5*` using **`async/await`**.
We currently don't have good `async` libraries to handle **SQL Server** asynchronously, for example.

Despite being designed to be `async`, **PySQLXEngine** has **sync** support as well. The classes ``PySQLXEngine`` and ``PySQLXEngineSync`` are made available.

Both `async` and `sync` classes have precisely the same methods.


**Providers/Drivers**

* [`sqlite`](https://www.sqlite.org/index.html)
* [`postgresql`](https://www.postgresql.org/)
* [`mysql`](https://www.mysql.com/)
* [`sqlserver`](https://www.microsoft.com/sql-server)


**URIs**

[sqlite](https://www.sqlite.org/index.html)

``` py
uri = "sqlite:./dev.db"
```

[postgresql](https://www.postgresql.org/)

``` py
uri = "postgresql://user:pass@host:port/db?schema=sample"
```

[mysql](https://www.mysql.com/)

``` py
uri = "mysql://user:pass@host:port/db?schema=sample"
```

[sqlserver](https://www.microsoft.com/sql-server)

``` py
uri = "sqlserver://host:port;initial catalog=sample;user=sa;password=pass;"
```

---

## **Example of use async and sync**

In a way, the code's only change would be the word `async/await`.

Asynchronous programming is a broad subject, but our tutorial is intended to be objective. So, in summary, 
when you need a performance in the sense of doing concurrency "*at the same time*", use `async`. 
You can use the sync form something need to do things that don't need concurrency.

### **Create the file**

Create a file called `main.py` and add the code below.


=== "**Async**"
    ``` py linenums="1" hl_lines="3 5 7-8"
    from pysqlx_engine import PySQLXEngine

    async def main(): # need to be async, because of await
        db = PySQLXEngine(uri="sqlite:./db.db")
        await db.connect() # need to await
        print("Connected: ", db.connected)
    ```

=== "**Sync**"
    ``` py linenums="1" hl_lines="3 5 7"
    from pysqlx_engine import PySQLXEngineSync

    def main(): # don't need to be async
        db = PySQLXEngineSync(uri="sqlite:./db.db")
        db.connect() # don't need to await
        print("Connected: ", db.connected)
    ```

### **Calling the functions**

To call the coroutine functions, you need to use the ``asyncio`` library, this library is part of the standard library of Python.

So, you need to add the below lines at the end of your code!


=== "Async"
    ``` py linenums="1" hl_lines="3-4"
    ...# your code

    import asyncio # need to import 
    asyncio.run(main()) # call the function
    ```

=== "Sync"
    ``` py linenums="1" hl_lines="3-4"
    ...# your code

    # don't need to import asyncio
    main() # call the function
    ```

### **Running the code**

Running the code using the terminal

<div class="termy">

```console
$ python3 main.py

Connected: True

```
</div>