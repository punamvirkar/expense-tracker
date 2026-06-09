from flask import Flask, render_template, request, redirect, session
import sqlite3
from datetime import datetime
def month_name(m):
    if not m:
        return "Unknown"
    return datetime.strptime(m, "%Y-%m").strftime("%B %Y")

app = Flask(__name__)
app.secret_key = "secret123"

# DB connect
def get_db():
    conn = sqlite3.connect("expenses.db")

    conn.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY,
            title TEXT,
            amount INTEGER,
            date TEXT
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            username TEXT UNIQUE,
            password TEXT
        )
    """)

    return conn

# Home
@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM expenses")
    data = cursor.fetchall()

    cursor.execute("SELECT SUM(amount) FROM expenses")
    total = cursor.fetchone()[0]

    if total is None:
        total = 0

    conn.close()
    return render_template("index.html", expenses=data, total=total)


# Add expense
@app.route('/add', methods=['POST'])
def add():
    title = request.form.get('title')
    amount = request.form.get('amount')
    date = request.form.get('date')  # SAFE

    conn = get_db()
    conn.execute(
        "INSERT INTO expenses (title, amount, date) VALUES (?, ?, ?)",
        (title, amount, date)
    )
    conn.commit()
    conn.close()

    return redirect('/')
# Delete
@app.route('/delete/<int:id>')
def delete(id):
    conn = get_db()
    conn.execute("DELETE FROM expenses WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect('/')


# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db()
        conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()

        return redirect('/login')

    return render_template("register.html")


# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        ).fetchone()
        conn.close()

        if user:
            session['user_id'] = user[0]
            return redirect('/')
        else:
            return "Invalid login"

    return render_template("login.html")


# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


# Report
@app.route('/report')
def report():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT date, SUM(amount)
        FROM expenses
        GROUP BY date
        ORDER BY date
    """)

    rows = cursor.fetchall()
    conn.close()

    labels = [r[0] for r in rows if r[0] is not None]
    values = [r[1] for r in rows]

    return render_template("report.html", labels=labels, values=values)
if __name__ == "__main__":
    app.run(debug=True)