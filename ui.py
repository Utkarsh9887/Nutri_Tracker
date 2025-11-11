# ui.py
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from datetime import date
import logging
import random
from food_search import search_foods

# Project modules (must exist in your project)
from constant import COLORS
from db import (
    connect_to_db, login_user, create_user, update_user_profile, view_past_logs,
    fetch_past_logs_for_plot, get_user_data_for_ml, predict_calorie_goal,
    get_all_users, get_user_streak, get_today_water, update_water,
    set_admin_status, reset_user_password, delete_user
)
from usda_api import USDANutritionAPI
from nutrition import log_food
from utils import is_number

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("NutriAI.UI")

# Theme presets
LIGHT_THEME = {"background": "#F9F9F9", "foreground": "#000000", "frame": "#FFFFFF"}
DARK_THEME = {"background": "#1E1E1E", "foreground": "#FFFFFF", "frame": "#2C2C2C"}


class ModernNutritionTracker:
    """Refactored and modular UI for NutriAI."""

    def __init__(self, root):
        self.root = root
        self.root.title("🍎 NutriAI - Modern Nutrition Tracker")
        self.root.geometry("1000x700")
        # DB / services
        self.conn = connect_to_db()
        self.usda_api = USDANutritionAPI()

        # session
        self.current_user_id = None
        self.current_username = None
        self.is_admin = False

        # style/theme
        self.theme = DARK_THEME
        self.style = ttk.Style()
        self.style.theme_use("clam")
        self.configure_styles()

        # main frame
        self.root.configure(bg=self.theme["background"])
        self.main_frame = ttk.Frame(self.root, style="TFrame")
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # start screen
        self.show_auth_screen()

    # ---------------------------
    # Helper utilities & styling
    # ---------------------------
    def configure_styles(self):
        self.style.configure("TFrame", background=self.theme["frame"])
        self.style.configure("TLabel", background=self.theme["background"],
                             foreground=self.theme["foreground"], font=("Segoe UI", 10))
        self.style.configure("Title.TLabel", font=("Segoe UI", 18, "bold"), foreground=COLORS.get("primary", "#1976D2"))
        self.style.configure("Subtitle.TLabel", font=("Segoe UI", 14, "bold"), foreground=COLORS.get("secondary", "#388E3C"))
        self.style.configure("Modern.TButton", font=("Segoe UI", 10, "bold"))

    def create_window(self, title, size="400x300"):
        win = tk.Toplevel(self.root)
        win.title(title)
        win.geometry(size)
        win.configure(bg=COLORS.get('background', self.theme['background']))
        win.grab_set()
        return win

    def create_button(self, parent, text, command, color=None, **kwargs):
        color = color or COLORS.get("primary", "#1976D2")
        btn = tk.Button(parent, text=text, command=command, bg=color, fg="white",
                        font=kwargs.get("font", ("Segoe UI", 12, "bold")),
                        width=kwargs.get("width", 20), height=kwargs.get("height", 2),
                        border=0, cursor="hand2")
        # hover effects
        btn.bind("<Enter>", lambda e, b=btn: b.configure(bg=COLORS.get("accent", "#0288D1")))
        btn.bind("<Leave>", lambda e, b=btn, c=color: b.configure(bg=c))
        return btn

    def show_message(self, title, msg, level="info"):
        if level == "error":
            messagebox.showerror(title, msg)
        elif level == "warn":
            messagebox.showwarning(title, msg)
        else:
            messagebox.showinfo(title, msg)

    def clear_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    def toggle_theme(self):
        self.theme = LIGHT_THEME if self.theme == DARK_THEME else DARK_THEME
        self.configure_styles()
        self.root.configure(bg=self.theme["background"])
        self.show_message("Theme Changed", "Switched theme successfully!")

    def exit_program(self):
        if messagebox.askokcancel("Exit", "Exit application?"):
            self.root.quit()

    # ---------------------------
    # Authentication
    # ---------------------------
    def show_auth_screen(self):
        self.clear_frame()
        header = ttk.Frame(self.main_frame)
        header.pack(pady=(50, 30))

        ttk.Label(header, text="🍎", font=("Segoe UI", 48)).pack()
        ttk.Label(header, text="NutriAI", style="Title.TLabel").pack()
        ttk.Label(header, text="Your AI-Powered Nutrition Companion", style="Subtitle.TLabel").pack()

        btn_frame = ttk.Frame(self.main_frame)
        btn_frame.pack(pady=30)

        self.create_button(btn_frame, "Sign Up", lambda: self.show_auth_window("signup"), COLORS.get("primary")).pack(pady=10)
        self.create_button(btn_frame, "Login", lambda: self.show_auth_window("login"), COLORS.get("secondary")).pack(pady=10)
        self.create_button(btn_frame, "Exit", self.exit_program, COLORS.get("error")).pack(pady=10)

    def show_auth_window(self, mode="login"):
        title = "Login" if mode == "login" else "Sign Up"
        win = self.create_window(title, size="420x320")

        ttk.Label(win, text=f"{title} to Your Account", style="Title.TLabel").pack(pady=18)
        form = ttk.Frame(win)
        form.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)

        ttk.Label(form, text="Username:").grid(row=0, column=0, sticky=tk.W, pady=5)
        user_entry = ttk.Entry(form, width=30)
        user_entry.grid(row=0, column=1, pady=5, padx=10)

        ttk.Label(form, text="Password:").grid(row=1, column=0, sticky=tk.W, pady=5)
        pass_entry = ttk.Entry(form, width=30, show="*")
        pass_entry.grid(row=1, column=1, pady=5, padx=10)

        confirm_entry = None
        if mode == "signup":
            ttk.Label(form, text="Confirm Password:").grid(row=2, column=0, sticky=tk.W, pady=5)
            confirm_entry = ttk.Entry(form, width=30, show="*")
            confirm_entry.grid(row=2, column=1, pady=5, padx=10)

        btn_frame = ttk.Frame(form)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=18)
        ttk.Button(btn_frame, text=title, style="Modern.TButton",
                   command=lambda: self.handle_auth_submit(mode, user_entry, pass_entry, confirm_entry, win)).pack(side=tk.LEFT, padx=8)
        ttk.Button(btn_frame, text="Cancel", command=win.destroy).pack(side=tk.LEFT, padx=8)

    def handle_auth_submit(self, mode, user_entry, pass_entry, confirm_entry, win):
        username = user_entry.get().strip()
        password = pass_entry.get().strip()
        if not username or not password:
            self.show_message("Error", "Please fill all fields", "error")
            return

        if mode == "signup":
            confirm = confirm_entry.get().strip() if confirm_entry else ""
            if password != confirm:
                self.show_message("Error", "Passwords do not match", "error")
                return
            try:
                create_user(self.conn, username, password)
                self.show_message("Success", "Account created successfully!")
                win.destroy()
            except Exception as e:
                logger.exception("Signup failed")
                self.show_message("Error", f"Sign up failed: {e}", "error")
        else:
            try:
                result = login_user(self.conn, username, password)
                if result:
                    self.current_user_id, self.current_username, self.is_admin = result
                    self.show_message("Success", f"Welcome {self.current_username}!")
                    win.destroy()
                    self.show_dashboard()
                else:
                    self.show_message("Error", "Invalid username or password", "error")
            except Exception as e:
                logger.exception("Login error")
                self.show_message("Error", f"Login failed: {e}", "error")

    # ---------------------------
    # Dashboard & components
    # ---------------------------
    def show_dashboard(self):
        self.clear_frame()
        self._build_header()
        self._build_action_buttons()
        self._build_water_tracker()
        self._build_achievements_section()
        self._build_tip_section()

    def _build_header(self):
        header = ttk.Frame(self.main_frame)
        header.pack(fill=tk.X, pady=(10, 20))
        ttk.Label(header, text=f"Welcome, {self.current_username} 👋", style="Title.TLabel").pack(side=tk.LEFT)

        button_frame = tk.Frame(header, bg=self.theme["background"])
        button_frame.pack(side=tk.RIGHT)
        tk.Button(button_frame, text="🌗 Toggle Theme", command=self.toggle_theme,
                  bg=COLORS["error"], fg='white', font=("Segoe UI", 10), border=0, cursor='hand2').pack(side=tk.RIGHT, padx=5)
        tk.Button(button_frame, text="Logout", command=self.logout,
                  bg=COLORS["error"], fg='white', font=("Segoe UI", 10), border=0, cursor='hand2').pack(side=tk.RIGHT, padx=5)

    def _build_action_buttons(self):
        actions = [
            ("📊 Profile", self.show_profile_window, COLORS.get("primary")),
            ("➕ Log Food", self.show_log_food_window, COLORS.get("secondary")),
            ("📋 View Logs", self.view_past_logs_window, "#9C27B0"),
            ("📈 Analytics", self.show_analytics_dashboard, "#607D8B"),
            ("💡 Recommendations", self.show_recommendations, "#E91E63")
        ]
        if self.is_admin:
            actions.append(("👥 All Users", self.show_all_users_window, "#3F51B5"))

        frame = ttk.Frame(self.main_frame)
        frame.pack(fill=tk.X, pady=10)

        for i, (text, cmd, color) in enumerate(actions):
            btn = self.create_button(frame, text, cmd, color)
            btn.config(width=15, height=3, font=("Segoe UI", 11, "bold"))
            btn.grid(row=i // 3, column=i % 3, padx=10, pady=10, sticky='nsew')
            frame.columnconfigure(i % 3, weight=1)

    def _build_water_tracker(self):
        water_frame = ttk.LabelFrame(self.main_frame, text="💧 Water Intake", padding=10)
        water_frame.pack(fill=tk.X, padx=20, pady=10)

        daily_goal = 8
        current_glasses = get_today_water(self.conn, self.current_user_id) if self.current_user_id else 0
        self.water_labels = []

        def refresh_display():
            for lbl in self.water_labels:
                lbl.destroy()
            self.water_labels.clear()
            for i in range(daily_goal):
                symbol = "💧" if i < current_glasses else "⚪"
                lbl = ttk.Label(water_frame, text=symbol, font=("Arial", 18))
                lbl.grid(row=0, column=i, padx=5)
                self.water_labels.append(lbl)

        def add_glass():
            nonlocal current_glasses
            if current_glasses < daily_goal:
                current_glasses += 1
                if self.current_user_id is not None:
                    update_water(self.conn, int(self.current_user_id), current_glasses)
                refresh_display()

        def remove_glass():
            nonlocal current_glasses
            if current_glasses > 0:
                current_glasses -= 1
                if self.current_user_id is not None:
                    update_water(self.conn, self.current_user_id, current_glasses)
                refresh_display()

        btn_frame = ttk.Frame(water_frame)
        btn_frame.grid(row=1, column=0, columnspan=daily_goal, pady=5)
        ttk.Button(btn_frame, text="➕ Add", command=add_glass, style="Modern.TButton").pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="➖ Remove", command=remove_glass, style="Modern.TButton").pack(side=tk.LEFT, padx=5)
        refresh_display()

    def _build_achievements_section(self):
        streak = get_user_streak(self.conn, self.current_user_id) if self.current_user_id else 0
        ttk.Label(self.main_frame, text=f"🔥 Current Streak: {streak} days", font=("Arial", 12), foreground="orange").pack(pady=10)
        achievements = self.get_achievements()
        self.achievements_section = AchievementsSection(self.main_frame)
        self.achievements_section.display_achievements(achievements)

    def _build_tip_section(self):
        tip_frame = ttk.LabelFrame(self.main_frame, text="💡 Tip of the Day", padding=10)
        tip_frame.pack(fill=tk.X, padx=20, pady=10)
        tip_label = ttk.Label(tip_frame, text=self.get_daily_tip(), font=("Arial", 11), wraplength=500, justify="center")
        tip_label.pack(pady=5)

    def logout(self):
        self.current_user_id = None
        self.current_username = None
        self.is_admin = False
        self.show_auth_screen()
    # ---------------------------
    # Profile Management
    # ---------------------------
    def show_profile_window(self):
        if self.current_user_id is None:
            self.show_message("Error", "You must be logged in to view your profile.", "error")
            return
        win = self.create_window("User Profile", size="420x500")
        ttk.Label(win, text="Profile Details", style='Title.TLabel').pack(pady=18)
        form = ttk.Frame(win)
        form.pack(padx=20, pady=10, fill=tk.BOTH, expand=True)

        fields = [
            ("Age", "age", ttk.Entry(form, width=30)),
            ("Gender", "gender", ttk.Combobox(form, values=["Male", "Female", "Other"], width=28)),
            ("Height (cm)", "height", ttk.Entry(form, width=30)),
            ("Weight (kg)", "weight", ttk.Entry(form, width=30)),
            ("Goal Weight (kg)", "goal_weight", ttk.Entry(form, width=30)),
            ("Activity Level", "activity_level", ttk.Combobox(form, values=["Low", "Moderate", "High"], width=28)),
            ("Weight Goal", "weight_goal", ttk.Combobox(form, values=["Lose", "Maintain", "Gain"], width=28))
        ]

        self.profile_entries = {}
        for i, (label, key, widget) in enumerate(fields):
            ttk.Label(form, text=f"{label}:").grid(row=i, column=0, sticky=tk.W, pady=5)
            widget.grid(row=i, column=1, pady=5, padx=10)
            self.profile_entries[key] = widget

        def save_profile():
            try:
                data = {}
                for key, widget in self.profile_entries.items():
                    val = widget.get()
                    if key in ["age", "height", "weight", "goal_weight"] and val and not is_number(val):
                        self.show_message("Invalid Input", f"Please enter a valid number for {key}.", "warn")
                        return
                    data[key] = float(val) if is_number(val) else val or None

                if self.current_user_id is not None:
                    update_user_profile(
                        self.conn, int(self.current_user_id),
                        data.get('age'), data.get('gender'),
                        data.get('height'), data.get('weight'),
                        data.get('goal_weight'),
                        data.get('activity_level'), data.get('weight_goal')
                    )
                else:
                    self.show_message("Error", "User ID is missing. Please log in again.", "error")
                    win.destroy()
                    return
                self.show_message("Success", "Profile updated successfully!")
                win.destroy()
            except Exception as e:
                logger.exception("Profile update failed")
                self.show_message("Error", f"Failed to update profile: {e}", "error")

        btn_frame = ttk.Frame(form)
        btn_frame.grid(row=len(fields), column=0, columnspan=2, pady=14)
        ttk.Button(btn_frame, text="Save", command=save_profile, style="Modern.TButton").pack(side=tk.LEFT, padx=8)
        ttk.Button(btn_frame, text="Cancel", command=win.destroy).pack(side=tk.LEFT, padx=8)

    # ---------------------------
    # Food Logging & Viewing
    # ---------------------------
    def show_log_food_window(self):
        if self.current_user_id is None:
            self.show_message("Error", "You must be logged in to log food.", "error")
            return

        win = self.create_window("Log Food", size="420x320")
        ttk.Label(win, text="Log Your Food", style='Title.TLabel').pack(pady=18)
        form = ttk.Frame(win)
        form.pack(padx=20, pady=8, fill=tk.BOTH, expand=True)

        ttk.Label(form, text="Food Name:").grid(row=0, column=0, sticky=tk.W, pady=5)
        food_entry = ttk.Entry(form, width=30)
        food_entry.grid(row=0, column=1, padx=10, pady=5)
        
        '''# ---- Food search suggestions ----
        suggestion_box = tk.Listbox(form, width=30, height=5, font=("Segoe UI", 9))
        suggestion_box.grid(row=1, column=1, padx=10, pady=2, sticky="w")
        def update_suggestions(event=None):
            query = food_entry.get()
            suggestion_box.delete(0, tk.END)
            if not query:
                return
            suggestions = search_foods(query)
            for s in suggestions:
                suggestion_box.insert(tk.END, s)
        def select_suggestion(event=None):
            selection = suggestion_box.get(tk.ANCHOR)
            if selection:
                food_entry.delete(0, tk.END)
                food_entry.insert(0, selection)
                suggestion_box.delete(0, tk.END)
        # Bind typing + selection
        food_entry.bind("<KeyRelease>", update_suggestions)
        suggestion_box.bind("<Double-Button-1>", select_suggestion)'''

        ttk.Label(form, text="Quantity (grams):").grid(row=1, column=0, sticky=tk.W, pady=5)
        qty_entry = ttk.Entry(form, width=30)
        qty_entry.grid(row=1, column=1, padx=10, pady=5)

        ttk.Label(form, text="Date (YYYY-MM-DD):").grid(row=2, column=0, sticky=tk.W, pady=5)
        date_entry = ttk.Entry(form, width=30)
        date_entry.insert(0, str(date.today()))
        date_entry.grid(row=2, column=1, padx=10, pady=5)

        ttk.Label(form, text="Meal Type:").grid(row=3, column=0, sticky=tk.W, pady=5)
        meal_var = tk.StringVar()
        meal_combo = ttk.Combobox(form, textvariable=meal_var, values=["Breakfast", "Lunch", "Dinner", "Snack"], width=27)
        meal_combo.grid(row=3, column=1, padx=10, pady=5)

        def log_food_action():
            try:
                food = food_entry.get().strip()
                qty = qty_entry.get().strip()
                meal = meal_var.get().strip()
                date_val = date_entry.get().strip()
                if not food or not qty or not meal:
                    self.show_message("Error", "All fields are required.", "error")
                    return
                if not is_number(qty):
                    self.show_message("Error", "Quantity must be a number.", "error")
                    return

                qty = float(qty)
                estimated, _ = log_food(self.conn, self.current_user_id, food, qty, date_val, meal, self.usda_api)

                msg = f"Logged {qty}g of {food}."
                if estimated:
                    msg += " (Estimated values used)"
                self.show_message("Success", msg)
                win.destroy()
            except Exception as e:
                logger.exception("Failed to log food")
                self.show_message("Error", f"Failed to log food: {e}", "error")

        btn_frame = ttk.Frame(form)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=12)
        ttk.Button(btn_frame, text="Log Food", command=log_food_action, style="Modern.TButton").pack(side=tk.LEFT, padx=8)
        ttk.Button(btn_frame, text="Cancel", command=win.destroy).pack(side=tk.LEFT, padx=8)

    def view_past_logs_window(self):
        if self.current_user_id is None:
            self.show_message("Error", "You must be logged in to view logs.", "error")
            return

        try:
            logs = view_past_logs(self.conn, self.current_user_id)
            win = self.create_window("Food Logs", size="900x450")
            ttk.Label(win, text="Your Food Log History", style='Title.TLabel').pack(pady=18)

            if not logs:
                ttk.Label(win, text="No logs found. Start logging your meals!").pack(pady=50)
                return

            frame = ttk.Frame(win)
            frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)

            cols = ("Date", "Food", "Qty (g)", "Carbs", "Calories", "Protein", "Fat")
            tree = ttk.Treeview(frame, columns=cols, show="headings")
            for col in cols:
                tree.heading(col, text=col)
                tree.column(col, width=110, anchor=tk.CENTER)
            for log in logs:
                tree.insert("", tk.END, values=log)

            scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
            tree.pack(fill=tk.BOTH, expand=True)
        except Exception as e:
            logger.exception("Failed to view logs")
            self.show_message("Error", f"Unable to load logs: {e}", "error")

    # ---------------------------
    # Analytics (plots)
    # ---------------------------
    def show_analytics_dashboard(self):
        if self.current_user_id is None:
            self.show_message("Error", "You must be logged in to view analytics.", "error")
            return
        try:
            data = fetch_past_logs_for_plot(self.conn, self.current_user_id)
            win = self.create_window("Analytics Dashboard", size="1000x700")

            if data.empty:
                ttk.Label(win, text="No data available for analytics.", style='Subtitle.TLabel').pack(pady=50)
                return

            notebook = ttk.Notebook(win)
            notebook.pack(fill=tk.BOTH, expand=True)

            # Calories vs Goal
            frame1 = ttk.Frame(notebook); notebook.add(frame1, text="Calories vs Goal")
            goal = predict_calorie_goal(self.conn, self.current_user_id)
            self._plot_bar_with_goal(frame1, data["Date"], data["Calories"], goal, "Calories vs Goal", "Calories")

            # Macronutrients
            frame2 = ttk.Frame(notebook); notebook.add(frame2, text="Macronutrient Breakdown")
            self._plot_pie_chart(frame2, data)

            # Weight Progress
            frame3 = ttk.Frame(notebook); notebook.add(frame3, text="Weight Progress")
            self._plot_weight_progress(frame3, data)

            # Weekly trends
            frame4 = ttk.Frame(notebook); notebook.add(frame4, text="Weekly Trends")
            self._plot_weekly_trends(frame4, data)
        except Exception as e:
            logger.exception("Analytics failed")
            self.show_message("Error", f"Failed to load analytics: {e}", "error")

    def _display_plot(self, parent, fig):
        canvas = FigureCanvasTkAgg(fig, parent)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _plot_bar_with_goal(self, parent, x, y, goal, title, ylabel):
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.bar(x, y, color=COLORS.get('secondary', '#66BB6A'), label="Consumed")
        ax.axhline(y=goal, color="red", linestyle="--", label="Goal")
        ax.set_title(title)
        ax.set_ylabel(ylabel)
        ax.legend()
        plt.tight_layout()
        self._display_plot(parent, fig)

    def _plot_pie_chart(self, parent, data):
        try:
            last_day = data.iloc[-1]
            macros = [last_day["Carbs"], last_day["Protein"], last_day["Fat"]]
            labels = ["Carbs", "Protein", "Fat"]
            fig, ax = plt.subplots(figsize=(5, 5))
            ax.pie(macros, labels=labels, autopct="%1.1f%%", startangle=90,
                   colors=["#42A5F5", "#66BB6A", "#FFA726"])
            ax.set_title(f"Macronutrient Breakdown ({last_day['Date']})")
            plt.tight_layout()
            self._display_plot(parent, fig)
        except Exception:
            ttk.Label(parent, text="Insufficient data for pie chart.").pack(pady=20)

    def _plot_weight_progress(self, parent, data):
        if self.current_user_id is not None:
            user_data = get_user_data_for_ml(self.conn, self.current_user_id)
        if not user_data or "weight" not in user_data:
            ttk.Label(parent, text="No weight data available.").pack(pady=20)
            return
        weights = [user_data["weight"]] * len(data)
        fig, ax = plt.subplots(figsize=(6, 4))
        ax.plot(data["Date"], weights, label="Current Weight", marker="o")
        if "goal_weight" in user_data:
            ax.axhline(y=user_data["goal_weight"], color="green", linestyle="--", label="Goal Weight")
        ax.set_title("Weight Progress")
        ax.legend()
        plt.tight_layout()
        self._display_plot(parent, fig)

    def _plot_weekly_trends(self, parent, data):
        weekly = data.tail(7)
        if weekly.empty:
            ttk.Label(parent, text="No weekly data available.").pack(pady=20)
            return
        fig, ax = plt.subplots(figsize=(7, 4))
        ax.bar(weekly["Date"], weekly["Calories"], color="#42A5F5", alpha=0.7, label="Calories")
        ax.plot(weekly["Date"], weekly["Protein"], marker="o", color="#66BB6A", label="Protein")
        ax.plot(weekly["Date"], weekly["Carbs"], marker="s", color="#FFA726", label="Carbs")
        ax.plot(weekly["Date"], weekly["Fat"], marker="^", color="#EF5350", label="Fat")
        ax.set_title("Last 7 Days: Calories & Macronutrients")
        ax.legend()
        plt.tight_layout()
        self._display_plot(parent, fig)

    # ---------------------------
    # Recommendations
    # ---------------------------
    def show_recommendations(self):
        if self.current_user_id is None:
            self.show_message("Error", "You must be logged in to view recommendations.", "error")
            return

        recs = []
        try:
            data = fetch_past_logs_for_plot(self.conn, self.current_user_id)
            if data.empty:
                recs.append("📋 No data yet. Start logging your meals to receive personalized insights.")
            else:
                avg_cal = data["Calories"].mean()
                goal = predict_calorie_goal(self.conn, self.current_user_id)
                if avg_cal < goal * 0.9:
                    recs.append("⚡ You're consuming fewer calories than your goal. Try adding healthy calorie-dense foods like nuts, dairy, or whole grains.")
                elif avg_cal > goal * 1.1:
                    recs.append("⚠️ You're exceeding your calorie goal. Cut down on sugary drinks and fried snacks.")
                else:
                    recs.append("✅ Great job! Your calorie intake is well balanced with your goal.")

                avg_protein = data["Protein"].mean()
                if avg_protein < 50:
                    recs.append("🍗 Increase protein — eggs, beans, tofu, or lean meats help.")

                avg_carbs = data["Carbs"].mean()
                if avg_carbs < 130:
                    recs.append("🥦 Consider more complex carbs (brown rice, oats, vegetables).")

                avg_fat = data["Fat"].mean()
                if avg_fat > 70:
                    recs.append("🧈 Consider reducing saturated fats and fried foods.")
        except Exception as e:
            logger.exception("Recommendations error")
            recs.append(f"❌ Could not load recommendations: {e}")

        win = self.create_window("AI Recommendations", size="650x450")
        ttk.Label(win, text="Personalized Recommendations", style='Title.TLabel').pack(pady=12)
        text_box = scrolledtext.ScrolledText(win, wrap=tk.WORD, width=75, height=25)
        text_box.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        for rec in recs:
            text_box.insert(tk.END, f"• {rec}\n\n")
        text_box.config(state=tk.DISABLED)

    # ---------------------------
    # Admin panel & helpers
    # ---------------------------
    def show_all_users_window(self):
        if not self.is_admin:
            self.show_message("Access Denied", "You must be an admin to access this feature.", "error")
            return
        try:
            users = get_all_users(self.conn)
            win = self.create_window("Admin Panel - All Users", size="950x500")
            ttk.Label(win, text="Registered Users", style='Title.TLabel').pack(pady=18)
            if not users:
                ttk.Label(win, text="No registered users found.").pack(pady=50)
                return

            frame = ttk.Frame(win)
            frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
            cols = ("ID", "Username", "Age", "Gender", "Height", "Weight", "Goal Weight", "Activity Level", "Weight Goal", "Is Admin")
            tree = ttk.Treeview(frame, columns=cols, show="headings", selectmode="browse")
            for col in cols:
                tree.heading(col, text=col)
                tree.column(col, anchor=tk.CENTER, width=90)
            for user in users:
                tree.insert("", tk.END, values=user)
            tree.pack(fill=tk.BOTH, expand=True)
            scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=tree.yview)
            tree.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

            btn_frame = ttk.Frame(win)
            btn_frame.pack(pady=12)
            ttk.Button(btn_frame, text="Promote/Demote", style='Modern.TButton',
                       command=lambda: self._toggle_admin_status(tree, win)).pack(side=tk.LEFT, padx=8)
            ttk.Button(btn_frame, text="Reset Password", style='Modern.TButton',
                       command=lambda: self._reset_user_password(tree)).pack(side=tk.LEFT, padx=8)
            ttk.Button(btn_frame, text="Delete User", style='Modern.TButton',
                       command=lambda: self._delete_user(tree, win)).pack(side=tk.LEFT, padx=8)
        except Exception as e:
            logger.exception("Admin panel failed")
            self.show_message("Error", f"Failed to load user data: {e}", "error")

    def _get_selected_user(self, tree):
        sel = tree.selection()
        if not sel:
            self.show_message("No Selection", "Please select a user first.", "warn")
            return None
        return tree.item(sel[0])["values"]

    def _toggle_admin_status(self, tree, win):
        user = self._get_selected_user(tree)
        if not user:
            return
        user_id, username, *_, is_admin = user
        try:
            new_status = not bool(is_admin)
            set_admin_status(self.conn, user_id, new_status)
            self.show_message("Success", f"{username} is now {'an Admin' if new_status else 'a regular user'}.")
            win.destroy()
            self.show_all_users_window()
        except Exception as e:
            logger.exception("Toggle admin failed")
            self.show_message("Error", f"Failed to change status: {e}", "error")

    def _reset_user_password(self, tree):
        user = self._get_selected_user(tree)
        if not user:
            return
        user_id, username, *_ = user
        new_pw = simpledialog.askstring("Reset Password", f"Enter new password for {username}:")
        if new_pw:
            try:
                reset_user_password(self.conn, user_id, new_pw)
                self.show_message("Success", f"Password reset successfully for {username}.")
            except Exception as e:
                logger.exception("Reset password failed")
                self.show_message("Error", f"Password reset failed: {e}", "error")

    def _delete_user(self, tree, win):
        user = self._get_selected_user(tree)
        if not user:
            return
        user_id, username, *_ = user
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete {username}?"):
            try:
                delete_user(self.conn, user_id)
                self.show_message("Deleted", f"User {username} and related logs removed.")
                win.destroy()
                self.show_all_users_window()
            except Exception as e:
                logger.exception("Delete user failed")
                self.show_message("Error", f"Failed to delete user: {e}", "error")

    # ---------------------------
    # Achievements
    # ---------------------------
    def get_achievements(self):
        achievements = []
        try:
            data = fetch_past_logs_for_plot(self.conn, self.current_user_id)
            if not data.empty:
                achievements.append({"title": "🥇 First Log", "description": "You've started your journey — great first step!", "progress": 100, "tier": "bronze"})
            streak = get_user_streak(self.conn, self.current_user_id) if self.current_user_id else 0
            if streak >= 7:
                achievements.append({"title": "📅 7-Day Streak", "description": "Amazing consistency! You've logged for 7 days straight!", "progress": 100, "tier": "silver"})
            elif streak > 0:
                achievements.append({"title": "📆 Streak in Progress", "description": f"Current streak: {streak} days. Keep it going!", "progress": int(min(100, (streak / 7) * 100)), "tier": "bronze"})

            if not data.empty:
                if self.current_user_id is not None:
                    goal = predict_calorie_goal(self.conn, self.current_user_id)
                hit_goal_days = ((data["Calories"] >= goal * 0.9) & (data["Calories"] <= goal * 1.1)).sum()
                if hit_goal_days >= 5:
                    achievements.append({"title": "🎯 Calorie Goal Master", "description": "You've consistently hit your calorie goals this week!", "progress": 100, "tier": "gold"})
                elif hit_goal_days > 0:
                    achievements.append({"title": "🎯 Calorie Tracker", "description": f"You hit your calorie goal {hit_goal_days} times this week!", "progress": int(min(100, (hit_goal_days / 5) * 100)), "tier": "bronze"})

            protein_days = (data["Protein"] >= 50).sum() if not data.empty else 0
            if protein_days >= 5:
                achievements.append({"title": "💪 Protein Pro", "description": "You've reached your protein goal consistently this week!", "progress": 100, "tier": "silver"})
            elif protein_days > 0:
                achievements.append({"title": "💪 Protein Progress", "description": f"Protein goal achieved on {protein_days} days.", "progress": int(min(100, (protein_days / 5) * 100)), "tier": "bronze"})
        except Exception as e:
            logger.exception("Get achievements failed")
            achievements.append({"title": "❌ Error Loading Data", "description": "Could not load your achievements at this time.", "progress": 0, "tier": "bronze"})
        return achievements

    def get_daily_tip(self):
        tips = [
            "Drink a glass of water before each meal to help control appetite.",
            "Include protein in every meal to stay full longer.",
            "Aim for 5 servings of fruits and vegetables daily.",
            "Plan your meals ahead to avoid unhealthy last-minute choices.",
            "Don't skip breakfast - it kickstarts your metabolism.",
            "Choose whole grains over refined grains for better nutrition.",
            "Listen to your body's hunger and fullness cues.",
            "Get enough sleep - it affects your food choices and metabolism.",
            "Stay active throughout the day, not just during workouts.",
            "Healthy fats like avocado and nuts are good for you in moderation."
        ]
        return random.choice(tips)


# ---------------------------
# AchievementsSection (UI helper)
# ---------------------------
class AchievementsSection:
    def __init__(self, parent):
        self.frame = ttk.LabelFrame(parent, text="🏆 Achievements", padding=10)
        self.frame.pack(fill=tk.X, padx=20, pady=10)
        self.widgets = []

    def display_achievements(self, achievements):
        for w in self.widgets:
            try:
                w.destroy()
            except Exception:
                pass
        self.widgets.clear()

        if not achievements:
            lbl = ttk.Label(self.frame, text="No achievements yet. Start logging to earn rewards!")
            lbl.pack(pady=10)
            self.widgets.append(lbl)
            return

        for ach in achievements:
            self._create_achievement_widget(ach)

    def _create_achievement_widget(self, ach):
        tier_colors = {"bronze": "#CD7F32", "silver": "#C0C0C0", "gold": "#FFD700"}
        color = tier_colors.get(ach.get("tier", "bronze"), "#CD7F32")

        frame = ttk.Frame(self.frame, relief="solid", borderwidth=1)
        frame.pack(fill=tk.X, pady=5, padx=5)

        content = ttk.Frame(frame)
        content.pack(fill=tk.X, padx=10, pady=6)

        ttk.Label(content, text=ach["title"], font=("Arial", 12, "bold"), foreground=color).grid(row=0, column=0, sticky=tk.W)
        ttk.Label(content, text=ach["description"], font=("Arial", 9)).grid(row=1, column=0, sticky=tk.W, pady=2)

        bar_frame = ttk.Frame(content)
        bar_frame.grid(row=2, column=0, sticky=tk.W + tk.E, pady=(5, 0))
        progress = ttk.Progressbar(bar_frame, length=200, value=ach.get("progress", 0), mode="determinate")
        progress.pack(side=tk.LEFT, padx=(0, 10))
        ttk.Label(bar_frame, text=f"{ach.get('progress', 0)}%").pack(side=tk.LEFT)

        self.widgets.extend([frame, content, bar_frame, progress])
    