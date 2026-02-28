import csv
import sqlite3
from datetime import datetime, date
from pathlib import Path
import tkinter as tk
from tkinter import ttk, messagebox, filedialog


BASE_DIR = Path(__file__).resolve().parent
DB_PATH = str(BASE_DIR / "activities.db")


def parse_duration_to_minutes(value: str) -> float:
    value = value.strip()
    parts = value.split(":")

    if len(parts) == 1:
        return float(parts[0])
    if len(parts) == 2:
        hours, minutes = parts
        return int(hours) * 60 + int(minutes)
    if len(parts) == 3:
        hours, minutes, seconds = parts
        return int(hours) * 60 + int(minutes) + int(seconds) / 60

    raise ValueError("Invalid duration format")


def parse_pace_to_min_per_km(value: str) -> float:
    value = value.strip()
    parts = value.split(":")

    if len(parts) == 1:
        return float(parts[0])
    if len(parts) == 2:
        minutes, seconds = parts
        return int(minutes) + int(seconds) / 60

    raise ValueError("Invalid pace format")


def format_minutes_to_hhmm(minutes_total: float) -> str:
    hours = int(minutes_total // 60)
    minutes = int(round(minutes_total % 60))
    return f"{hours:02d}:{minutes:02d}"


def validate_date(value: str) -> None:
    datetime.strptime(value, "%Y-%m-%d")


def create_db_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    return sqlite3.connect(db_path)


def create_activities_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            activity_date TEXT NOT NULL,
            activity_type TEXT NOT NULL,
            distance_km REAL NOT NULL,
            avg_metric_value REAL NOT NULL,
            avg_metric_unit TEXT NOT NULL,
            total_minutes REAL NOT NULL,
            calories INTEGER NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    conn.commit()


def build_activities_query(
    activity_filter: str = "all",
    from_date: str = "",
    to_date: str = "",
    min_dist: str = "",
    max_dist: str = "",
) -> tuple[str, list]:
    query = """
        SELECT id, activity_date, activity_type, distance_km, avg_metric_value,
               avg_metric_unit, total_minutes, calories
        FROM activities
        WHERE 1=1
    """
    params = []

    activity_filter = activity_filter.strip().lower()
    if activity_filter and activity_filter != "all":
        query += " AND activity_type = ?"
        params.append(activity_filter)

    from_date = from_date.strip()
    if from_date:
        validate_date(from_date)
        query += " AND activity_date >= ?"
        params.append(from_date)

    to_date = to_date.strip()
    if to_date:
        validate_date(to_date)
        query += " AND activity_date <= ?"
        params.append(to_date)

    min_dist = str(min_dist).strip()
    if min_dist:
        query += " AND distance_km >= ?"
        params.append(float(min_dist))

    max_dist = str(max_dist).strip()
    if max_dist:
        query += " AND distance_km <= ?"
        params.append(float(max_dist))

    query += " ORDER BY activity_date DESC, id DESC"
    return query, params


def insert_activity_record(
    conn: sqlite3.Connection,
    activity_date: str,
    activity_type: str,
    distance_km: float,
    avg_metric_value: float,
    avg_metric_unit: str,
    total_minutes: float,
    calories: int,
    created_at: str | None = None,
) -> None:
    conn.execute(
        """
        INSERT INTO activities (
            activity_date,
            activity_type,
            distance_km,
            avg_metric_value,
            avg_metric_unit,
            total_minutes,
            calories,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            activity_date,
            activity_type,
            distance_km,
            avg_metric_value,
            avg_metric_unit,
            total_minutes,
            calories,
            created_at or datetime.now().isoformat(timespec="seconds"),
        ),
    )
    conn.commit()


def fetch_activities(
    conn: sqlite3.Connection,
    activity_filter: str = "all",
    from_date: str = "",
    to_date: str = "",
    min_dist: str = "",
    max_dist: str = "",
):
    query, params = build_activities_query(activity_filter, from_date, to_date, min_dist, max_dist)
    return conn.execute(query, params).fetchall()


class ActivityMonitorApp:
    ACTIVITIES = ["cycling", "hiking", "walking"]

    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("Sport Activity Monitor")
        self.root.geometry("1180x760")

        self.conn = create_db_connection(DB_PATH)
        self.create_table()

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=8)

        self.status_var = tk.StringVar(value="")
        self.status_label = ttk.Label(self.root, textvariable=self.status_var, foreground="#444")
        self.status_label.pack(fill="x", padx=10, pady=(0, 8), anchor="w")

        self.add_tab = ttk.Frame(self.notebook)
        self.browse_tab = ttk.Frame(self.notebook)

        self.notebook.add(self.add_tab, text="Add activity")
        self.notebook.add(self.browse_tab, text="Browse stats")

        self.build_add_tab()
        self.build_browse_tab()
        self.refresh_table()
        self.update_status_bar()

    def create_table(self) -> None:
        create_activities_table(self.conn)

    def build_add_tab(self) -> None:
        form = ttk.LabelFrame(self.add_tab, text="New activity")
        form.pack(fill="x", padx=12, pady=12)

        self.activity_var = tk.StringVar(value=self.ACTIVITIES[0])
        self.date_var = tk.StringVar(value=date.today().isoformat())
        self.distance_var = tk.StringVar()
        self.avg_var = tk.StringVar()
        self.duration_var = tk.StringVar()
        self.calories_var = tk.StringVar()
        self.avg_label_var = tk.StringVar(value="Average speed (km/h)")
        self.avg_hint_var = tk.StringVar(value="Example: 25.5")

        fields = [
            ("Date (YYYY-MM-DD)", self.date_var),
            ("Activity", self.activity_var),
            ("Distance (km)", self.distance_var),
            ("", self.avg_var),
            ("Total time (hh:mm or hh:mm:ss)", self.duration_var),
            ("Calories", self.calories_var),
        ]

        for idx, (label_text, variable) in enumerate(fields):
            if idx == 3:
                ttk.Label(form, textvariable=self.avg_label_var).grid(row=idx, column=0, sticky="w", padx=10, pady=8)
                entry = ttk.Entry(form, textvariable=variable, width=28)
                entry.grid(row=idx, column=1, sticky="w", padx=10, pady=8)
                ttk.Label(form, textvariable=self.avg_hint_var).grid(row=idx, column=2, sticky="w", padx=10, pady=8)
                continue

            ttk.Label(form, text=label_text).grid(row=idx, column=0, sticky="w", padx=10, pady=8)

            if label_text == "Activity":
                activity_cb = ttk.Combobox(form, textvariable=variable, values=self.ACTIVITIES, state="readonly", width=25)
                activity_cb.grid(row=idx, column=1, sticky="w", padx=10, pady=8)
                activity_cb.bind("<<ComboboxSelected>>", self.on_activity_change)
            else:
                ttk.Entry(form, textvariable=variable, width=28).grid(row=idx, column=1, sticky="w", padx=10, pady=8)

            if label_text == "Distance (km)":
                ttk.Label(form, text="Example: 12.4").grid(row=idx, column=2, sticky="w", padx=10, pady=8)

        ttk.Button(form, text="Save activity", command=self.save_activity).grid(row=7, column=0, padx=10, pady=15, sticky="w")
        ttk.Button(form, text="Clear form", command=self.clear_form).grid(row=7, column=1, padx=10, pady=15, sticky="w")

        help_text = (
            "Distance example: 12.4 km.\n"
            "For cycling, use average speed in km/h.\n"
            "For hiking/walking, use pace in min/km (e.g. 9:30 or 9.5)."
        )
        ttk.Label(form, text=help_text, foreground="#555").grid(row=8, column=0, columnspan=3, sticky="w", padx=10, pady=(0, 10))

    def build_browse_tab(self) -> None:
        filters = ttk.LabelFrame(self.browse_tab, text="Filters")
        filters.pack(fill="x", padx=12, pady=8)

        self.filter_activity_var = tk.StringVar(value="all")
        self.filter_from_var = tk.StringVar()
        self.filter_to_var = tk.StringVar()
        self.filter_min_distance_var = tk.StringVar()
        self.filter_max_distance_var = tk.StringVar()

        ttk.Label(filters, text="Activity").grid(row=0, column=0, padx=8, pady=8, sticky="w")
        ttk.Combobox(
            filters,
            textvariable=self.filter_activity_var,
            values=["all", *self.ACTIVITIES],
            state="readonly",
            width=16,
        ).grid(row=0, column=1, padx=8, pady=8, sticky="w")

        ttk.Label(filters, text="From date (YYYY-MM-DD)").grid(row=0, column=2, padx=8, pady=8, sticky="w")
        ttk.Entry(filters, textvariable=self.filter_from_var, width=18).grid(row=0, column=3, padx=8, pady=8, sticky="w")

        ttk.Label(filters, text="To date (YYYY-MM-DD)").grid(row=0, column=4, padx=8, pady=8, sticky="w")
        ttk.Entry(filters, textvariable=self.filter_to_var, width=18).grid(row=0, column=5, padx=8, pady=8, sticky="w")

        ttk.Label(filters, text="Min distance (km)").grid(row=1, column=0, padx=8, pady=8, sticky="w")
        ttk.Entry(filters, textvariable=self.filter_min_distance_var, width=18).grid(row=1, column=1, padx=8, pady=8, sticky="w")

        ttk.Label(filters, text="Max distance (km)").grid(row=1, column=2, padx=8, pady=8, sticky="w")
        ttk.Entry(filters, textvariable=self.filter_max_distance_var, width=18).grid(row=1, column=3, padx=8, pady=8, sticky="w")

        ttk.Button(filters, text="Apply filters", command=self.refresh_table).grid(row=1, column=4, padx=8, pady=8, sticky="w")
        ttk.Button(filters, text="Reset", command=self.reset_filters).grid(row=1, column=5, padx=8, pady=8, sticky="w")

        table_frame = ttk.Frame(self.browse_tab)
        table_frame.pack(fill="both", expand=True, padx=12, pady=8)

        columns = (
            "id",
            "date",
            "activity",
            "distance",
            "avg",
            "duration",
            "calories",
        )
        self.tree = ttk.Treeview(table_frame, columns=columns, show="headings", height=20)

        self.tree.heading("id", text="ID")
        self.tree.heading("date", text="Date")
        self.tree.heading("activity", text="Activity")
        self.tree.heading("distance", text="Distance (km)")
        self.tree.heading("avg", text="Avg speed / pace")
        self.tree.heading("duration", text="Total time")
        self.tree.heading("calories", text="Calories")

        self.tree.column("id", width=60, anchor="center")
        self.tree.column("date", width=130, anchor="center")
        self.tree.column("activity", width=120, anchor="center")
        self.tree.column("distance", width=140, anchor="center")
        self.tree.column("avg", width=180, anchor="center")
        self.tree.column("duration", width=130, anchor="center")
        self.tree.column("calories", width=120, anchor="center")

        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=y_scroll.set)

        self.tree.pack(side="left", fill="both", expand=True)
        y_scroll.pack(side="right", fill="y")

        actions = ttk.Frame(self.browse_tab)
        actions.pack(fill="x", padx=12, pady=(0, 12))

        ttk.Button(actions, text="Delete selected", command=self.delete_selected).pack(side="left", padx=6)
        ttk.Button(actions, text="Export filtered to CSV", command=self.export_filtered_to_csv).pack(side="left", padx=6)
        ttk.Button(actions, text="Show charts", command=self.show_charts).pack(side="left", padx=6)

    def on_activity_change(self, _event=None) -> None:
        activity = self.activity_var.get()
        if activity == "cycling":
            self.avg_label_var.set("Average speed (km/h)")
            self.avg_hint_var.set("Example: 25.5")
        else:
            self.avg_label_var.set("Average pace (min/km)")
            self.avg_hint_var.set("Example: 8:30 or 8.5")

    def validate_date(self, value: str) -> None:
        validate_date(value)

    def save_activity(self) -> None:
        try:
            activity_date = self.date_var.get().strip()
            activity_type = self.activity_var.get().strip().lower()
            distance_km = float(self.distance_var.get().strip())
            total_minutes = parse_duration_to_minutes(self.duration_var.get())
            calories = int(float(self.calories_var.get().strip()))

            self.validate_date(activity_date)

            if activity_type not in self.ACTIVITIES:
                raise ValueError("Invalid activity")
            if distance_km <= 0:
                raise ValueError("Distance must be greater than 0")
            if total_minutes <= 0:
                raise ValueError("Duration must be greater than 0")
            if calories < 0:
                raise ValueError("Calories cannot be negative")

            avg_text = self.avg_var.get().strip()
            if activity_type == "cycling":
                avg_metric_value = float(avg_text)
                avg_metric_unit = "km/h"
                if avg_metric_value <= 0:
                    raise ValueError("Average speed must be greater than 0")
            else:
                avg_metric_value = parse_pace_to_min_per_km(avg_text)
                avg_metric_unit = "min/km"
                if avg_metric_value <= 0:
                    raise ValueError("Average pace must be greater than 0")

            insert_activity_record(
                self.conn,
                activity_date=activity_date,
                activity_type=activity_type,
                distance_km=distance_km,
                avg_metric_value=avg_metric_value,
                avg_metric_unit=avg_metric_unit,
                total_minutes=total_minutes,
                calories=calories,
            )

            messagebox.showinfo("Saved", "Activity has been saved.")
            self.clear_form()
            self.refresh_table()
            self.notebook.select(self.browse_tab)

        except ValueError as exc:
            messagebox.showerror("Validation error", str(exc))

    def clear_form(self) -> None:
        self.date_var.set(date.today().isoformat())
        self.activity_var.set(self.ACTIVITIES[0])
        self.distance_var.set("")
        self.avg_var.set("")
        self.duration_var.set("")
        self.calories_var.set("")
        self.on_activity_change()

    def build_query(self):
        return build_activities_query(
            activity_filter=self.filter_activity_var.get(),
            from_date=self.filter_from_var.get(),
            to_date=self.filter_to_var.get(),
            min_dist=self.filter_min_distance_var.get(),
            max_dist=self.filter_max_distance_var.get(),
        )

    def fetch_filtered_rows(self):
        query, params = self.build_query()
        return self.conn.execute(query, params).fetchall()

    def refresh_table(self) -> None:
        for item in self.tree.get_children():
            self.tree.delete(item)

        try:
            rows = self.fetch_filtered_rows()
        except ValueError as exc:
            messagebox.showerror("Filter error", str(exc))
            return

        for row in rows:
            row_id, activity_date, activity_type, distance_km, avg_value, avg_unit, total_minutes, calories = row
            avg_display = f"{avg_value:.2f} {avg_unit}"
            duration_display = format_minutes_to_hhmm(total_minutes)
            self.tree.insert(
                "",
                "end",
                values=(
                    row_id,
                    activity_date,
                    activity_type,
                    f"{distance_km:.2f}",
                    avg_display,
                    duration_display,
                    calories,
                ),
            )

        self.update_status_bar()

    def get_records_count(self) -> int:
        row = self.conn.execute("SELECT COUNT(*) FROM activities").fetchone()
        return int(row[0]) if row else 0

    def update_status_bar(self) -> None:
        count = self.get_records_count()
        label = "record" if count == 1 else "records"
        self.status_var.set(f"DB: {DB_PATH} | Total saved: {count} {label}")

    def reset_filters(self) -> None:
        self.filter_activity_var.set("all")
        self.filter_from_var.set("")
        self.filter_to_var.set("")
        self.filter_min_distance_var.set("")
        self.filter_max_distance_var.set("")
        self.refresh_table()

    def delete_selected(self) -> None:
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("No selection", "Select at least one row to delete.")
            return

        if not messagebox.askyesno("Confirm", "Delete selected activity entries?"):
            return

        ids_to_delete = []
        for item in selected:
            row = self.tree.item(item, "values")
            ids_to_delete.append(int(row[0]))

        self.conn.executemany("DELETE FROM activities WHERE id = ?", [(x,) for x in ids_to_delete])
        self.conn.commit()
        self.refresh_table()

    def export_filtered_to_csv(self) -> None:
        rows = self.fetch_filtered_rows()
        if not rows:
            messagebox.showinfo("No data", "There is no data for current filters.")
            return

        target_path = filedialog.asksaveasfilename(
            title="Save CSV",
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv")],
            initialfile="activities_export.csv",
        )
        if not target_path:
            return

        with open(target_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(
                [
                    "id",
                    "activity_date",
                    "activity_type",
                    "distance_km",
                    "avg_metric_value",
                    "avg_metric_unit",
                    "total_minutes",
                    "calories",
                ]
            )
            writer.writerows(rows)

        messagebox.showinfo("Exported", f"CSV exported to:\n{target_path}")

    def show_charts(self) -> None:
        rows = self.fetch_filtered_rows()
        if not rows:
            messagebox.showinfo("No data", "There is no data for current filters.")
            return

        try:
            import matplotlib.pyplot as plt
            from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        except ImportError:
            messagebox.showerror(
                "Missing dependency",
                "matplotlib is required for charts. Install it with: pip install matplotlib",
            )
            return

        by_activity_distance = {name: 0.0 for name in self.ACTIVITIES}
        by_activity_calories = {name: 0 for name in self.ACTIVITIES}
        by_month_distance = {}

        for row in rows:
            _, activity_date, activity_type, distance_km, _, _, _, calories = row
            by_activity_distance[activity_type] += distance_km
            by_activity_calories[activity_type] += calories

            month_key = activity_date[:7]
            by_month_distance[month_key] = by_month_distance.get(month_key, 0.0) + distance_km

        chart_window = tk.Toplevel(self.root)
        chart_window.title("Activity charts")
        chart_window.geometry("1050x700")

        fig = plt.Figure(figsize=(10, 6), dpi=100)
        ax1 = fig.add_subplot(121)
        ax2 = fig.add_subplot(222)
        ax3 = fig.add_subplot(224)

        activities = list(by_activity_distance.keys())
        distances = [by_activity_distance[k] for k in activities]
        calories = [by_activity_calories[k] for k in activities]

        ax1.bar(activities, distances, color=["#4e79a7", "#59a14f", "#f28e2b"])
        ax1.set_title("Distance by activity")
        ax1.set_ylabel("Kilometers")

        ax2.bar(activities, calories, color=["#76b7b2", "#edc949", "#af7aa1"])
        ax2.set_title("Calories by activity")
        ax2.set_ylabel("kcal")

        months = sorted(by_month_distance.keys())
        month_values = [by_month_distance[m] for m in months]
        ax3.plot(months, month_values, marker="o", color="#e15759")
        ax3.set_title("Distance trend by month")
        ax3.set_ylabel("Kilometers")
        ax3.tick_params(axis="x", rotation=45)

        fig.tight_layout()

        canvas = FigureCanvasTkAgg(fig, master=chart_window)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def close(self) -> None:
        self.conn.close()


def main() -> None:
    root = tk.Tk()
    app = ActivityMonitorApp(root)
    root.protocol("WM_DELETE_WINDOW", lambda: (app.close(), root.destroy()))
    root.mainloop()


if __name__ == "__main__":
    main()
