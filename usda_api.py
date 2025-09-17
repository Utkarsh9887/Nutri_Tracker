# usda_api.py
import requests
from typing import Optional, Dict, Any
from constant import USDA_BASE_URL, USDA_API_KEY
from utils import warn, info

class USDANutritionAPI:
    def __init__(self, api_key: str = USDA_API_KEY):
        self.api_key = api_key
        self.base_url = USDA_BASE_URL
        self.session = requests.Session()
        self.session.headers.update({"Content-Type": "application/json"})
        self.cache = {}

    def search_foods(self, query: str, page_size: int = 10) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/foods/search"
        params = {
            "api_key": self.api_key,
            "query": query,
            "pageSize": page_size,
            "dataType": ["Survey (FNDDS)", "Branded", "Foundation", "SR Legacy"]
        }
        try:
            r = self.session.get(url, params=params, timeout=10)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            warn(f"USDA search error: {e}")
            return None

    def get_food_details(self, fdc_id: int) -> Optional[Dict[str, Any]]:
        url = f"{self.base_url}/food/{fdc_id}"
        params = {"api_key": self.api_key}
        try:
            r = self.session.get(url, params=params, timeout=10)
            r.raise_for_status()
            return r.json()
        except requests.RequestException as e:
            warn(f"USDA details error: {e}")
            return None

    def _extract_nutrient_id(self, nutrient_entry: dict):
        """
        USDA responses vary: sometimes nutrient info appears nested under 'nutrient' with 'number' or 'id',
        sometimes there is 'nutrientId' at top level. We'll check several fields.
        """
        # common patterns
        nutrient = nutrient_entry.get('nutrient') or {}
        candidates = [
            nutrient.get('number'),
            nutrient.get('id'),
            nutrient_entry.get('nutrientId'),
            nutrient_entry.get('number'),
            nutrient_entry.get('nutrient_number')
        ]
        for c in candidates:
            if c is None:
                continue
            try:
                return int(c)
            except Exception:
                try:
                    return int(str(c))
                except:
                    continue
        return None

    def _extract_amount(self, nutrient_entry: dict):
        # field names used sometimes: 'amount', 'value', 'nutrientAmount', 'nutrientValue'
        for key in ('amount', 'value', 'nutrient_amount', 'nutrientValue'):
            if key in nutrient_entry and nutrient_entry[key] is not None:
                return float(nutrient_entry[key])
        # maybe under nested 'nutrient' ?
        nutrient = nutrient_entry.get('nutrient') or {}
        for key in ('amount', 'value'):
            if key in nutrient and nutrient[key] is not None:
                return float(nutrient[key])
        return 0.0

    def extract_nutrition_info(self, food_data: dict) -> dict:
        """
        Return a dict: calories, carbs, protein, fat, fiber. Values per 100g (or per serving depending on USDA record).
        We attempt to find the nutrient numbers typically used in FDC:
          - Energy: nutrient number 208 (kcal) or legacy 1008 (some older scripts used different codes)
          - Carbohydrate: 205 (g) or 1005
          - Protein: 203 (g) or 1003
          - Total lipid (fat): 204 (g) or 1004
          - Fiber: 291 (g) or 1079
        """
        # mapping covers both legacy and FDC nutrient numbers
        nutrient_map = {
            208: "calories", 1008: "calories",
            205: "carbs", 1005: "carbs",
            203: "protein", 1003: "protein",
            204: "fat", 1004: "fat",
            291: "fiber", 1079: "fiber"
        }
        nutrition_info = {"calories": 0.0, "carbs": 0.0, "protein": 0.0, "fat": 0.0, "fiber": 0.0}
        if not food_data:
            return nutrition_info
        nutrients = food_data.get('foodNutrients') or food_data.get('foodNutrients', [])
        for n in nutrients:
            nid = self._extract_nutrient_id(n)
            if nid is None:
                continue
            amt = self._extract_amount(n)
            if nid in nutrient_map:
                nutrition_info[nutrient_map[nid]] = amt
        return nutrition_info

    def get_nutrition_for_food(self, food_name: str, quantity: float = 100.0):
        cache_key = f"{food_name.lower()}_{quantity}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        # search
        search = self.search_foods(food_name)
        if not search or 'foods' not in search or not search['foods']:
            return None
        first = search['foods'][0]
        fdc_id = first.get('fdcId') or first.get('fdc_id') or None
        if not fdc_id:
            return None
        details = self.get_food_details(fdc_id)
        if not details:
            return None
        nutrition = self.extract_nutrition_info(details)
        ratio = quantity / 100.0
        adjusted = {k: v * ratio for k, v in nutrition.items()}
        self.cache[cache_key] = adjusted
        return adjusted
