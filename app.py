import os
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from db import get_db_connection

app = Flask(__name__)
app.secret_key = 'matrix_cyberpunk_secret_key'

UPLOAD_FOLDER = os.path.join('static', 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection failed"}), 500

    cursor = conn.cursor(dictionary=True)
    
    if username == 'admin@nexus.corp' and password == 'matrix2026':
        role = 'HR_ADMIN'
    else:
        cursor.execute("SELECT * FROM employees WHERE username = %s AND password_hash = %s", (username, password))
        user = cursor.fetchone()
        if not user:
            cursor.close()
            conn.close()
            return jsonify({"success": False, "message": "Invalid credentials"}), 401
        role = user['user_role']

    log_cursor = conn.cursor()
    log_cursor.execute("INSERT INTO audit_logs (username, action_type, details) VALUES (%s, %s, %s)",
                       (username, 'LOGIN', f"Session initiated ({role})"))
    conn.commit()
    
    cursor.close()
    log_cursor.close()
    conn.close()
    return jsonify({"success": True, "role": role, "username": username})

@app.route('/api/logs', methods=['GET'])
def get_audit_logs():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT 50")
    logs = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(logs)

# 3. GET ALL EMPLOYEES
@app.route('/api/employees', methods=['GET'])
def get_employees():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, code, name, dept, role, salary, status, username, user_role, photo_url FROM employees")
    employees = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(employees)

# 4. ADMIN CREATE NEW EMPLOYEE
@app.route('/api/employees', methods=['POST'])
def add_employee():
    data = request.json
    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection failed"}), 500
    
    cursor = conn.cursor()
    cursor.execute("SELECT IFNULL(MAX(id), 0) + 1 FROM employees")
    next_id = cursor.fetchone()[0]
    code = f"NX-{next_id:03d}"

    raw_user = data.get('username', '').strip()
    email = raw_user if raw_user else f"{data.get('name').split()[0].lower()}{next_id}@nexus.corp"
    default_avatar = f"https://api.dicebear.com/7.x/bottts/svg?seed={code}"

    try:
        query = """INSERT INTO employees (code, name, dept, role, salary, status, username, password_hash, user_role, photo_url) 
                   VALUES (%s, %s, %s, %s, %s, 'ACTIVE', %s, 'matrix2026', 'EMPLOYEE', %s)"""
        cursor.execute(query, (
            code,
            data.get('name'),
            data.get('dept'),
            data.get('role'),
            data.get('salary'),
            email,
            default_avatar
        ))
        
        cursor.execute("INSERT INTO audit_logs (username, action_type, details) VALUES (%s, %s, %s)",
                       ('HR_ADMIN', 'CREATE_EMPLOYEE', f"Created operative {code} ({data.get('name')})"))
        
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"success": True, "code": code, "username": email})
    except Exception as e:
        conn.rollback()
        cursor.close()
        conn.close()
        return jsonify({"success": False, "message": str(e)}), 400

@app.route('/api/employees/<int:emp_id>', methods=['PUT'])
def admin_update_employee(emp_id):
    data = request.json
    conn = get_db_connection()
    cursor = conn.cursor()
    query = "UPDATE employees SET name = %s, dept = %s, role = %s, salary = %s WHERE id = %s"
    cursor.execute(query, (data.get('name'), data.get('dept'), data.get('role'), data.get('salary'), emp_id))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"success": True})

@app.route('/api/employees/<int:emp_id>', methods=['DELETE'])
def delete_employee(emp_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM employees WHERE id = %s", (emp_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"success": True})

# 7. EMPLOYEE SELF-SERVICE PROFILE
@app.route('/api/profile/update', methods=['POST'])
def update_own_profile():
    username = request.form.get('username')
    name = request.form.get('name')
    new_password = request.form.get('password')
    photo = request.files.get('photo')

    conn = get_db_connection()
    cursor = conn.cursor()

    photo_url = None
    if photo and photo.filename != '':
        filename = secure_filename(f"{username}_{photo.filename}")
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        photo.save(filepath)
        photo_url = f"/static/uploads/{filename}"

    if photo_url and new_password:
        cursor.execute("UPDATE employees SET name = %s, password_hash = %s, photo_url = %s WHERE username = %s",
                       (name, new_password, photo_url, username))
    elif photo_url:
        cursor.execute("UPDATE employees SET name = %s, photo_url = %s WHERE username = %s",
                       (name, photo_url, username))
    elif new_password:
        cursor.execute("UPDATE employees SET name = %s, password_hash = %s WHERE username = %s",
                       (name, new_password, username))
    else:
        cursor.execute("UPDATE employees SET name = %s WHERE username = %s", (name, username))

    cursor.execute("INSERT INTO audit_logs (username, action_type, details) VALUES (%s, %s, %s)",
                   (username, 'PROFILE_UPDATE', 'Operative updated personal profile and credentials'))

    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"success": True})

@app.route('/api/performance', methods=['GET'])
def get_performance():
    conn = get_db_connection()
    if not conn:
        return jsonify({"success": False, "message": "Database connection failed"}), 500
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM company_ratings ORDER BY created_at DESC LIMIT 20")
    reviews = cursor.fetchall()

    cursor.execute("SELECT IFNULL(ROUND(AVG(rating), 1), 5.0) AS avg_rating, COUNT(*) AS total_reviews FROM company_ratings")
    stats = cursor.fetchone()

    cursor.close()
    conn.close()
    return jsonify({
        "avg_rating": float(stats['avg_rating']),
        "total_reviews": stats['total_reviews'],
        "reviews": reviews
    })

@app.route('/api/performance', methods=['POST'])
def add_performance_rating():
    data = request.json
    username = data.get('username')
    rating = int(data.get('rating', 5))
    category = data.get('category', 'GENERAL')
    feedback = data.get('feedback', '').strip()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO company_ratings (username, rating, category, feedback) VALUES (%s, %s, %s, %s)",
        (username, rating, category, feedback)
    )
    cursor.execute(
        "INSERT INTO audit_logs (username, action_type, details) VALUES (%s, %s, %s)",
        (username, 'COMPANY_RATING', f"Submitted {rating}/5 rating under {category}")
    )
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({"success": True})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
