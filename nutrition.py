# nutrition.py
from db import log_food_db, view_past_logs, fetch_past_logs_for_plot
from usda_api import USDANutritionAPI
from typing import Tuple, Dict, Any
from constant import USDA_API_KEY
from utils import parse_date, warn
import pandas as pd
from typing import Optional, Tuple

# small fallback DB (you can keep the one you had)
FOOD_DATABASE = {
    "apple": {"carbs": 14, "calories": 52, "protein": 0.3, "fat": 0.2, "fiber": 2.4},
    "banana": {"carbs": 23, "calories": 89, "protein": 1.1, "fat": 0.3, "fiber": 2.6},
    "orange": {"carbs": 12, "calories": 47, "protein": 0.9, "fat": 0.1, "fiber": 2.4},
    "chicken breast": {"carbs": 0, "calories": 165, "protein": 31, "fat": 3.6, "fiber": 0},
    "beef steak": {"carbs": 0, "calories": 271, "protein": 25, "fat": 19, "fiber": 0},
    "salmon": {"carbs": 0, "calories": 208, "protein": 20, "fat": 13, "fiber": 0},
    "white rice": {"carbs": 28, "calories": 130, "protein": 2.7, "fat": 0.3, "fiber": 0.4},
    "brown rice": {"carbs": 23, "calories": 112, "protein": 2.6, "fat": 0.9, "fiber": 1.8},
    "pasta": {"carbs": 25, "calories": 131, "protein": 5, "fat": 1.1, "fiber": 1.8},
    "whole wheat bread": {"carbs": 13, "calories": 69, "protein": 3.6, "fat": 0.9, "fiber": 1.9},
    "white bread": {"carbs": 13, "calories": 66, "protein": 2.2, "fat": 0.8, "fiber": 0.6},
    "potato": {"carbs": 17, "calories": 77, "protein": 2, "fat": 0.1, "fiber": 2.2},
    "sweet potato": {"carbs": 20, "calories": 86, "protein": 1.6, "fat": 0.1, "fiber": 3},
    "broccoli": {"carbs": 7, "calories": 34, "protein": 2.8, "fat": 0.4, "fiber": 2.6},
    "spinach": {"carbs": 3.6, "calories": 23, "protein": 2.9, "fat": 0.4, "fiber": 2.2},
    "carrot": {"carbs": 10, "calories": 41, "protein": 0.9, "fat": 0.2, "fiber": 2.8},
    "milk": {"carbs": 5, "calories": 42, "protein": 3.4, "fat": 1, "fiber": 0},
    "yogurt": {"carbs": 6, "calories": 61, "protein": 3.5, "fat": 1.5, "fiber": 0},
    "cheese": {"carbs": 1.3, "calories": 113, "protein": 7, "fat": 9, "fiber": 0},
    "egg": {"carbs": 0.6, "calories": 78, "protein": 6, "fat": 5, "fiber": 0},
    "almonds": {"carbs": 6, "calories": 164, "protein": 6, "fat": 14, "fiber": 3.5},
    "walnuts": {"carbs": 4, "calories": 185, "protein": 4.3, "fat": 18, "fiber": 1.9},
    "peanut butter": {"carbs": 6, "calories": 188, "protein": 8, "fat": 16, "fiber": 2},
    "olive oil": {"carbs": 0, "calories": 119, "protein": 0, "fat": 14, "fiber": 0},
    "avocado": {"carbs": 9, "calories": 160, "protein": 2, "fat": 15, "fiber": 7},
    "chocolate": {"carbs": 16, "calories": 152, "protein": 2.2, "fat": 9, "fiber": 1.6},
    "oatmeal": {"carbs": 12, "calories": 68, "protein": 2.4, "fat": 1.4, "fiber": 1.7},
    "quinoa": {"carbs": 21, "calories": 120, "protein": 4.4, "fat": 1.9, "fiber": 2.8},
    "lentils": {"carbs": 20, "calories": 116, "protein": 9, "fat": 0.4, "fiber": 7.9},
    "chickpeas": {"carbs": 27, "calories": 139, "protein": 7.1, "fat": 2.6, "fiber": 7.1}
}

def log_food(conn, user_id: Optional[int], food_name: str, quantity: float, date_str: str, meal_type: str, usda_api: Optional[USDANutritionAPI]= None) -> Tuple[bool, Optional[int]]:
    """
    Attempts to fetch nutrition from USDA API, falls back to local DB, or uses estimates.
    Returns tuple (was_estimated: bool, row_id: Optional[int])
    """
    # validate inputs
    date = parse_date(date_str)
    nutrition_info = None
    if user_id is None:
        return True, None  # not logged in

    nutrition_data = None
    if usda_api:
        try:
            nutrition_info = usda_api.get_nutrition_for_food(food_name, quantity)
        except Exception as e:
            warn(f"USDA API error: {e}")

    estimated = False
    if not nutrition_info:
        key = food_name.lower()
        if key in FOOD_DATABASE:
            n = FOOD_DATABASE[key]
            ratio = quantity / 100.0
            nutrition_info = {
                "calories":n["calories"] * ratio,
                "carbs":n["carbs"] * ratio,
                "protein":n["protein"] * ratio,
                "fat":n["fat"] * ratio,
                "fiber":n.get("fiber", 0) * ratio
            }
        else:
            # Use conservative estimate but mark as estimated
            ratio = quantity / 100.0
            nutrition_info = {
                "calories":100 * ratio,
                "carbs":20 * ratio,
                "protein":5 * ratio,
                "fat":3 * ratio,
                "fiber":2 * ratio
            }
            estimated = True
            warn(f"No USDA or local data for '{food_name}', inserting estimated values.")

    row_id = log_food_db(conn, user_id, food_name, quantity,
                         nutrition_info["carbs"], nutrition_info["calories"],
                         nutrition_info["protein"], nutrition_info["fat"], nutrition_info["fiber"],
                         date.isoformat(), meal_type)
    return estimated, row_id

def generate_recommendations(conn, user_id):
    logs = view_past_logs(conn, user_id)
    if not logs:
        return {"error": "No logs found"}
    df = pd.DataFrame(logs, columns=["Date", "Food", "Quantity", "Carbs", "Calories", "Protein", "Fat"])
    # compute averages and reuse your original logic
    daily_avg_calories = df['Calories'].mean()
    # ... produce recommendations similarly to your original code
    return {"summary": f"Avg calories: {daily_avg_calories:.0f}"}

# expose analytic helper
def fetch_for_plot(conn, user_id):
    return fetch_past_logs_for_plot(conn, user_id)
