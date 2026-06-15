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
            kernel_updates INTEGER,
            security_updates INTEGER,
            critical_packages INTEGER,
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
            kernel_updates,
            security_updates,
            critical_packages,
            status,
            last_check
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data["hostname"],
        data["ip"],
        data["os"],
        data["uptime"],
        data["updates"],
        data["kernel_updates"],
        data["security_updates"],
        data["critical_packages"],
        data["status"],
        data["last_check"]
    ))

    conn.commit()
    conn.close()

def get_telemetry_history():

    conn = sqlite3.connect(DATABASE)

    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            hostname,
            ip,
            os,
            uptime,
            updates,
            kernel_updates,
            security_updates,
            critical_packages,
            status,
            last_check
        FROM telemetry
        ORDER BY id DESC
    """)

    rows = cursor.fetchall()

    conn.close()

    return rows
