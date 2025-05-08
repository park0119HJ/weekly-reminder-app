from flask import Flask, render_template, request, redirect
import datetime
import sqlite3

app = Flask(__name__)

days_kor = ['월', '화', '수', '목', '금']

def get_week_info(target_date=None):
    if target_date is None:
        target_date = datetime.date.today()
    year = target_date.year
    month = target_date.month
    day = target_date.day

    first_day_of_month = datetime.date(year, month, 1)
    first_weekday = first_day_of_month.weekday()

    if first_weekday < 3:
        prev_month = month - 1 if month > 1 else 12
        prev_year = year if month > 1 else year - 1
        return f"{prev_year}-{str(prev_month).zfill(2)}-last"
    else:
        week_number = (day + first_weekday - 1) // 7 + 1
        return f"{year}-{str(month).zfill(2)}-{week_number}"

def get_week_dates(year, month, week_num):
    first_day = datetime.date(year, month, 1)
    first_day_weekday = first_day.weekday()

    if first_day_weekday == 0:
        first_monday = first_day
    else:
        first_monday = first_day + datetime.timedelta(days=(7 - first_day_weekday))

    target_monday = first_monday + datetime.timedelta(weeks=week_num - 1)
    return [(target_monday + datetime.timedelta(days=i)) for i in range(5)]

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS schedule (
        week TEXT,
        day TEXT,
        date TEXT,
        category TEXT,
        content TEXT,
        status TEXT
    )''')
    conn.commit()
    conn.close()

@app.route("/")
def parent_view():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM schedule WHERE status='published' ORDER BY week, day")
    rows = c.fetchall()
    conn.close()
    return render_template("parent_view.html", rows=rows)

@app.route("/teacher", methods=["GET", "POST"])
def teacher():
    init_db()
    now = datetime.date.today()
    year = now.year
    month = now.month

    first_day = datetime.date(year, month, 1)
    first_weekday = first_day.weekday()
    current_week = (now.day + first_weekday - 1) // 7 + 1

    weeks = [f"{year}-{str(month).zfill(2)}-{i}" for i in range(1, 6)]

    selected_week = request.args.get("week") or get_week_info()

    if request.method == "POST":
        week = request.form.get("week")
        status = request.form.get("status")
        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        # 기존 데이터 삭제
        c.execute("DELETE FROM schedule WHERE week=?", (week,))

        # 데이터 삽입
        for idx, day in enumerate(days_kor):
            date = request.form.get(f"date_{day}")
            homework = request.form.get(f"homework_{day}")
            prepare = request.form.get(f"prepare_{day}")

            c.execute("INSERT INTO schedule VALUES (?, ?, ?, ?, ?, ?)", (week, day, date, '숙제', homework, status))
            c.execute("INSERT INTO schedule VALUES (?, ?, ?, ?, ?, ?)", (week, day, date, '준비물', prepare, status))

        conn.commit()
        conn.close()
        return redirect(f"/teacher?week={week}")

    # 불러오기
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM schedule WHERE week=?", (selected_week,))
    rows = c.fetchall()
    conn.close()

    dates = []
    if "last" not in selected_week:
        y, m, w = map(int, selected_week.split("-"))
        dates = get_week_dates(y, m, w)

    return render_template("teacher_write.html", weeks=weeks, selected_week=selected_week, dates=dates, rows=rows)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
