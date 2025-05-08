from flask import Flask, render_template, request, redirect
import sqlite3
from datetime import datetime, timedelta

app = Flask(__name__)

# DB 초기화
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS schedule 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                  week TEXT, 
                  day TEXT, 
                  category TEXT,
                  content TEXT,
                  date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    conn.commit()
    conn.close()

init_db()

# 주차 리스트 생성 함수 (오늘 포함 + 이후 4주)
def generate_weeks():
    today = datetime.now()
    weeks = []
    for i in range(5):
        target_date = today + timedelta(weeks=i)
        month = target_date.month
        week_num = (target_date.day - 1) // 7 + 1
        weeks.append(f"{month}월 {week_num}주")
    return weeks

# 요일 + 날짜 리스트 생성
def generate_days_with_date():
    today = datetime.now()
    days_kor = ["월", "화", "수", "목", "금"]
    days = []

    for i, d in enumerate(days_kor):
        target_date = today + timedelta(days=(i - today.weekday() + 0 if today.weekday() <= i else 7 + i - today.weekday()))
        days.append(f"{d} ({target_date.month}/{target_date.day})")
    
    return days, days_kor  # 표시용, DB용

# 선생님 입력
@app.route('/teacher', methods=['GET', 'POST'])
def teacher():
    weeks = generate_weeks()
    display_days, db_days = generate_days_with_date()

    if request.method == 'POST':
        week = request.form['week']
        conn = sqlite3.connect('database.db')
        c = conn.cursor()

        for day in db_days:
            homework = request.form.get(f"{day}_homework", "").strip()
            material = request.form.get(f"{day}_material", "").strip()

            if homework:
                c.execute("INSERT INTO schedule (week, day, category, content) VALUES (?, ?, ?, ?)", 
                          (week, day, "숙제", homework))

            if material:
                c.execute("INSERT INTO schedule (week, day, category, content) VALUES (?, ?, ?, ?)", 
                          (week, day, "준비물", material))

        conn.commit()
        conn.close()
        return redirect('/teacher')

    return render_template('teacher_write_table.html', weeks=weeks, display_days=display_days, db_days=db_days)

# 학부모 페이지
@app.route('/')
def parent():
    weeks = generate_weeks()
    selected_week = request.args.get('week', weeks[0])

    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT day, category, content FROM schedule WHERE week = ? ORDER BY day", (selected_week,))
    items = c.fetchall()
    conn.close()

    data = {}
    for day, category, content in items:
        if day not in data:
            data[day] = {"숙제": [], "준비물": []}
        data[day][category].append(content)

    return render_template('parent_view.html', week=selected_week, weeks=weeks, data=data)

if __name__ == '__main__':
    app.run(debug=True)
