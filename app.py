from flask import Flask, render_template, request, redirect
import datetime
import sqlite3

app = Flask(__name__)

def get_week_info(target_date=None):
    if target_date is None:
        target_date = datetime.date.today()
    year = target_date.year
    month = target_date.month
    day = target_date.day

    first_day_of_month = datetime.date(year, month, 1)
    first_weekday = first_day_of_month.weekday()  # 월:0 ~ 일:6

    if first_weekday < 3:
        prev_month = month - 1 if month > 1 else 12
        prev_year = year if month > 1 else year - 1
        return f"{prev_year}년 {prev_month}월 마지막주"
    else:
        week_number = (day + first_weekday - 1) // 7 + 1
        return f"{year}년 {month}월 {week_number}주"

def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS schedule (week TEXT, category TEXT, mon TEXT, tue TEXT, wed TEXT, thu TEXT, fri TEXT)''')
    conn.commit()
    conn.close()

@app.route("/")
def parent_view():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM schedule ORDER BY ROWID DESC LIMIT 2")
    rows = c.fetchall()
    conn.close()
    return render_template("parent_view.html", rows=rows)

@app.route("/teacher", methods=["GET", "POST"])
def teacher():
    init_db()
    weeks = [get_week_info()]

    if request.method == "POST":
        week = request.form.get("week")
        homework = {
            'mon': request.form.get("homework_mon"),
            'tue': request.form.get("homework_tue"),
            'wed': request.form.get("homework_wed"),
            'thu': request.form.get("homework_thu"),
            'fri': request.form.get("homework_fri"),
        }
        prepare = {
            'mon': request.form.get("prepare_mon"),
            'tue': request.form.get("prepare_tue"),
            'wed': request.form.get("prepare_wed"),
            'thu': request.form.get("prepare_thu"),
            'fri': request.form.get("prepare_fri"),
        }

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("DELETE FROM schedule")
        c.execute("INSERT INTO schedule VALUES (?, ?, ?, ?, ?, ?, ?)", (week, '숙제', homework['mon'], homework['tue'], homework['wed'], homework['thu'], homework['fri']))
        c.execute("INSERT INTO schedule VALUES (?, ?, ?, ?, ?, ?, ?)", (week, '준비물', prepare['mon'], prepare['tue'], prepare['wed'], prepare['thu'], prepare['fri']))
        conn.commit()
        conn.close()

        return redirect("/teacher")

    return render_template("teacher_write.html", weeks=weeks)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)