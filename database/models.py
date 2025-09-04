# database/models.py
import sqlite3
import json
import os
from collections import defaultdict
from database.db import get_connection

_browse_index = defaultdict(int)
_browse_cache = defaultdict(list)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            name TEXT,
            age INTEGER,
            gender TEXT,
            preference TEXT,
            city TEXT,
            phone TEXT,
            bio TEXT,
            photos TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS likes (
            liker_id INTEGER,
            liked_id INTEGER,
            PRIMARY KEY (liker_id, liked_id)
        )
    ''')

    conn.commit()
    conn.close()

def save_user(user_id: int, data: dict):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
        INSERT OR REPLACE INTO users (
            user_id, name, age, gender, preference, city, phone, bio, photos, username
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        user_id,
        data.get("name"),
        data.get("age"),
        data.get("gender"),
        data.get("preference"),
        data.get("city"),
        data.get("phone"),
        data.get("bio"),
        json.dumps(data.get("photos", []), ensure_ascii=False),
        data.get("username"),
    ))

    conn.commit()
    conn.close()

def get_user(user_id: int) -> dict | None:
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()

    if not row:
        return None

    # колонки в тій же послідовності, що й в таблиці
    columns = [
        "user_id", "name", "age", "gender", "preference",
        "city", "phone", "bio", "photos", "username"
    ]

    user = dict(zip(columns, row))

    # photos зберігаються як json → треба розпарсити
    if user.get("photos"):
        try:
            user["photos"] = json.loads(user["photos"])
        except Exception:
            user["photos"] = []
    else:
        user["photos"] = []

    return user

def preload_profiles(user_id: int):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT gender, preference FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return []

    my_gender, my_preference = row

    if my_preference == "girls":
        target_gender = "girl"
    elif my_preference == "boys":
        target_gender = "boy"
    else:
        target_gender = None

    if target_gender:
        cursor.execute("SELECT * FROM users WHERE gender = ? AND user_id != ?", (target_gender, user_id))
    else:
        cursor.execute("SELECT * FROM users WHERE user_id != ?", (user_id,))

    columns = [col[0] for col in cursor.description]
    profiles = []
    for row in cursor.fetchall():
        profile = dict(zip(columns, row))
        if profile.get("photos"):
            try:
                profile["photos"] = json.loads(profile["photos"])
            except:
                profile["photos"] = []
        else:
            profile["photos"] = []
        profiles.append(profile)

    conn.close()
    _browse_cache[user_id] = profiles
    _browse_index[user_id] = 0
    return profiles

def get_next_profile(user_id: int):
    profiles = _browse_cache.get(user_id)
    if not profiles:
        return None
    idx = _browse_index.get(user_id, 0)
    if idx >= len(profiles):
        return None
    profile = profiles[idx]
    _browse_index[user_id] += 1
    return profile

def record_like(liker_id: int, liked_id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR IGNORE INTO likes (liker_id, liked_id)
        VALUES (?, ?)
    ''', (liker_id, liked_id))
    conn.commit()
    conn.close()

def is_registered(user_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def check_mutual_like(user1: int, user2: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT 1 FROM likes
        WHERE liker_id = ? AND liked_id = ?
    ''', (user2, user1))
    result = cursor.fetchone()
    conn.close()
    return result is not None
