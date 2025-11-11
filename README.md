# 🥗 Nutrition AI — Intelligent Nutrition Analysis System

## 📘 Overview
**Nutrition AI** is an intelligent nutrition analysis tool that calculates and provides nutritional data for different foods using both **local datasets** (`nutrition.csv`) and **API-based data retrieval** from the USDA database.  
It allows users to input ingredients, quantities, or meals, and get detailed nutritional breakdowns including calories, proteins, fats, and more.  

The project features:
- Automatic nutrition data retrieval from API (fallback to local database if API fails)
- Admin interface for managing data
- User interface built with Python (`Tkinter`)
- Integrated database for storing and managing food entries

---

## 📂 Project Structure

```
nutrition_Ai/
│
├── constant.py           # Contains constants and configuration variables
├── create_admin.py       # Script to create or manage admin users
├── db.py                 # Handles database connections and CRUD operations
├── main.py               # Main application entry point
├── nutrition.csv         # Local nutrition dataset used as fallback
├── nutrition.py          # Core logic for nutrition data calculations
├── nutrition_local.ipynb # Jupyter notebook for data exploration and testing
├── ui.py                 # GUI built using Tkinter for user interaction
├── usda_api.py           # Handles data retrieval from USDA API
├── utils.py              # Helper functions used across the app
└── .git/                 # Git version control folder
```

---

## ⚙️ Installation & Setup

### 1️⃣ Prerequisites
Ensure you have the following installed:
- **Python 3.8+**
- **pip** (Python package manager)
- **SQLite** (default database used)

### 2️⃣ Clone or Extract the Project
```bash
git clone https://github.com/yourusername/nutrition_ai.git
cd nutrition_ai
```

Or, if using the provided ZIP:
```bash
unzip "nutrition_Ai (2).zip"
cd nutrition_Ai
```

### 3️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```
*(If `requirements.txt` is missing, install manually:)*
```bash
pip install pandas requests tkinter
```

---

## 🚀 How to Run

### Run the Main Application
```bash
python main.py
```

### Access the GUI Dashboard
The user interface (`ui.py`) allows you to:
- Enter food name or ingredient
- Input quantity (grams/ml)
- View detailed nutritional breakdown
- Save results to database

```bash
python ui.py
```

### Create an Admin (Optional)
```bash
python create_admin.py
```

---

## 🧠 How It Works

1. **User Input**: User enters a food item and its quantity.
2. **Data Retrieval**: The system fetches data from:
   - USDA API (primary source)
   - `nutrition.csv` (fallback source)
3. **Computation**: Nutrition values are adjusted based on the input quantity.
4. **Display**: Results are displayed in GUI and optionally saved to the database.

---

## 📊 Dataset

The included dataset `nutrition.csv` contains:
- Food names
- Macronutrient values (Calories, Protein, Fat, Carbs, Fiber)
- Serving sizes and measurement units

---

## 🧩 API Integration

The project integrates with the **USDA FoodData Central API** via `usda_api.py`.

To use the API:
1. Obtain a free API key from [USDA FoodData Central](https://fdc.nal.usda.gov/api-key-signup.html)
2. Add your API key in `constant.py`:
   ```python
   USDA_API_KEY = "your_api_key_here"
   ```

---

## 💾 Database

- Default database: **SQLite**
- Managed via `db.py`
- Stores:
  - User searches
  - Saved results
  - Admin accounts

---

## 📈 Future Enhancements

- Add machine learning model for nutrition prediction
- Enable multi-language support
- Add meal plan generation based on calorie goals
- Integration with fitness tracking apps

---

## 🧑‍💻 Contributors

- **Developer:** Utkarsh Verma, Saksham Kannojiya, Vaibhav Bhandari
- **Language:** Python
- **Tools Used:** Tkinter, Pandas, Requests, SQLite

---

## 📜 License

This project is open-source under the **MIT License** — feel free to use, modify, and distribute it with proper attribution.
