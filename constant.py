# constants.py
COLORS = {
    'primary': '#4CAF50',       # Green
    'secondary': '#2196F3',     # Blue
    'accent': '#FF9800',        # Orange
    'background': "#080808",    # Light gray
    'text': "#FEFAFA",          # Dark gray
    'success': '#4CAF50',
    'warning': '#FFC107',
    'error': '#F44336'
}

# Password hashing config
PWD_HASH_ITERATIONS = 150_000
PWD_HASH_NAME = "sha256"
PWD_SALT_BYTES = 16

# Database file
DB_FILE = "database/nutrition_tracker.db"
