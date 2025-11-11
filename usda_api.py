# usda_api.py — Local nutrition database version
import sqlite3
from typing import Optional, Dict

class USDANutritionAPI:
    """
    Local nutrition database reader.
    Returns nutrient values for the given food and quantity (in grams).
    """

    def __init__(self, db_path: str = "database/nutrition_local.db"):
        self.db_path = db_path

    def get_nutrition_for_food(self, food_name: str, quantity: float = 100.0) -> Optional[Dict[str, float]]:
        try:
            conn = sqlite3.connect(self.db_path)
            cur = conn.cursor()

            # Look for partial match in food names
            cur.execute(
                "SELECT calories, carbs, protein, fat, fiber FROM foods WHERE name LIKE ? LIMIT 1",
                (f"%{food_name.lower()}%",)
            )
            row = cur.fetchone()
            conn.close()

            if not row:
                print(f"⚠️ '{food_name}' not found in local DB.")
                return None

            keys = ["calories", "carbs", "protein", "fat", "fiber"]
            ratio = quantity / 100.0
            return {k: round(v * ratio, 2) for k, v in dict(zip(keys, row)).items()}

        except Exception as e:
            print(f"Database error: {e}")
            return None
# Example usage:
