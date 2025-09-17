# constants.py
COLORS = {
    'primary': '#4CAF50',       # Green
    'secondary': '#2196F3',     # Blue
    'accent': '#FF9800',        # Orange
    'background': "#0A0A0A",    # Light gray
    'text': "#FEFAFA",          # Dark gray
    'success': '#4CAF50',
    'warning': '#FFC107',
    'error': '#F44336'
}

# USDA default config
USDA_API_KEY = "rqrDylfBJxVKWXnXgb7BGhShKaRsE2sqiMeME78b"
USDA_BASE_URL = "https://api.nal.usda.gov/fdc/v1"

# Password hashing config
PWD_HASH_ITERATIONS = 150_000
PWD_HASH_NAME = "sha256"
PWD_SALT_BYTES = 16

# Database file
DB_FILE = "nutrition_tracker.db"
