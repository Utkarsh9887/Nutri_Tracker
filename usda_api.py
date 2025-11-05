# usda_api.py — Combined free nutrition API (Open Food Facts + Nutritionix)
import requests
from typing import Optional, Dict, Any
from utils import warn

# --------------------------------------------------------------------
#  PRIMARY:  Open Food Facts  (no key, open-source)
# --------------------------------------------------------------------
class OpenFoodFactsAPI:
    BASE_URL = "https://world.openfoodfacts.org/cgi/search.pl"

    def get_nutrition_for_food(self, food_name: str, quantity: float = 100.0) -> Optional[Dict[str, Any]]:
        try:
            params = {
                "search_terms": food_name,
                "search_simple": 1,
                "action": "process",
                "json": 1,
                "page_size": 1,
            }
            r = requests.get(self.BASE_URL, params=params, timeout=10)
            r.raise_for_status()
            data = r.json()
            if not data.get("products"):
                return None

            nutriments = data["products"][0].get("nutriments", {})
            per_100g = {
                "calories": nutriments.get(f"energy-kcal_100g", 0.0),
                "carbs": nutriments.get(f"carbohydrates_100g", 0.0),
                "protein": nutriments.get(f"proteins_100g", 0.0),
                "fat": nutriments.get(f"fat_100g", 0.0),
                "fiber": nutriments.get(f"fiber_100g", 0.0),
            }
            print(per_100g)
            # scale to the exact quantity
            ratio = quantity / 100.0
            scaled = {k: round(v * ratio, 2) for k, v in per_100g.items()}

            return scaled
        except requests.RequestException as e:
            warn(f"Open Food Facts error: {e}")
            return None


# --------------------------------------------------------------------
#  BACKUP:  Nutritionix  (free personal API key)
# --------------------------------------------------------------------
class NutritionixAPI:
    BASE_URL = "https://trackapi.nutritionix.com/v2/natural/nutrients"

    def __init__(self, app_id: str = "", app_key: str = ""):
        self.app_id = "7bcaef13"
        self.app_key = "384923ff68e4e7d5373aa86623c4ac2a"

    def get_nutrition_for_food(self, food_name: str, quantity: float = 100.0) -> Optional[Dict[str, Any]]:
        try:
            headers = {
                "x-app-id": self.app_id,
                "x-app-key": self.app_key,
                "Content-Type": "application/json",
            }
            data = {"query": f"100g {food_name}"}
            r = requests.post(self.BASE_URL, json=data, headers=headers, timeout=10)
            r.raise_for_status()
            result = r.json()
            if not result.get("foods"):
                return None

            item = result["foods"][0]
            return {
                "calories": item.get("nf_calories", 0.0),
                "carbs": item.get("nf_total_carbohydrate", 0.0),
                "protein": item.get("nf_protein", 0.0),
                "fat": item.get("nf_total_fat", 0.0),
                "fiber": item.get("nf_dietary_fiber", 0.0),
            }
        except requests.RequestException as e:
            warn(f"Nutritionix error: {e}")
            return None


# --------------------------------------------------------------------
#  UNIFIED WRAPPER (keeps same class name used by your project)
# --------------------------------------------------------------------
class USDANutritionAPI:
    """
    Unified nutrition API that first tries Open Food Facts (no key),
    then falls back to Nutritionix if necessary.
    Returns nutrients per 100 g to match nutrition.py scaling.
    """

    def __init__(self, app_id: str = "", app_key: str = ""):
        self.primary = OpenFoodFactsAPI()
        self.backup = NutritionixAPI(app_id, app_key)

    def get_nutrition_for_food(self, food_name: str, quantity: float = 100.0) -> Optional[Dict[str, Any]]:
        # 1️⃣ Try Open Food Facts
        info = self.primary.get_nutrition_for_food(food_name, quantity)
        if info and info["calories"] > 0:
            return info

        # 2️⃣ Fallback → Nutritionix
        warn(f"Open Food Facts data missing for '{food_name}', using Nutritionix.")
        info = self.backup.get_nutrition_for_food(food_name, quantity)
        return info

# Example usage:
api = USDANutritionAPI()
print(api.get_nutrition_for_food("apple",200))