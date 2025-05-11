import sqlite3
import os,shutil
import logging

if not os.path.exists("./logs"):
    os.makedirs("./logs")

logger = logging.getLogger(__name__)
logging.basicConfig(filename='logs/db.log', level=logging.DEBUG)


# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    # ======== TABLE _ USER
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (username TEXT PRIMARY KEY, password TEXT)''')
    # Insert a sample user (for testing)
    c.execute("INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)",
              ('test', 'test'))
    # ======== TABLE _ PROJECT
    c.execute('''CREATE TABLE IF NOT EXISTS projects 
                 (
                 project_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                 project_name TEXT NOT NULL,
                 project_status TEXT DEFAULT 'Init',
                 project_model TEXT DEFAULT NULL,
                 created_at TEXT NOT NULL DEFAULT current_timestamp,
                 updated_at TEXT NOT NULL DEFAULT current_timestamp
                 )''')
    # ======== TABLE _ CLASSIFICATION
    c.execute('''CREATE TABLE IF NOT EXISTS project_classes 
                     (
                     class_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                     project_id INTEGER,
                     class_name TEXT NOT NULL,
                     project_name TEXT NOT NULL,
                     created_at TEXT NOT NULL DEFAULT current_timestamp,
                     updated_at TEXT NOT NULL DEFAULT current_timestamp
                     )''')
    conn.commit()
    conn.close()


def query_db(query, args=(), one=False):
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    logger.info("QUERY: " + query)
    cur.execute(query, args)
    if query.upper().find("SELECT")>-1:
        r = [dict((cur.description[i][0], value) \
                   for i, value in enumerate(row)) for row in cur.fetchall()]
        cur.close()
        conn.close()
        logger.info(r)
        return (r[0] if r else None) if one else r
    elif query.upper().find("INSERT") > -1:
        cur.execute("SELECT last_insert_rowid()")
        logger.info("SELECT last_insert_rowid()")
        r = [dict((cur.description[i][0], value) \
                  for i, value in enumerate(row)) for row in cur.fetchall()]
        logger.info(r[0]["last_insert_rowid()"])
        conn.commit()
        cur.close()
        conn.close()
        return r[0]["last_insert_rowid()"]
    else:
        logger.info(query)
        conn.commit()
        logger.info(query)
        cur.close()
        conn.close()
        return ()
