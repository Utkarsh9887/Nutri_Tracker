# db.py
import sqlite3
from sqlite3 import Connection
from typing import Optional, Tuple, List
from constant import DB_FILE
from utils import generate_salt, hash_password, verify_password

def connect_to_db(db_file: str = DB_FILE) -> Connection:
    conn = sqlite3.connect(db_file, check_same_thread=False)
    cursor = conn.cursor()
    

    # Create users table (new schema) if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        age INTEGER,
        gender TEXT,
        height REAL,
        weight REAL,
        goal_weight REAL,
        activity_level TEXT,
        weight_goal TEXT,
        is_admin INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # Create food_logs table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS food_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        food_name TEXT NOT NULL,
        quantity REAL NOT NULL,
        carbs REAL,
        calories REAL,
        protein REAL,
        fat REAL,
        fiber REAL,
        date DATE NOT NULL,
        meal_type TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS water_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date TEXT,
            glasses INTEGER DEFAULT 0,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )""")

    conn.commit()
    return conn

# User functions
def create_user(conn: Connection, username: str, password: str,is_admin: bool = False) -> bool:
    cursor = conn.cursor()
    salt = generate_salt()
    pwd_hash_hex, salt_hex = hash_password(password, salt)
    try:
        cursor.execute(
            "INSERT INTO users (username, password_hash, salt,is_admin) VALUES (?, ?, ?, ?)",
            (username, pwd_hash_hex, salt_hex, 1 if is_admin else 0)
        )
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        raise Exception("Username already exists")
    except Exception as e:
        raise

def login_user(conn: Connection, username: str, password: str) -> Optional[Tuple[int, str, bool]]:
    cursor = conn.cursor()
    cursor.execute("SELECT id, password_hash, salt , is_admin FROM users WHERE username = ?", (username,))
    row = cursor.fetchone()
    if not row:
        return None
    user_id, stored_hash, stored_salt,is_admin = row
    if verify_password(password, stored_hash, stored_salt):
        return (user_id, username, bool(is_admin))
    return None
def update_user_profile(conn: Connection, user_id: int, age, gender, height, weight, goal_weight, activity_level, weight_goal):
    cursor = conn.cursor()
    cursor.execute(
        """UPDATE users SET age=?, gender=?, height=?, weight=?, goal_weight=?, activity_level=?, weight_goal=? WHERE id=?""",
        (age, gender, height, weight, goal_weight, activity_level, weight_goal, user_id)
    )
    conn.commit()
    return True

def get_user_data_for_ml(conn: Connection, user_id: int):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT age, gender, height, weight, goal_weight, activity_level, weight_goal FROM users WHERE id = ?",
        (user_id,)
    )
    row = cursor.fetchone()
    if row:
        return {
            'age': row[0],
            'gender': row[1],
            'height': row[2],
            'weight': row[3],
            'goal_weight': row[4],
            'activity_level': row[5],
            'weight_goal': row[6]
        }
    return None

# Food logs
def log_food_db(conn: Connection, user_id: int, food_name: str, quantity: float, carbs, calories, protein, fat, fiber, date, meal_type):
    cursor = conn.cursor()
    print("DEBUG insert values:", carbs, calories, protein, fat, fiber)
    cursor.execute(
        "INSERT INTO food_logs (user_id, food_name, quantity, carbs, calories, protein, fat, fiber, date, meal_type) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (user_id, food_name, quantity, carbs, calories, protein, fat, fiber, date, meal_type)
    )
    conn.commit()
    return cursor.lastrowid

def view_past_logs(conn: Connection, user_id: int):
    cursor = conn.cursor()
    cursor.execute(
        "SELECT date, food_name, quantity, carbs, calories, protein, fat FROM food_logs WHERE user_id = ? ORDER BY date DESC, id DESC",
        (user_id,)
    )
    return cursor.fetchall()

# db.py
import pandas as pd

def fetch_past_logs_for_plot(conn, user_id):
    """Fetch data for visualization: returns DataFrame with Date, Carbs, Calories, Protein, Fat"""
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT date,
                   COALESCE(SUM(carbs), 0)   AS Carbs,
                   COALESCE(SUM(calories), 0) AS Calories,
                   COALESCE(SUM(protein), 0) AS Protein,
                   COALESCE(SUM(fat), 0) AS Fat
            FROM food_logs
            WHERE user_id = ?
            GROUP BY date
            ORDER BY date
            """,
            (user_id,)
        )

        rows = cursor.fetchall()
        if not rows:
            return pd.DataFrame(columns=["Date", "Carbs", "Calories", "Protein", "Fat"])

        df = pd.DataFrame(rows, columns=["Date", "Carbs", "Calories", "Protein", "Fat"])
        # Ensure correct dtypes
        df['Date'] = pd.to_datetime(df['Date']).dt.date
        df[['Carbs', 'Calories', 'Protein', 'Fat']] = df[['Carbs', 'Calories', 'Protein', 'Fat']].apply(pd.to_numeric, errors='coerce').fillna(0)
        return df
    except Exception as e:
        print(f"Error fetching data for plots: {e}")
        return pd.DataFrame(columns=["Date", "Carbs", "Calories", "Protein", "Fat"])

def get_all_users(conn):
    """
    Fetch all users from the database.
    """
    cur = conn.cursor()
    cur.execute("""
        SELECT id, username, age, gender, height, weight, goal_weight, activity_level, weight_goal, is_admin
        FROM users
    """)
    return cur.fetchall()
def set_admin_status(conn, user_id: int, is_admin: bool):
    cur = conn.cursor()
    cur.execute("UPDATE users SET is_admin=? WHERE id=?", (1 if is_admin else 0, user_id))
    conn.commit()


def reset_user_password(conn, user_id: int, new_password: str):
    salt = generate_salt()
    password_hash, salt_hex = hash_password(new_password, salt)
    cur = conn.cursor()
    cur.execute("UPDATE users SET password_hash=?, salt=? WHERE id=?", (password_hash, salt_hex, user_id))
    conn.commit()


def delete_user(conn, user_id: int):
    cur = conn.cursor()
    # delete logs first (foreign key constraint)
    cur.execute("DELETE FROM food_logs WHERE user_id=?", (user_id,))
    cur.execute("DELETE FROM users WHERE id=?", (user_id,))
    conn.commit()

def predict_calorie_goal(conn, user_id: int) -> int:
    """
    Estimate daily calorie needs using the Mifflin-St Jeor Equation.
    Adjusts based on activity level and weight goal.
    """
    cur = conn.cursor()
    cur.execute("""
        SELECT age, gender, height, weight, goal_weight, activity_level, weight_goal
        FROM users WHERE id=?
    """, (user_id,))
    row = cur.fetchone()

    if not row:
        return 2000  # fallback default

    age, gender, height, weight, goal_weight, activity_level, weight_goal = row

    # --- 1. Basal Metabolic Rate (BMR) ---
    if gender and gender.lower() == "male":
        bmr = 10 * weight + 6.25 * height - 5 * age + 5
    else:
        bmr = 10 * weight + 6.25 * height - 5 * age - 161

    # --- 2. Activity Factor ---
    activity_factors = {
        "sedentary": 1.2,
        "light": 1.375,
        "moderate": 1.55,
        "active": 1.725,
        "very active": 1.9
    }
    factor = activity_factors.get(str(activity_level).lower(), 1.2)
    calories = bmr * factor

    # --- 3. Adjust for Weight Goal ---
    if weight_goal and str(weight_goal).lower() == "lose":
        calories -= 500  # deficit
    elif weight_goal and str(weight_goal).lower() == "gain":
        calories += 500  # surplus

    return int(calories)
def get_user_streak(conn, user_id: int) -> int:
    """Calculate consecutive logging streak for a user."""
    cur = conn.cursor()
    cur.execute("""
        SELECT DISTINCT date
        FROM food_logs
        WHERE user_id = ?
        ORDER BY date DESC
    """, (user_id,))
    dates = [row[0] for row in cur.fetchall()]
    if not dates:
        return 0

    streak = 1
    prev = pd.to_datetime(dates[0]).date()
    for d in dates[1:]:
        curr = pd.to_datetime(d).date()
        if (prev - curr).days == 1:
            streak += 1
            prev = curr
        else:
            break
    return streak
def get_today_water(conn, user_id: int) -> int:
    cur = conn.cursor()
    cur.execute("SELECT glasses FROM water_logs WHERE user_id=? AND date=date('now')", (user_id,))
    row = cur.fetchone()
    return row[0] if row else 0


def update_water(conn, user_id: int, glasses: int):
    cur = conn.cursor()
    cur.execute("SELECT id FROM water_logs WHERE user_id=? AND date=date('now')", (user_id,))
    row = cur.fetchone()
    if row:
        cur.execute("UPDATE water_logs SET glasses=? WHERE id=?", (glasses, row[0]))
    else:
        cur.execute("INSERT INTO water_logs (user_id, date, glasses) VALUES (?, date('now'), ?)", (user_id, glasses))
    conn.commit()
def add_food(name, calories, carbs, protein, fat, fiber):
    conn = sqlite3.connect("nutrition_local.db")
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO foods (name, calories, carbs, protein, fat, fiber) VALUES (?, ?, ?, ?, ?, ?)",
        (name.lower(), calories, carbs, protein, fat, fiber)
    )
    conn.commit()
    conn.close()
    print(f"✅ Added '{name}' to local database.")