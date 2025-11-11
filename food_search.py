# food_search.py
import sqlite3
from rapidfuzz import fuzz
from db import connect_to_db

def search_foods(keyword: str, limit: int = 8):
    """
    Search the local nutrition database for foods similar to the keyword.
    Returns a list of matching food names.
    """
    keyword = keyword.strip().lower()
    if not keyword:
        return []

    conn = sqlite3.connect("nutrition_local.db")
    cur = conn.cursor()
    cur.execute("SELECT food_name FROM food_logs")
    all_foods = [row[0] for row in cur.fetchall()]
    conn.close()

    # Fuzzy matching: allow slight typos
    scored = [(food_name, fuzz.partial_ratio(keyword, food_name.lower())) for food_name in all_foods]
    scored.sort(key=lambda x: x[1], reverse=True)
    return [food_name for food_name, score in scored[:limit] if score > 50]
