import mysql.connector

# ---------- CONNECTION ---------- #

def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="appuser",
        password="password123",
        database="students"
    )

def create_table():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            uid VARCHAR(50) PRIMARY KEY,
            name VARCHAR(100),
            elo_rating INT DEFAULT 1200,
            is_online BOOLEAN DEFAULT FALSE
        )
    """)

    conn.commit()
    conn.close()


# ---------- INSERT USER ---------- #

def insert_user(uid, name):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            "INSERT IGNORE INTO users (uid, name) VALUES (%s, %s)",
            (uid, name)
        )
        conn.commit()
        print(f"[MYSQL] Inserted {uid}")
    except Exception as e:
        print(f"[MYSQL ERROR] {uid} → {e}")

    conn.close()


# ---------- CHECK USER ---------- #

def user_exists(uid):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT uid FROM users WHERE uid = %s", (uid,))
    result = cursor.fetchone()

    conn.close()
    return result is not None


# ---------- SET ONLINE ---------- #

def set_user_online(uid):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE users SET is_online = TRUE WHERE uid = %s",
        (uid,)
    )

    conn.commit()
    conn.close()

def set_user_offline(uid):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE users SET is_online = FALSE WHERE uid = %s",
        (uid,)
    )

    conn.commit()
    conn.close()

def get_user_rating(uid):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT elo_rating FROM users WHERE uid = %s", (uid,))
    result = cursor.fetchone()

    conn.close()
    return result[0] if result else 1200


def update_user_rating(uid, rating):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "UPDATE users SET elo_rating = %s WHERE uid = %s",
        (rating, uid)
    )

    conn.commit()
    conn.close()