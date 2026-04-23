import sqlite3
import os
import random
from datetime import date
from flask import Flask, jsonify, request, render_template, redirect, url_for, session, send_file, flash
from fpdf import FPDF

app = Flask(__name__)
# Standard secret key practice for session management
app.secret_key = "super_secret_key"
DB_NAME = "aceest_fitness.db"

# ---------- DATABASE INITIALIZATION ----------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    # Users
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        username TEXT PRIMARY KEY,
        password TEXT,
        role TEXT
    )
    """)
    
    # Clients
    cur.execute("""
    CREATE TABLE IF NOT EXISTS clients (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        age INTEGER,
        height REAL,
        weight REAL,
        program TEXT,
        calories INTEGER,
        target_weight REAL,
        target_adherence INTEGER,
        membership_status TEXT,
        membership_end TEXT
    )
    """)
    
    # Progress
    cur.execute("""
    CREATE TABLE IF NOT EXISTS progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_name TEXT,
        week TEXT,
        adherence INTEGER
    )
    """)
    
    # Workouts
    cur.execute("""
    CREATE TABLE IF NOT EXISTS workouts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_name TEXT,
        date TEXT,
        workout_type TEXT,
        duration_min INTEGER,
        notes TEXT
    )
    """)
    
    # Exercises
    cur.execute("""
    CREATE TABLE IF NOT EXISTS exercises (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        workout_id INTEGER,
        name TEXT,
        sets INTEGER,
        reps INTEGER,
        weight REAL
    )
    """)
    
    # Metrics
    cur.execute("""
    CREATE TABLE IF NOT EXISTS metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        client_name TEXT,
        date TEXT,
        weight REAL,
        waist REAL,
        bodyfat REAL
    )
    """)
    
    # Defaults
    cur.execute("SELECT * FROM users WHERE username='admin'")
    if not cur.fetchone():
        cur.execute("INSERT INTO users VALUES ('admin','admin','Admin')")

    conn.commit()
    conn.close()

# Templates dictionary
PROGRAM_TEMPLATES = {
    "Fat Loss": ["Full Body HIIT", "Circuit Training", "Cardio + Weights"],
    "Muscle Gain": ["Push/Pull/Legs", "Upper/Lower Split", "Full Body Strength"],
    "Beginner": ["Full Body 3x/week", "Light Strength + Mobility"]
}

def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

# ---------- AUTH ROUTES ----------
@app.route('/', methods=['GET', 'POST'])
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'current_user' in session:
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password'].strip()
        
        conn = get_db()
        user = conn.execute("SELECT role FROM users WHERE username=? AND password=?", (username, password)).fetchone()
        conn.close()
        
        if user:
            session['current_user'] = username
            session['current_role'] = user['role']
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid credentials!")
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# ---------- DASHBOARD ----------
@app.route('/dashboard')
def dashboard():
    if 'current_user' not in session:
        return redirect(url_for('login'))
        
    conn = get_db()
    clients = conn.execute("SELECT name FROM clients ORDER BY name").fetchall()
    conn.close()
    
    return render_template('dashboard.html', clients=[c['name'] for c in clients], current_user=session['current_user'])

@app.route('/add_client', methods=['POST'])
def add_client():
    if 'current_user' not in session:
        return redirect(url_for('login'))
        
    name = request.form['name'].strip()
    if name:
        conn = get_db()
        conn.execute("INSERT OR IGNORE INTO clients (name, membership_status) VALUES (?, ?)", (name, "Active"))
        conn.commit()
        conn.close()
        flash(f"Client {name} saved successfully.")
    
    return redirect(url_for('dashboard'))

# ---------- CLIENT DETAILS ----------
@app.route('/client/<name>')
def client_details(name):
    if 'current_user' not in session:
        return redirect(url_for('login'))
        
    conn = get_db()
    row = conn.execute("SELECT * FROM clients WHERE name=?", (name,)).fetchone()
    client = dict(row) if row else None
    workouts = conn.execute("SELECT * FROM workouts WHERE client_name=? ORDER BY date DESC", (name,)).fetchall()
    conn.close()
    
    if not client:
        flash("Client not found.")
        return redirect(url_for('dashboard'))
        
    return render_template('client_details.html', client=client, workouts=workouts)

# ---------- GENERATE PROGRAM ----------
@app.route('/client/<name>/generate_program', methods=['POST'])
def generate_program(name):
    if 'current_user' not in session:
        return redirect(url_for('login'))
        
    program_type = random.choice(list(PROGRAM_TEMPLATES.keys()))
    program_detail = random.choice(PROGRAM_TEMPLATES[program_type])
    
    print(f"\n[AI GENERATOR] Generated {program_detail} for {name}\n")
    
    conn = get_db()
    conn.execute("UPDATE clients SET program=? WHERE name=?", (program_detail, name))
    conn.commit()
    conn.close()
    
    flash(f"Generated AI Program for {name}: {program_detail}")
    return redirect(url_for('client_details', name=name))

# ---------- ADD WORKOUT ----------
@app.route('/client/<name>/add_workout', methods=['POST'])
def add_workout(name):
    if 'current_user' not in session:
        return redirect(url_for('login'))
        
    w_date = request.form['date']
    w_type = request.form['type']
    w_duration = request.form.get('duration', 60)
    w_notes = request.form.get('notes', '')
    
    conn = get_db()
    conn.execute("INSERT INTO workouts (client_name, date, workout_type, duration_min, notes) VALUES (?,?,?,?,?)",
                 (name, w_date, w_type, w_duration, w_notes))
    conn.commit()
    conn.close()
    
    flash("Workout added successfully.")
    return redirect(url_for('client_details', name=name))

# ---------- PDF GENERATION ----------
@app.route('/client/<name>/generate_pdf')
def generate_pdf(name):
    if 'current_user' not in session:
        return redirect(url_for('login'))
        
    conn = get_db()
    row = conn.execute("SELECT * FROM clients WHERE name=?", (name,)).fetchone()
    client = dict(row) if row else None
    conn.close()
    
    if not client:
        return "Client not found", 404
        
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"ACEest Client Report - {name}", ln=True)
    
    pdf.set_font("Arial", "", 12)
    pdf.cell(0, 10, f"ID: {client.get('id', 'N/A')}", ln=True)
    pdf.cell(0, 10, f"Name: {client.get('name', 'N/A')}", ln=True)
    pdf.cell(0, 10, f"Age: {client.get('age', 'N/A')}", ln=True)
    pdf.cell(0, 10, f"Height: {client.get('height', 'N/A')}", ln=True)
    pdf.cell(0, 10, f"Weight: {client.get('weight', 'N/A')}", ln=True)
    pdf.cell(0, 10, f"Program: {client.get('program', 'N/A')}", ln=True)
    pdf.cell(0, 10, f"Calories: {client.get('calories', 'N/A')}", ln=True)
    pdf.cell(0, 10, f"Target Weight: {client.get('target_weight', 'N/A')}", ln=True)
    pdf.cell(0, 10, f"Target Adherence: {client.get('target_adherence', 'N/A')}", ln=True)
    pdf.cell(0, 10, f"Membership: {client.get('membership_status', 'N/A')}", ln=True)
    pdf.cell(0, 10, f"End Date: {client.get('membership_end', 'N/A')}", ln=True)
    
    filename = f"{name}_report.pdf"
    pdf.output(filename)
    return send_file(filename, as_attachment=True)

# ---------- CHART API ----------
@app.route('/api/progress/<name>')
def get_progress(name):
    conn = get_db()
    data = conn.execute("SELECT week, adherence FROM progress WHERE client_name=? ORDER BY id", (name,)).fetchall()
    conn.close()
    
    return jsonify({
        "labels": [d["week"] for d in data],
        "adherence": [d["adherence"] for d in data]
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy"}), 200

if __name__ == '__main__':
    init_db()
    
    # Optional: Fill some dummy progress data so the chart looks nice on new test users
    conn = sqlite3.connect(DB_NAME)
    try:
        # Check if progress exists for admin/test
        prog = conn.execute("SELECT count(*) FROM progress").fetchone()[0]
        if prog == 0:
            for w in range(1, 5):
                conn.execute("INSERT INTO progress (client_name, week, adherence) VALUES (?,?,?)", ("Test User", f"Week {w}", random.randint(70,100)))
        conn.commit()
    except:
        pass
    conn.close()
    
    app.run(host='0.0.0.0', port=5000, debug=True)
