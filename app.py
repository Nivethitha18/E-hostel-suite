"""
============================================================
  HOSTEL MANAGEMENT SYSTEM - Flask Backend
  File: app.py

  HOW TO RUN:
    python app.py

  THEN OPEN BROWSER:
    http://localhost:5000
============================================================
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import mysql.connector

# ─────────────────────────────────────────────
# CREATE FLASK APP
# static_folder='.' means Flask serves files
# from the same folder as app.py
# ─────────────────────────────────────────────
app = Flask(__name__, static_folder='.')
CORS(app)

# ─────────────────────────────────────────────
# DATABASE CONFIG
# Change 'root123' to YOUR MySQL password
# ─────────────────────────────────────────────
DB_CONFIG = {
    'host':     'localhost',
    'user':     'root',
    'password': 'Mysql@123',      # ← CHANGE THIS
    'database': 'hostel_db'
}


def get_db():
    """Returns a MySQL connection. Prints error if it fails."""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as e:
        print(f"[DB ERROR] Cannot connect to MySQL: {e}")
        return None


# ─────────────────────────────────────────────
# ROUTE 1: Serve index.html when browser opens
#           http://localhost:5000
# ─────────────────────────────────────────────
@app.route('/')
def serve_frontend():
    return send_from_directory('.', 'index.html')


# ─────────────────────────────────────────────
# ROUTE 2: GET /api/room_stats
# Called by frontend on page load.
# Returns list of rooms with student counts.
# Example response:
# [{"block":"D","floor":0,"room_number":1,"student_count":2}, ...]
# ─────────────────────────────────────────────
@app.route('/api/room_stats', methods=['GET'])
def room_stats():
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT block, floor, room_number, COUNT(*) AS student_count
            FROM students
            GROUP BY block, floor, room_number
        """)
        rows = cursor.fetchall()
        return jsonify(rows)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ─────────────────────────────────────────────
# ROUTE 3: POST /api/allocate_room
# Called when student form is submitted.
# Validates data then inserts into MySQL.
# ─────────────────────────────────────────────
@app.route('/api/allocate_room', methods=['POST'])
def allocate_room():
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
    try:
        data = request.get_json()

        # Validate all required fields
        required = ['student_id','name','roll_number','dept','year','phone','block','floor','room_number']
        for field in required:
            if field not in data or str(data[field]).strip() == '':
                return jsonify({'success': False, 'message': f'Missing field: {field}'}), 400

        cursor = conn.cursor(dictionary=True)

        # Check if room is full (max 3 students)
        cursor.execute("""
            SELECT COUNT(*) AS total FROM students
            WHERE block=%s AND floor=%s AND room_number=%s
        """, (data['block'], int(data['floor']), int(data['room_number'])))
        if cursor.fetchone()['total'] >= 3:
            return jsonify({'success': False, 'message': 'Room is already full!'}), 409

        # Check duplicate student_id
        cursor.execute("SELECT student_id FROM students WHERE student_id=%s", (data['student_id'],))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'Student ID already exists!'}), 409

        # Check duplicate roll_number
        cursor.execute("SELECT roll_number FROM students WHERE roll_number=%s", (data['roll_number'],))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'Roll number already registered!'}), 409

        # Insert student
        cursor.execute("""
            INSERT INTO students
                (student_id, name, roll_number, dept, year, phone, block, floor, room_number)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data['student_id'].strip(),
            data['name'].strip(),
            data['roll_number'].strip(),
            data['dept'].strip(),
            data['year'].strip(),
            data['phone'].strip(),
            data['block'].strip(),
            int(data['floor']),
            int(data['room_number'])
        ))
        conn.commit()
        return jsonify({'success': True, 'message': 'Room allocated successfully!'})

    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ─────────────────────────────────────────────
# ROUTE 4: GET /api/students
# Returns all students. Useful for admin view.
# ─────────────────────────────────────────────
@app.route('/api/students', methods=['GET'])
def get_all_students():
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM students ORDER BY created_at DESC")
        students = cursor.fetchall()
        for s in students:
            if s.get('created_at'):
                s['created_at'] = str(s['created_at'])
        return jsonify(students)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ─────────────────────────────────────────────
# ROUTE 5: GET /api/room_students
# Returns students inside one specific room.
# Usage: /api/room_students?block=D&floor=0&room=5
# ─────────────────────────────────────────────
@app.route('/api/room_students', methods=['GET'])
def room_students():
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database connection failed'}), 500
    try:
        block = request.args.get('block')
        floor = request.args.get('floor')
        room  = request.args.get('room')
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT student_id, name, roll_number, dept, year, phone
            FROM students
            WHERE block=%s AND floor=%s AND room_number=%s
        """, (block, int(floor), int(room)))
        return jsonify(cursor.fetchall())
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ─────────────────────────────────────────────
# ROUTE 6: DELETE /api/remove_student
# Removes a student and frees their room slot.
# Body: { "student_id": "STU001" }
# ─────────────────────────────────────────────
@app.route('/api/remove_student', methods=['DELETE'])
def remove_student():
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed'}), 500
    try:
        data = request.get_json()
        student_id = data.get('student_id')
        if not student_id:
            return jsonify({'success': False, 'message': 'student_id required'}), 400
        cursor = conn.cursor()
        cursor.execute("DELETE FROM students WHERE student_id=%s", (student_id,))
        conn.commit()
        if cursor.rowcount == 0:
            return jsonify({'success': False, 'message': 'Student not found'}), 404
        return jsonify({'success': True, 'message': 'Student removed successfully'})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ─────────────────────────────────────────────
# START SERVER
# ─────────────────────────────────────────────
if __name__ == '__main__':
    print("\n" + "="*50)
    print("  Hostel Management System - Backend Running")
    print("  Open http://localhost:5000 in your browser")
    print("="*50 + "\n")
    app.run(debug=True, port=5000)