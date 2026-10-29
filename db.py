import os
import sqlite3
import re
from config import Config

# Global variable indicating active database engine
ACTIVE_DB_TYPE = 'sqlite'
_mysql_available = False

try:
    import pymysql
    import pymysql.cursors
    _mysql_available = True
except ImportError:
    _mysql_available = False


import socket

def check_mysql_connection():
    """Test if MySQL server is reachable with configured credentials."""
    if not _mysql_available:
        return False
    # Quick socket probe on port to avoid pymysql connection hangs
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.5)
        host = '127.0.0.1' if Config.MYSQL_HOST in ('localhost', '127.0.0.1') else Config.MYSQL_HOST
        result = sock.connect_ex((host, Config.MYSQL_PORT))
        sock.close()
        if result != 0:
            return False
    except Exception:
        return False

    try:
        conn = pymysql.connect(
            host=Config.MYSQL_HOST,
            port=Config.MYSQL_PORT,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            connect_timeout=1
        )
        conn.close()
        return True
    except Exception:
        return False


def get_mysql_connection(use_database=True):
    """Create and return a PyMySQL connection."""
    kwargs = {
        'host': Config.MYSQL_HOST,
        'port': Config.MYSQL_PORT,
        'user': Config.MYSQL_USER,
        'password': Config.MYSQL_PASSWORD,
        'charset': 'utf8mb4',
        'cursorclass': pymysql.cursors.DictCursor,
        'autocommit': False
    }
    if use_database:
        kwargs['database'] = Config.MYSQL_DB
    return pymysql.connect(**kwargs)


def get_sqlite_connection():
    """Create and return a SQLite connection with dict-like row factory."""
    conn = sqlite3.connect(Config.SQLITE_DB)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def determine_active_db():
    """Determine whether to use MySQL or SQLite based on configuration and availability."""
    global ACTIVE_DB_TYPE
    if Config.DB_TYPE == 'mysql':
        ACTIVE_DB_TYPE = 'mysql'
    elif Config.DB_TYPE == 'sqlite':
        ACTIVE_DB_TYPE = 'sqlite'
    else:  # 'auto'
        if check_mysql_connection():
            ACTIVE_DB_TYPE = 'mysql'
        else:
            ACTIVE_DB_TYPE = 'sqlite'
    return ACTIVE_DB_TYPE


def get_connection():
    """Obtain a database connection for the active engine."""
    db_type = determine_active_db()
    if db_type == 'mysql':
        try:
            return get_mysql_connection(), 'mysql'
        except Exception as e:
            # Fallback to SQLite if MySQL failed during active operation
            print(f"[DB WARNING] Failed to connect to MySQL ({e}). Falling back to SQLite.")
            return get_sqlite_connection(), 'sqlite'
    else:
        return get_sqlite_connection(), 'sqlite'


def query_db(query, args=(), one=False, commit=False):
    """
    Execute a parameterized SQL query safely.
    Handles parameter syntax translation (%s for MySQL vs ? for SQLite).
    """
    conn, engine = get_connection()
    try:
        cursor = conn.cursor()
        
        # Translate placeholder syntax for SQLite
        executable_query = query
        if engine == 'sqlite':
            # Replace %s with ? safely
            executable_query = re.sub(r'%s', '?', query)
        else:
            # Ensure MySQL uses %s
            executable_query = re.sub(r'\?', '%s', query)
        
        cursor.execute(executable_query, args)
        
        if commit:
            conn.commit()
            last_id = cursor.lastrowid
            row_count = cursor.rowcount
            cursor.close()
            conn.close()
            return {'last_id': last_id, 'row_count': row_count}
        
        rv = cursor.fetchall()
        cursor.close()
        conn.close()
        
        # Format results consistently as list of dicts
        if engine == 'sqlite':
            results = [dict(row) for row in rv]
        else:
            results = list(rv)
            
        return (results[0] if results else None) if one else results
    except Exception as e:
        if commit and conn:
            try:
                conn.rollback()
            except Exception:
                pass
        if conn:
            conn.close()
        raise e


def init_sqlite_db():
    """Initialize SQLite database with schema translated from schema.sql."""
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found at {schema_path}")
        
    with open(schema_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    # Adapt MySQL schema syntax to SQLite
    # 1. Remove CREATE DATABASE / USE statements
    sql_content = re.sub(r'CREATE DATABASE [^;]+;', '', sql_content, flags=re.IGNORECASE)
    sql_content = re.sub(r'USE [^;]+;', '', sql_content, flags=re.IGNORECASE)
    
    # 2. Adjust AUTO_INCREMENT to AUTOINCREMENT and INT PRIMARY KEY AUTO_INCREMENT
    sql_content = re.sub(r'INT AUTO_INCREMENT PRIMARY KEY', 'INTEGER PRIMARY KEY AUTOINCREMENT', sql_content, flags=re.IGNORECASE)
    sql_content = re.sub(r'AUTO_INCREMENT', '', sql_content, flags=re.IGNORECASE)
    
    # 3. Strip MySQL table options
    sql_content = re.sub(r'ENGINE=InnoDB[^;]*', '', sql_content, flags=re.IGNORECASE)
    sql_content = re.sub(r'DEFAULT CHARSET=[a-zA-Z0-9]+', '', sql_content, flags=re.IGNORECASE)
    
    conn = get_sqlite_connection()
    cursor = conn.cursor()
    
    # Execute statements
    statements = sql_content.split(';')
    for statement in statements:
        stmt = statement.strip()
        if stmt:
            try:
                cursor.execute(stmt)
            except Exception as e:
                # Ignore table drop errors on first run
                if "no such table" not in str(e).lower():
                    print(f"[SQLITE INIT NOTE] {e} on: {stmt[:60]}...")
    conn.commit()
    conn.close()
    print(f"[DB INFO] SQLite database successfully initialized at: {Config.SQLITE_DB}")


def init_mysql_db():
    """Initialize MySQL database using schema.sql."""
    schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found at {schema_path}")

    # Connect to MySQL server without selecting database first
    conn = pymysql.connect(
        host=Config.MYSQL_HOST,
        port=Config.MYSQL_PORT,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        charset='utf8mb4',
        autocommit=True
    )
    cursor = conn.cursor()
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{Config.MYSQL_DB}`;")
    cursor.execute(f"USE `{Config.MYSQL_DB}`;")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        sql_content = f.read()

    # Split and execute
    statements = sql_content.split(';')
    for statement in statements:
        stmt = statement.strip()
        if stmt:
            try:
                cursor.execute(stmt)
            except Exception as e:
                print(f"[MYSQL INIT NOTE] {e} on: {stmt[:60]}...")
    conn.close()
    print(f"[DB INFO] MySQL database `{Config.MYSQL_DB}` successfully initialized.")


def init_db(force=False):
    """Initialize the appropriate database based on configuration."""
    active_type = determine_active_db()
    if active_type == 'mysql':
        try:
            init_mysql_db()
            return 'mysql'
        except Exception as e:
            print(f"[DB ERROR] MySQL initialization failed: {e}. Falling back to SQLite.")
            init_sqlite_db()
            return 'sqlite'
    else:
        init_sqlite_db()
        return 'sqlite'
