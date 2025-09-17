# ui.py
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, simpledialog
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
from db import get_all_users

from constant import COLORS, USDA_API_KEY
from db import connect_to_db, login_user, create_user, update_user_profile, view_past_logs
from db import fetch_past_logs_for_plot, get_user_data_for_ml, predict_calorie_goal
from usda_api import USDANutritionAPI
from nutrition import log_food, generate_recommendations
from utils import is_number, parse_date

class ModernNutritionTracker:
    def __init__(self, root):
        self.conn = connect_to_db()
        self.current_user_id = None
        self.current_username = None
        self.is_admin: bool = False
        self.root = root
        self.root.title("🍎 NutriAI - Modern Nutrition Tracker")
        self.root.geometry("1000x700")
        self.root.configure(bg=COLORS['background'])

        self.usda_api = USDANutritionAPI(USDA_API_KEY)
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.configure_styles()
        self.setup_main_frame()

    def configure_styles(self):
        self.style.configure('TFrame', background=COLORS['background'])
        self.style.configure('TLabel', background=COLORS['background'],
                             foreground=COLORS['text'], font=('Segoe UI', 10))
        self.style.configure('Title.TLabel',
                             font=('Segoe UI', 18, 'bold'),
                             foreground=COLORS['primary'])
        self.style.configure('Subtitle.TLabel',
                             font=('Segoe UI', 14, 'bold'),
                             foreground=COLORS['secondary'])
        self.style.configure('Modern.TButton',
                             font=('Segoe UI', 10, 'bold'),
                             background=COLORS['primary'],
                             foreground='white',
                             borderwidth=0)
        self.style.map('Modern.TButton',
                       background=[('active', COLORS['secondary']),
                                   ('pressed', COLORS['accent'])])

    def setup_main_frame(self):
        self.main_frame = ttk.Frame(self.root, style='TFrame')
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        self.show_auth_screen()

    def clear_frame(self):
        for widget in self.main_frame.winfo_children():
            widget.destroy()

    # ====================
    # AUTH SCREENS
    # ====================
    def show_auth_screen(self):
        self.clear_frame()

        header_frame = ttk.Frame(self.main_frame)
        header_frame.pack(pady=(50, 30))
        ttk.Label(header_frame, text="🍎", font=('Segoe UI', 48)).pack()
        ttk.Label(header_frame, text="NutriAI", style='Title.TLabel').pack()
        ttk.Label(header_frame, text="Your AI-Powered Nutrition Companion",
                  style='Subtitle.TLabel').pack()

        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(pady=30)
        auth_buttons = [
            ("Sign Up", self.show_signup_window, COLORS['primary']),
            ("Login", self.show_login_window, COLORS['secondary']),
            ("Exit", self.exit_program, COLORS['error'])
        ]
        for text, command, color in auth_buttons:
            btn = tk.Button(button_frame, text=text, command=command,
                            bg=color, fg='white',
                            font=('Segoe UI', 12, 'bold'),
                            width=20, height=2, border=0, cursor='hand2')
            btn.pack(pady=10)
            btn.bind("<Enter>", lambda e, b=btn: b.configure(bg=COLORS['accent']))
            btn.bind("<Leave>", lambda e, b=btn, c=color: b.configure(bg=c))

    def show_signup_window(self):
        win = tk.Toplevel(self.root)
        win.title("Sign Up")
        win.geometry("400x300")
        win.configure(bg=COLORS['background'])
        win.grab_set()
        ttk.Label(win, text="Create Account", style='Title.TLabel').pack(pady=20)

        form = ttk.Frame(win)
        form.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        ttk.Label(form, text="Username:").grid(row=0, column=0, sticky=tk.W, pady=5)
        user_entry = ttk.Entry(form, width=30)
        user_entry.grid(row=0, column=1, pady=5, padx=10)
        ttk.Label(form, text="Password:").grid(row=1, column=0, sticky=tk.W, pady=5)
        pass_entry = ttk.Entry(form, width=30, show="*")
        pass_entry.grid(row=1, column=1, pady=5, padx=10)
        ttk.Label(form, text="Confirm:").grid(row=2, column=0, sticky=tk.W, pady=5)
        confirm_entry = ttk.Entry(form, width=30, show="*")
        confirm_entry.grid(row=2, column=1, pady=5, padx=10)

        def submit():
            u, p, c = user_entry.get(), pass_entry.get(), confirm_entry.get()
            if not u or not p:
                messagebox.showerror("Error", "Fill all fields")
                return
            if p != c:
                messagebox.showerror("Error", "Passwords don't match")
                return
            try:
                create_user(self.conn, u, p)
                messagebox.showinfo("Success", "Account created!")
                win.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))
        btn_frame = ttk.Frame(form)
        btn_frame.grid(row=3, column=0, columnspan=2, pady=20)
        ttk.Button(btn_frame, text="Sign Up", command=submit, style='Modern.TButton').pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Cancel", command=win.destroy).pack(side=tk.LEFT, padx=10)

    def show_login_window(self):
        win = tk.Toplevel(self.root)
        win.title("Login")
        win.geometry("400x250")
        win.configure(bg=COLORS['background'])
        win.grab_set()
        ttk.Label(win, text="Login to Your Account", style='Title.TLabel').pack(pady=20)

        form = ttk.Frame(win)
        form.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        ttk.Label(form, text="Username:").grid(row=0, column=0, sticky=tk.W, pady=5)
        user_entry = ttk.Entry(form, width=30)
        user_entry.grid(row=0, column=1, pady=5, padx=10)
        ttk.Label(form, text="Password:").grid(row=1, column=0, sticky=tk.W, pady=5)
        pass_entry = ttk.Entry(form, width=30, show="*", )
        pass_entry.grid(row=1, column=1, pady=5, padx=10)

        def submit():
            u, p = user_entry.get(), pass_entry.get()
            if not u or not p:
                messagebox.showerror("Error", "Fill all fields")
                return
            try:
                result = login_user(self.conn, u, p)
                if result is not None:   # ✅ check before unpacking
                    self.current_user_id, self.current_username, self.is_admin = result
                    messagebox.showinfo("Success", "Logged in!")
                    win.destroy()
                    self.show_dashboard()
                else:
                    messagebox.showerror("Error", "Invalid username or password")
            except Exception as e:
                messagebox.showerror("Error", f"Login failed: {e}")  


        btn_frame = ttk.Frame(form)
        btn_frame.grid(row=2, column=0, columnspan=2, pady=20)
        ttk.Button(btn_frame, text="Login", command=submit, style='Modern.TButton').pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Cancel", command=win.destroy).pack(side=tk.LEFT, padx=10)

    # ====================
    # DASHBOARD
    # ====================
    def show_dashboard(self):
        self.clear_frame()
        header = ttk.Frame(self.main_frame)
        header.pack(fill=tk.X, pady=(10, 20))
        ttk.Label(header, text=f"Welcome, {self.current_username}! 👋",
                  style='Title.TLabel').pack(side=tk.LEFT)
        tk.Button(header, text="Logout", command=self.logout,
                  bg=COLORS['error'], fg='white', font=('Segoe UI', 10),
                  border=0, cursor='hand2').pack(side=tk.RIGHT)

        actions = [
            ("📊 Profile", self.show_profile_window, COLORS['primary']),
            ("➕ Log Food", self.show_log_food_window, COLORS['secondary']),
            ("📋 View Logs", self.view_past_logs_window, '#9C27B0'),
            ("📈 Analytics", self.show_analytics_dashboard, '#607D8B'),
            ("💡 Recommendations", self.show_recommendations, '#E91E63')
        ]
        if self.is_admin:  # ✅ only admins see this button
            actions.append(("👥 All Users", self.show_all_users_window, '#3F51B5'))

        action_frame = ttk.Frame(self.main_frame)
        action_frame.pack(fill=tk.X, pady=10)
        for i, (text, cmd, color) in enumerate(actions):
            btn = tk.Button(action_frame, text=text, command=cmd,
                            bg=color, fg='white', font=('Segoe UI', 11, 'bold'),
                            width=15, height=3, border=0, cursor='hand2')
            btn.grid(row=i//3, column=i%3, padx=10, pady=10, sticky='nsew')
            action_frame.columnconfigure(i%3, weight=1)
            btn.bind("<Enter>", lambda e, b=btn: b.configure(bg=COLORS['accent']))
            btn.bind("<Leave>", lambda e, b=btn, c=color: b.configure(bg=c))

    def logout(self):
        self.current_user_id = None
        self.current_username = None
        self.show_auth_screen()

    def exit_program(self):
        if messagebox.askokcancel("Exit", "Exit application?"):
            self.root.quit()

    # ====================
    # PROFILE
    # ====================
    def show_profile_window(self):
        win = tk.Toplevel(self.root)
        win.title("Complete Profile")
        win.geometry("400x500")
        win.configure(bg=COLORS['background'])
        win.grab_set()
        ttk.Label(win, text="Profile", style='Title.TLabel').pack(pady=20)

        form = ttk.Frame(win)
        form.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        entries = {}
        fields = [("Age", "age"), ("Gender", "gender"),
                  ("Height (cm)", "height"), ("Weight (kg)", "weight"),
                  ("Goal Weight", "goal_weight"),
                  ("Activity Level", "activity_level"),
                  ("Weight Goal", "weight_goal")]
        for i, (label, key) in enumerate(fields):
            ttk.Label(form, text=label+":").grid(row=i, column=0, sticky=tk.W, pady=5)
            entry = ttk.Entry(form, width=30)
            entry.grid(row=i, column=1, pady=5, padx=10)
            entries[key] = entry

        def save():
            if self.current_user_id is None:
                messagebox.showerror("Error", "You must be logged in to update your profile.")
                return
            try:
                data = {k: (float(v.get()) if is_number(v.get()) else v.get())
                        for k, v in entries.items()}
                update_user_profile(self.conn, int(self.current_user_id),
                                    data['age'], data['gender'],
                                    data['height'], data['weight'],
                                    data['goal_weight'],
                                    data['activity_level'],
                                    data['weight_goal'])
                messagebox.showinfo("Success", "Profile updated!")
                win.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))
        btn_frame = ttk.Frame(form)
        btn_frame.grid(row=len(fields), column=0, columnspan=2, pady=20)
        ttk.Button(btn_frame, text="Save", command=save, style='Modern.TButton').pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Cancel", command=win.destroy).pack(side=tk.LEFT, padx=10)

    # ====================
    # FOOD LOGGING
    # ====================
    def show_log_food_window(self):
        win = tk.Toplevel(self.root)
        win.title("Log Food")
        win.geometry("400x300")
        win.configure(bg=COLORS['background'])
        win.grab_set()
        ttk.Label(win, text="Log Food", style='Title.TLabel').pack(pady=20)

        form = ttk.Frame(win)
        form.pack(pady=10, padx=20, fill=tk.BOTH, expand=True)
        ttk.Label(form, text="Food:").grid(row=0, column=0, pady=5, sticky=tk.W)
        food_entry = ttk.Entry(form, width=30)
        food_entry.grid(row=0, column=1, padx=10, pady=5)
        ttk.Label(form, text="Quantity (g):").grid(row=1, column=0, pady=5, sticky=tk.W)
        qty_entry = ttk.Entry(form, width=30)
        qty_entry.grid(row=1, column=1, padx=10, pady=5)
        ttk.Label(form, text="Date (YYYY-MM-DD):").grid(row=2, column=0, pady=5, sticky=tk.W)
        date_entry = ttk.Entry(form, width=30)
        date_entry.insert(0, "2025-09-12")
        date_entry.grid(row=2, column=1, padx=10, pady=5)
        ttk.Label(form, text="Meal Type:").grid(row=3, column=0, pady=5, sticky=tk.W)
        meal_var = tk.StringVar()
        meal_combo = ttk.Combobox(form, width=27, textvariable=meal_var,
                                  values=["Breakfast", "Lunch", "Dinner", "Snack"])
        meal_combo.grid(row=3, column=1, pady=5, padx=10)

        def submit():
            if self.current_user_id is None:
                messagebox.showerror("Error", "You must be logged in to log food.")
                return
            try:
                food, qty, date, meal = food_entry.get(), float(qty_entry.get()), date_entry.get(), meal_var.get()
                estimated, _ = log_food(self.conn, self.current_user_id, food, qty, date, meal, self.usda_api)
                msg = f"Logged {qty}g {food}"
                if estimated:
                    msg += " (estimated values)"
                messagebox.showinfo("Success", msg)
                win.destroy()
            except Exception as e:
                messagebox.showerror("Error", str(e))

        btn_frame = ttk.Frame(form)
        btn_frame.grid(row=4, column=0, columnspan=2, pady=20)
        ttk.Button(btn_frame, text="Log", command=submit, style='Modern.TButton').pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Cancel", command=win.destroy).pack(side=tk.LEFT, padx=10)

    def view_past_logs_window(self):
        if self.current_user_id is None:
            messagebox.showerror("Error", "You must be logged in to update your profile.")
            return
        logs = view_past_logs(self.conn, self.current_user_id)
        win = tk.Toplevel(self.root)
        win.title("Food Logs")
        win.geometry("700x400")
        win.configure(bg=COLORS['background'])
        ttk.Label(win, text="Your Food Log History", style='Title.TLabel').pack(pady=20)
        if not logs:
            ttk.Label(win, text="No logs found").pack(pady=50)
            return
        frame = ttk.Frame(win)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        cols = ("Date", "Food", "Qty", "Carbs", "Calories", "Protein", "Fat")
        tree = ttk.Treeview(frame, columns=cols, show="headings")
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=90, anchor=tk.CENTER)
        for log in logs:
            tree.insert("", tk.END, values=log)
        tree.pack(fill=tk.BOTH, expand=True)

    # ====================
    # ANALYTICS
    # ====================
    def show_analytics_dashboard(self):
        if self.current_user_id is None:
            messagebox.showerror("Error", "You must be logged in to view analytics.")
            return
        data = fetch_past_logs_for_plot(self.conn, self.current_user_id)
        win = tk.Toplevel(self.root)
        win.title("Analytics")
        win.geometry("1000x700")
        win.configure(bg=COLORS['background'])

        if data.empty:
            ttk.Label(win, text="No data to show").pack(pady=50)
            return

        notebook = ttk.Notebook(win)
        notebook.pack(fill=tk.BOTH, expand=True)

        # --- Calories vs Goal ---
        frame1 = ttk.Frame(notebook)
        notebook.add(frame1, text="Calories vs Goal")

        fig1, ax1 = plt.subplots(figsize=(6, 4))
        goal = predict_calorie_goal(self.conn, self.current_user_id)
        ax1.bar(data["Date"], data["Calories"], color=COLORS['secondary'], label="Consumed")
        ax1.axhline(y=goal, color="red", linestyle="--", label="Goal")
        ax1.set_title("Calories vs Goal")
        ax1.legend()
        canvas1 = FigureCanvasTkAgg(fig1, frame1)
        canvas1.draw()
        canvas1.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # --- Macronutrient Breakdown ---
        frame2 = ttk.Frame(notebook)
        notebook.add(frame2, text="Macronutrient Breakdown")

        last_day = data.iloc[-1]  # latest entry
        macros = [last_day["Carbs"], last_day["Protein"], last_day["Fat"]]
        labels = ["Carbs", "Protein", "Fat"]
        fig2, ax2 = plt.subplots(figsize=(5, 5))
        ax2.pie(macros, labels=labels, autopct="%1.1f%%", startangle=90,
                colors=["#42A5F5", "#66BB6A", "#FFA726"])
        ax2.set_title(f"Macronutrient Breakdown ({last_day['Date']})")
        canvas2 = FigureCanvasTkAgg(fig2, frame2)
        canvas2.draw()
        canvas2.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # --- Weight Progress ---
        frame3 = ttk.Frame(notebook)
        notebook.add(frame3, text="Weight Progress")

        user_data = get_user_data_for_ml(self.conn, self.current_user_id)
        if user_data and "weight" in user_data:
            weights = [user_data["weight"]] * len(data)  # placeholder: replace with logs if tracked
            fig3, ax3 = plt.subplots(figsize=(6, 4))
            ax3.plot(data["Date"], weights, label="Weight", marker="o")
            if "goal_weight" in user_data:
                ax3.axhline(y=user_data["goal_weight"], color="green", linestyle="--", label="Goal Weight")
            ax3.set_title("Weight Progress")
            ax3.legend()
            canvas3 = FigureCanvasTkAgg(fig3, frame3)
            canvas3.draw()
            canvas3.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        else:
            ttk.Label(frame3, text="No weight data available").pack(pady=20)
            
        # --- Weekly Trends ---
        frame4 = ttk.Frame(notebook)
        notebook.add(frame4, text="Weekly Trends")

        # Keep only last 7 days
        weekly = data.tail(7)

        if not weekly.empty:
            fig4, ax4 = plt.subplots(figsize=(7, 4))

            # Plot calories
            ax4.bar(weekly["Date"], weekly["Calories"], color="#42A5F5", alpha=0.7, label="Calories")

            # Overlay protein, carbs, fat as lines
            ax4.plot(weekly["Date"], weekly["Protein"], marker="o", color="#66BB6A", label="Protein")
            ax4.plot(weekly["Date"], weekly["Carbs"], marker="s", color="#FFA726", label="Carbs")
            ax4.plot(weekly["Date"], weekly["Fat"], marker="^", color="#EF5350", label="Fat")

            ax4.set_title("Last 7 Days: Calories & Macronutrients")
            ax4.set_ylabel("Amount")
            ax4.legend()

            canvas4 = FigureCanvasTkAgg(fig4, frame4)
            canvas4.draw()
            canvas4.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        else:
            ttk.Label(frame4, text="No weekly data available").pack(pady=20)


    # ====================
    # RECOMMENDATIONS
    # ====================
    def show_recommendations(self):
        recs = []
        if self.current_user_id is None:
            messagebox.showerror("Error", "You must be logged in to view Recommendation.")
            return
        data = fetch_past_logs_for_plot(self.conn, self.current_user_id)

        if not data.empty:
            avg_cal = data["Calories"].mean()
            goal = predict_calorie_goal(self.conn, self.current_user_id)

            if avg_cal < goal * 0.9:
                recs.append("⚡ You're eating fewer calories than your goal. Consider adding nutrient-dense foods.")
            elif avg_cal > goal * 1.1:
                recs.append("⚠️ You're exceeding your calorie goal. Reduce high-sugar/high-fat foods.")
            else:
                recs.append("✅ You're close to your calorie goal. Keep it up!")

            avg_protein = data["Protein"].mean()
            if avg_protein < 50:
                recs.append("🍗 Increase your protein intake with foods like eggs, beans, chicken, or tofu.")

            avg_fiber = data["Carbs"].mean()  # assuming part of carbs includes fiber
            if avg_fiber < 25:
                recs.append("🥦 Add more fiber: vegetables, oats, legumes, fruits.")

        else:
            recs.append("No data yet. Start logging your meals to get recommendations!")

        win = tk.Toplevel(self.root)
        win.title("Recommendations")
        win.geometry("600x400")
        win.configure(bg=COLORS['background'])

        text = scrolledtext.ScrolledText(win, wrap=tk.WORD, width=70, height=25)
        text.pack(fill=tk.BOTH, expand=True)

        for r in recs:
            text.insert(tk.END, f"• {r}\n\n")

        text.config(state=tk.DISABLED)

    def show_all_users_window(self):
        from db import get_all_users, set_admin_status, reset_user_password, delete_user
    
        users = get_all_users(self.conn)
        win = tk.Toplevel(self.root)
        win.title("All Users (Admin Panel)")
        win.geometry("1000x500")
        win.configure(bg=COLORS['background'])
    
        ttk.Label(win, text="Registered Users", style='Title.TLabel').pack(pady=20)
    
        if not users:
            ttk.Label(win, text="No users found.").pack(pady=50)
            return
    
        frame = ttk.Frame(win)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
    
        cols = ("ID", "Username", "Age", "Gender", "Height", "Weight", "Goal Weight",
                "Activity Level", "Weight Goal", "Is Admin")
        tree = ttk.Treeview(frame, columns=cols, show="headings", selectmode="browse")
    
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=90, anchor=tk.CENTER)
    
        for user in users:
            tree.insert("", tk.END, values=user)
    
        tree.pack(fill=tk.BOTH, expand=True)
    
        # --- Admin Buttons ---
        btn_frame = ttk.Frame(win)
        btn_frame.pack(pady=15)
    
        def get_selected_user():
            sel = tree.selection()
            if not sel:
                messagebox.showwarning("Warning", "Select a user first")
                return None
            return tree.item(sel[0])["values"]
    
        def promote_demote():
            user = get_selected_user()
            if not user:
                return
            user_id, username, *_, is_admin = user
            new_status = not bool(is_admin)
            set_admin_status(self.conn, user_id, new_status)
            messagebox.showinfo("Success", f"User {username} is now {'Admin' if new_status else 'Normal'}")
            win.destroy()
            self.show_all_users_window()
    
        def reset_password():
            user = get_selected_user()
            if not user:
                return
            user_id, username, *_ = user
            new_pw = simpledialog.askstring("Reset Password", f"Enter new password for {username}:")
            if new_pw:
                reset_user_password(self.conn, user_id, new_pw)
                messagebox.showinfo("Success", f"Password reset for {username}")
    
        def delete_selected():
            user = get_selected_user()
            if not user:
                return
            user_id, username, *_ = user
            if messagebox.askyesno("Confirm Delete", f"Delete user {username} and all logs?"):
                delete_user(self.conn, user_id)
                messagebox.showinfo("Deleted", f"User {username} removed")
                win.destroy()
                self.show_all_users_window()
    
        ttk.Button(btn_frame, text="Promote/Demote", command=promote_demote, style='Modern.TButton').pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Reset Password", command=reset_password, style='Modern.TButton').pack(side=tk.LEFT, padx=10)
        ttk.Button(btn_frame, text="Delete User", command=delete_selected, style='Modern.TButton').pack(side=tk.LEFT, padx=10)
    

