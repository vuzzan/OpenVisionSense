import sqlite3
import os,shutil
import logging

if not os.path.exists("./logs"):
    os.makedirs("./logs")
# Configure logger for module1
logger_db = logging.getLogger(__name__)
logger_db.setLevel(logging.DEBUG)
fh1 = logging.FileHandler('logs/db.log')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
fh1.setFormatter(formatter)
logger_db.addHandler(fh1)



# Initialize SQLite database


def init_db():
    print("Init db")
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
    # ======== TABLE _ CLASSIFICATION
    c.execute('''CREATE TABLE IF NOT EXISTS queue_jobs 
                         (
                         job_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                         project_id INTEGER,
                         project_name TEXT DEFAULT NULL,
                         source_file_path TEXT NOT NULL,
                         result_file_path TEXT DEFAULT NULL,
                         job_result INTEGER DEFAULT NULL,
                         job_class TEXT DEFAULT NULL,
                         job_status TEXT DEFAULT 'Wait Run',
                         created_at TEXT NOT NULL DEFAULT current_timestamp,
                         updated_at TEXT DEFAULT NULL
                         )''')
    conn.commit()
    conn.close()


def query_db(query, args=(), one=False):
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(query, args)
    if query.upper().find("SELECT")>-1:
        logger_db.info("QUERY: " + query)
        r = [dict((cur.description[i][0], value) \
                   for i, value in enumerate(row)) for row in cur.fetchall()]
        cur.close()
        conn.close()
        logger_db.info(r)
        return (r[0] if r else None) if one else r
    elif query.upper().find("INSERT") > -1:
        cur.execute("SELECT last_insert_rowid()")
        logger_db.info("SELECT last_insert_rowid()")
        r = [dict((cur.description[i][0], value) \
                  for i, value in enumerate(row)) for row in cur.fetchall()]
        logger_db.info(r[0]["last_insert_rowid()"])
        conn.commit()
        cur.close()
        conn.close()
        return r[0]["last_insert_rowid()"]
    else:
        logger_db.info("QUERY 2: " + query)
        conn.commit()
        cur.close()
        conn.close()
        return ()
