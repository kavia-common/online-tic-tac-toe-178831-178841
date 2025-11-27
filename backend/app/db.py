import os
import threading
import mysql.connector
from typing import Optional, Dict, Any, List

# Simple thread-local connection manager for mysql-connector-python

_thread_local = threading.local()


def _get_env(var_name: str, default: Optional[str] = None) -> Optional[str]:
    """Helper to read environment variable with default."""
    return os.environ.get(var_name, default)


def _db_config() -> Dict[str, Any]:
    """Build DB config from environment variables."""
    return {
        "host": _get_env("DB_HOST", "localhost"),
        "port": int(_get_env("DB_PORT", "5001") or "5001"),
        "database": _get_env("DB_NAME", "myapp"),
        "user": _get_env("DB_USER", "appuser"),
        "password": _get_env("DB_PASSWORD", "dbuser123"),
        "autocommit": False,
    }


def get_connection():
    """
    Get or create a mysql-connector connection tied to current thread.
    Ensures a single connection per thread to avoid overhead.
    """
    conn = getattr(_thread_local, "conn", None)
    if conn is None or not conn.is_connected():
        cfg = _db_config()
        conn = mysql.connector.connect(**cfg)
        _thread_local.conn = conn
    return conn


def close_connection():
    """Close thread-local connection if it exists."""
    conn = getattr(_thread_local, "conn", None)
    if conn and conn.is_connected():
        try:
            conn.close()
        finally:
            _thread_local.conn = None


def execute(query: str, params: Optional[tuple] = None) -> int:
    """
    Execute a write query and commit.

    Returns affected row count.
    """
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(query, params or ())
        conn.commit()
        return cur.rowcount
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


def fetch_one(query: str, params: Optional[tuple] = None) -> Optional[tuple]:
    """Execute a select and return one row (tuple) or None."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(query, params or ())
        return cur.fetchone()
    finally:
        cur.close()


def fetch_all(query: str, params: Optional[tuple] = None) -> List[tuple]:
    """Execute a select and return all rows (list of tuples)."""
    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute(query, params or ())
        return cur.fetchall()
    finally:
        cur.close()
