from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime, timedelta
import calendar

app = Flask(__name__)

def get_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()

    # 반 테이블 생성
    c.execute("""
    CREATE TABLE IF NOT EXISTS classes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT
    )
    """)

    # 주간 학습안내 테이블 생성
    c.execute("""
    CREATE TABLE IF NOT EXISTS weekly_schedule (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        class_id INTEGER,
        week TEXT,
        day TEXT,
        date TEXT,
        type TEXT,
        content TEXT,
        status TEXT
    )
    """)

    # 반 데이터가 없으면 자동 추가
    c.execute("SELECT COUNT(*) FROM classes")
    if c.fetchone()[0] == 0:
        classes = ['이삭반', '요엘반', '요셉반', '다니엘반', '여호수아반']
        for class_name in classes:
            c.execute("INSERT INTO classes (name) VALUES (?)", (class_name,))
    conn.commit()
    conn.close()

def get_classes():
    init_db()
    conn = get_connection()
    classes = conn.execute("SELECT * FROM classes").fetchall()
    conn.close()
    return classes

def get_weeks():
    now = datetime.now()
    weeks = []
    first = datetime(now.year, now.month, 1)

    for i in range(6):
        week_start = first + timedelta(days=i * 7)
        if week_start.month != now.month:
            continue
        week_number = calendar.monthcalendar(week_start.year, week_start.month)[i]
        if week_number[3] != 0:
            week_label = f"{week_start.month}월 {i + 1}주"
        else:
            week_label = f"{week_start.month-1}월 마지막주"
        weeks.append(week_label)
    return weeks

def get_dates(week_label):
    year = datetime.now().year
    month, week_num = map(int, week_label.replace("월", "").replace("주", "").split())
    cal = calendar.monthcalendar(year, month)

    if "마지막" in week_label:
        target_week = cal[-1]
    else:
        target_week = cal[week_num - 1]

    dates = []
    for day in target_week[0:5]:
        if day == 0:
            dates.append("")
        else:
            dates.append(datetime(year, month, day))
    return dates

@app.route("/teacher", methods=["GET", "POST"])
def teacher():
    classes = get_classes()
    class_id = request.args.get("class_id")
    if not class_id:
        return render_template("select_class.html", classes=classes)

    week = request.args.get("week") or get_weeks()[0]

    if request.method == "POST":
        conn = get_connection()
        conn.execute("DELETE FROM weekly_schedule WHERE class_id = ? AND week = ?", (class_id, week))

        for i, day in enumerate(["월", "화", "수", "목", "금"]):
            conn.execute("INSERT INTO weekly_schedule (class_id, week, day, date, type, content, status) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                         (class_id, week, day, request.form.get(f"date_{day}"), "숙제", request.form.get(f"homework_{day}"), request.form.get("status")))
            conn.execute("INSERT INTO weekly_schedule (class_id, week, day, date, type, content, status) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                         (class_id, week, day, request.form.get(f"date_{day}"), "준비물", request.form.get(f"prepare_{day}"), request.form.get("status")))
        conn.commit()
        conn.close()
        return redirect(f"/teacher?class_id={class_id}&week={week}")

    conn = get_connection()
    rows = conn.execute("SELECT * FROM weekly_schedule WHERE class_id = ? AND week = ?", (class_id, week)).fetchall()
    conn.close()

    dates = get_dates(week)

    return render_template("teacher_write_table.html", classes=classes, class_id=class_id, weeks=get_weeks(), selected_week=week, dates=dates, rows=rows)

@app.route("/", methods=["GET"])
def parent():
    classes = get_classes()
    class_id = request.args.get("class_id")
    if not class_id:
        return render_template("select_class.html", classes=classes)

    conn = get_connection()
    rows = conn.execute("SELECT * FROM weekly_schedule WHERE class_id = ? AND status = 'published'", (class_id,)).fetchall()
    conn.close()

    return render_template("parent_view.html", rows=rows, classes=classes, class_id=class_id)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
