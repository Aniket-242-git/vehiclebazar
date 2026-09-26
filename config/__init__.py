"""Project package initialization.

Database driver compatibility for shared hosting (cPanel):

* Development uses SQLite (no driver needed) - see config/settings/development.py
* Production uses MySQL. The preferred driver is ``mysqlclient`` (fast, C-based).
  Some shared hosts cannot compile/install ``mysqlclient``, so we transparently
  fall back to the pure-Python ``PyMySQL`` driver (pip install PyMySQL), which
  requires no compiler and works everywhere.

This import must happen before Django loads any DB backend, which is exactly
what a project-level ``__init__.py`` guarantees.
"""

try:
    import MySQLdb  # noqa: F401  (mysqlclient installed - use it)
except ImportError:
    try:
        import pymysql

        pymysql.install_as_MySQLdb()
    except ImportError:
        # Neither driver is available. This is fine for development (SQLite);
        # production settings will raise a clear error when MySQL is used.
        pass
