import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
from tkcalendar import DateEntry
from database import connect_db, add_transaction, get_all_transactions, get_summary, delete_transaction, \
    get_monthly_summary
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from datetime import datetime
import csv

connect_db()


class SafeDateEntry(DateEntry):
    def _on_focus_out_cal(self, event):
        try:
            if self.focus_get() is not None:
                self._top_cal.withdraw()
        except KeyError:
            pass


class ExpenseTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Expense Tracker")
        self.root.geometry("1200x650")

        self.style = ttk.Style()
        self.categories = ["Food", "Transport", "Bills", "Entertainment", "Salary", "Shopping", "Health", "Other"]

        self.login_screen()

    def login_screen(self):
        password = simpledialog.askstring("Login", "Enter password:", show='*')
        if password != "admin":
            messagebox.showerror("Access Denied", "Incorrect password")
            self.root.destroy()
        else:
            self.setup_ui()
            self.refresh_table()

    def setup_ui(self):
        filter_frame = ttk.LabelFrame(self.root, text="Filter")
        filter_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(filter_frame, text="Month:").grid(row=0, column=0, padx=5, pady=5)
        self.month_combo = ttk.Combobox(filter_frame, values=["All"] + [f"{i:02d}" for i in range(1, 13)], width=5,
                                        state="readonly")
        self.month_combo.grid(row=0, column=1, padx=5, pady=5)
        self.month_combo.set("All")

        self.year_combo = ttk.Combobox(filter_frame,
                                       values=["All"] + [str(y) for y in range(2020, datetime.now().year + 1)], width=6,
                                       state="readonly")
        self.year_combo.grid(row=0, column=3, padx=5, pady=5)
        self.year_combo.set("All")

        ttk.Label(filter_frame, text="Category:").grid(row=0, column=4, padx=5, pady=5)
        self.filter_category_combo = ttk.Combobox(filter_frame, values=["All"] + self.categories, state="readonly")
        self.filter_category_combo.grid(row=0, column=5, padx=5, pady=5)
        self.filter_category_combo.set("All")

        ttk.Button(filter_frame, text="Apply Filter", command=self.apply_filter).grid(row=0, column=6, padx=5, pady=5)

        input_frame = ttk.LabelFrame(self.root, text="Add Transaction")
        input_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(input_frame, text="Date:").grid(row=0, column=0, padx=5, pady=5)
        self.date_entry = SafeDateEntry(input_frame)
        self.date_entry.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(input_frame, text="Category:").grid(row=0, column=2, padx=5, pady=5)
        self.category_entry = ttk.Combobox(input_frame, values=self.categories, state="readonly")
        self.category_entry.grid(row=0, column=3, padx=5, pady=5)
        self.category_entry.set("Food")

        ttk.Label(input_frame, text="Amount:").grid(row=0, column=4, padx=5, pady=5)
        self.amount_entry = ttk.Entry(input_frame)
        self.amount_entry.grid(row=0, column=5, padx=5, pady=5)

        ttk.Label(input_frame, text="Type:").grid(row=0, column=6, padx=5, pady=5)
        self.type_combo = ttk.Combobox(input_frame, values=["Income", "Expense"], state="readonly")
        self.type_combo.grid(row=0, column=7, padx=5, pady=5)
        self.type_combo.set("Expense")
        self.type_combo.bind("<<ComboboxSelected>>", self.on_type_change)

        ttk.Button(input_frame, text="Add", command=self.add_transaction).grid(row=0, column=8, padx=5, pady=5)

        self.tree = ttk.Treeview(self.root, columns=("ID", "Date", "Category", "Amount", "Type"), show="headings")
        for col in self.tree["columns"]:
            self.tree.heading(col, text=col)
            self.tree.column(col, anchor="center")
        self.tree.pack(fill="both", expand=True, padx=10, pady=10)

        ttk.Button(self.root, text="Remove Selected Transaction", command=self.remove_transaction).pack(pady=5)

        bottom_frame = ttk.Frame(self.root)
        bottom_frame.pack(fill="x", padx=10, pady=10)

        self.summary_label = ttk.Label(bottom_frame, text="Summary")
        self.summary_label.pack(side="left")

        ttk.Button(bottom_frame, text="Toggle Theme", command=self.toggle_theme).pack(side="right", padx=5)
        ttk.Button(bottom_frame, text="Export to CSV", command=self.export_to_csv).pack(side="right", padx=5)
        ttk.Button(bottom_frame, text="Pie Chart", command=self.show_pie_chart).pack(side="right", padx=5)
        ttk.Button(bottom_frame, text="Monthly Chart", command=self.show_monthly_chart).pack(side="right", padx=5)
        ttk.Button(bottom_frame, text="Bar Chart", command=self.show_bar_chart).pack(side="right", padx=5)
        ttk.Button(bottom_frame, text="Progress Bars", command=self.show_progress_bars).pack(side="right", padx=5)
        ttk.Button(bottom_frame, text="Income Waterfall", command=self.show_waterfall_chart).pack(side="right", padx=5)

    def add_transaction(self):
        try:
            raw_date = self.date_entry.get()
            parsed_date = datetime.strptime(raw_date, '%m/%d/%y')
            date = parsed_date.strftime('%Y-%m-%d')

            category = self.category_entry.get()
            amount = float(self.amount_entry.get())
            type_ = self.type_combo.get()

            if not category:
                raise ValueError("Category is required")

            add_transaction(date, category, amount, type_)

            self.category_entry.set("Food")
            self.amount_entry.delete(0, tk.END)

            self.refresh_table()
        except ValueError as e:
            messagebox.showerror("Error", str(e))

    def refresh_table(self):
        for row in self.tree.get_children():
            self.tree.delete(row)

        month = self.month_combo.get()
        year = self.year_combo.get()
        category = self.filter_category_combo.get()

        month = None if month == "All" else month
        year = None if year == "All" else year
        category = None if category == "All" else category

        transactions = get_all_transactions(month, year, category)

        for row in transactions:
            if len(row) == 5:
                self.tree.insert("", tk.END, values=row)

        summary = get_summary()
        summary_text = " | ".join(f"{t}: ${a:.2f}" for t, a in summary)
        self.summary_label.config(text=f"Summary: {summary_text}")

    def apply_filter(self):
        self.refresh_table()

    def remove_transaction(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showinfo("Remove", "No transaction selected.")
            return
        for item in selected:
            item_id = self.tree.item(item)['values'][0]
            delete_transaction(item_id)
        self.refresh_table()

    def show_bar_chart(self):
        transactions = get_all_transactions()
        expense_data = [t for t in transactions if t[4] == "Expense"]

        if not expense_data:
            messagebox.showinfo("Bar Chart", "No expense data to display.")
            return

        category_totals = {}
        for _, _, category, amount, _ in expense_data:
            category_totals[category] = category_totals.get(category, 0) + amount

        categories = list(category_totals.keys())
        values = list(category_totals.values())

        fig, ax = plt.subplots(figsize=(10, 6))
        bars = ax.bar(categories, values, color=plt.cm.Pastel1.colors)

        ax.set_title("Expenses by Category")
        ax.set_ylabel("Amount")
        ax.set_xlabel("Category")
        ax.grid(axis="y", linestyle="--", alpha=0.7)
        plt.xticks(rotation=45)

        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, height + max(values) * 0.01,
                    f"${height:.2f}", ha='center', va='bottom', fontsize=9)

        win = tk.Toplevel(self.root)
        win.title("Category-wise Expenses")

        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack()

    def show_progress_bars(self):
        category_budgets = {
            "Food": 300, "Transport": 150, "Bills": 200, "Entertainment": 100,
            "Salary": 0, "Shopping": 250, "Health": 100, "Other": 100
        }

        transactions = get_all_transactions()
        expenses = [t for t in transactions if t[4] == "Expense"]

        spent = {}
        for _, _, category, amount, _ in expenses:
            spent[category] = spent.get(category, 0) + amount

        win = tk.Toplevel(self.root)
        win.title("Budget Progress Bars")

        for category, budget in category_budgets.items():
            amount_spent = spent.get(category, 0)
            percent = min(int((amount_spent / budget) * 100), 100) if budget else 0

            label = ttk.Label(win, text=f"{category}: ${amount_spent:.2f} / ${budget} ({percent}%)")
            label.pack(anchor="w", padx=10)

            progress = ttk.Progressbar(win, length=300, value=percent)
            progress.pack(padx=10, pady=5)

    def show_waterfall_chart(self):
        summary = get_summary()
        income = sum(amount for t, amount in summary if t == "Income")
        expense = sum(amount for t, amount in summary if t == "Expense")
        net = income - expense

        steps = ["Income", "Expense", "Net"]
        values = [income, -expense, net]
        colors = ["green", "red", "blue"]

        cum_values = [0]
        for val in values[:-1]:
            cum_values.append(cum_values[-1] + val)

        fig, ax = plt.subplots(figsize=(8, 5))
        ax.bar(steps, values, bottom=cum_values, color=colors)
        ax.axhline(0, color="black", linewidth=0.8)
        ax.set_title("Income Statement Waterfall")
        ax.set_ylabel("Amount")
        ax.grid(axis="y", linestyle="--", alpha=0.6)

        for i, val in enumerate(values):
            ax.text(i, cum_values[i] + val / 2, f"${val:.2f}", ha="center", va="center", color="white", fontsize=10)

        win = tk.Toplevel(self.root)
        win.title("Income Waterfall Chart")

        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack()

    def show_pie_chart(self):
        transactions = get_all_transactions()
        expense_data = [t for t in transactions if t[4] == "Expense"]

        if not expense_data:
            messagebox.showinfo("Pie Chart", "No expense data to display.")
            return

        category_totals = {}
        for _, _, category, amount, _ in expense_data:
            category_totals[category] = category_totals.get(category, 0) + amount

        labels = list(category_totals.keys())
        sizes = list(category_totals.values())
        colors = plt.cm.Set3.colors

        def make_autopct(sizes):
            def autopct(pct):
                total = sum(sizes)
                val = int(round(pct * total / 100.0))
                return f"{pct:.1f}%\n(${val})"

            return autopct

        fig, ax = plt.subplots()
        wedges, texts, autotexts = ax.pie(
            sizes, labels=labels, autopct=make_autopct(sizes), startangle=140, colors=colors
        )
        ax.axis("equal")
        ax.set_title("Expenses by Category")

        win = tk.Toplevel(self.root)
        win.title("Expense Pie Chart")

        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack()

    def show_monthly_chart(self):
        monthly_data = get_monthly_summary()
        if not monthly_data:
            messagebox.showinfo("Monthly Chart", "No data available.")
            return

        months = [m for m, _, _ in monthly_data]
        income = [i for _, i, _ in monthly_data]
        expense = [e for _, _, e in monthly_data]

        fig, ax = plt.subplots(figsize=(12, 6))

        x = range(len(months))
        width = 0.35

        income_bars = ax.bar([p - width / 2 for p in x], income, width=width, label="Income", color="green")
        expense_bars = ax.bar([p + width / 2 for p in x], expense, width=width, label="Expense", color="red")

        ax.set_xticks(x)
        ax.set_xticklabels(months, rotation=45, ha="right")
        ax.set_title("Monthly Income and Expenses")
        ax.set_xlabel("Month")
        ax.set_ylabel("Amount")
        ax.legend()
        ax.grid(axis="y", linestyle="--", alpha=0.7)

        for bar in income_bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, height + max(income) * 0.01,
                    f"${height:.2f}", ha='center', va='bottom', fontsize=8)

        for bar in expense_bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width() / 2, height + max(expense) * 0.01,
                    f"${height:.2f}", ha='center', va='bottom', fontsize=8)

        win = tk.Toplevel(self.root)
        win.title("Monthly Summary")

        canvas = FigureCanvasTkAgg(fig, master=win)
        canvas.draw()
        canvas.get_tk_widget().pack()

    def export_to_csv(self):
        transactions = get_all_transactions()
        if not transactions:
            messagebox.showinfo("Export", "No transactions to export.")
            return

        file = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[["CSV files", "*.csv"]])
        if file:
            with open(file, mode="w", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["ID", "Date", "Category", "Amount", "Type"])
                writer.writerows(transactions)
            messagebox.showinfo("Export", f"Transactions exported to {file}")

    def toggle_theme(self):
        current = self.style.theme_use()
        new_theme = "clam" if current == "default" else "default"
        self.style.theme_use(new_theme)

    def on_type_change(self, event):
        if self.type_combo.get() == "Income":
            self.category_entry.set("Salary")
        else:
            self.category_entry.set("Food")


if __name__ == "__main__":
    root = tk.Tk()
    app = ExpenseTracker(root)
    root.mainloop()