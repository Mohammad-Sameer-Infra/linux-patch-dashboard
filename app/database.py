import sqlite3


DATABASE = "telemetry.db"


def init_db():

    conn = sqlite3.connect(DATABASE)

    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS telemetry (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            hostname TEXT,
            ip TEXT,
            os TEXT,
            uptime TEXT,
            updates INTEGER,
            status TEXT,
            last_check TEXT
        )
    """)

    conn.commit()
    conn.close()


def insert_telemetry(data):

    conn = sqlite3.connect(DATABASE)

    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO telemetry (
            hostname,
            ip,
            os,
            uptime,
            updates,
            status,
            last_check
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        data["hostname"],
        data["ip"],
        data["os"],
        data["uptime"],
        data["updates"],
        data["status"],
        data["last_check"]
    ))

    conn.commit()
    conn.close()
