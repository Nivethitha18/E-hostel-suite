"""
============================================================
  HOSTEL MANAGEMENT SYSTEM — Flask Backend
  File : app.py
  Run  : python app.py
  Open : http://localhost:5000
============================================================
  ROUTES
  ──────
  GET  /                      → serve index.html
  GET  /api/room_stats        → room occupancy counts
  POST /api/allocate_room     → register student in a room
  GET  /api/wardens           → list all wardens
  POST /api/add_warden        → add a new warden
  PUT  /api/update_warden     → update existing warden
  DELETE /api/delete_warden   → delete a warden
  GET  /api/students          → list all students
  GET  /api/room_students     → students in one room
  DELETE /api/remove_student  → remove a student
============================================================
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import mysql.connector

# ─────────────────────────────────────────────────────────
# FLASK APP SETUP
# ─────────────────────────────────────────────────────────
app = Flask(__name__, static_folder='.')
# static_folder='.' → Flask looks for index.html in same folder

CORS(app)
# CORS = Cross-Origin Resource Sharing
# Without this, the browser refuses to let the HTML page
# call the Flask API (security restriction called CORS policy)


# ─────────────────────────────────────────────────────────
# DATABASE CONFIG  ← PUT YOUR MYSQL PASSWORD HERE
# ─────────────────────────────────────────────────────────
DB_CONFIG = {
    'host':     '127.0.0.1',
    'port':     3306,
    'user':     'root',
    'password': 'Mysql@123',   # ← CHANGE THIS TO YOUR PASSWORD
    'database': 'hostel_db'
}


# ─────────────────────────────────────────────────────────
# DATABASE CONNECTION HELPER
# Every route calls get_db() to open a fresh connection.
# We close it in the finally block of each route.
# ─────────────────────────────────────────────────────────
def get_db():
    """
    Opens and returns a MySQL connection.
    Returns None if connection fails (wrong password, MySQL not running, etc.)
    Prints the exact error so you can see it in the terminal.
    """
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        # This prints in the terminal when you run python app.py
        print(f"\n[DB ERROR] ──────────────────────────────")
        print(f"  Code   : {err.errno}")
        print(f"  Message: {err.msg}")
        print(f"────────────────────────────────────────\n")
        return None


# ─────────────────────────────────────────────────────────
# ROUTE 1 — Serve the frontend HTML
# When you open http://localhost:5000 in browser,
# Flask sends back index.html from the same folder.
# ─────────────────────────────────────────────────────────
@app.route('/')
def serve_frontend():
    return send_from_directory('.', 'index.html')


# ═════════════════════════════════════════════════════════
#  WARDEN ROUTES  (the ones you asked to add)
# ═════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────
# ROUTE 2 — GET /api/wardens
#
# What it does:
#   Reads all rows from the wardens table in MySQL.
#   Returns them as a JSON array to the frontend.
#   The frontend displays them in the "Existing Wardens" list.
#
# Example response:
#   [
#     { "warden_id": 1, "name": "Rajesh", "email": "...",
#       "phone": "...", "block": "D", "created_at": "..." },
#     ...
#   ]
# ─────────────────────────────────────────────────────────
@app.route('/api/wardens', methods=['GET'])
def get_wardens():
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database connection failed. Check terminal for details.'}), 500

    cursor = None
    try:
        # dictionary=True → each row comes back as a dict, not a tuple
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                warden_id,
                name,
                email,
                phone,
                block,
                created_at
            FROM wardens
            ORDER BY created_at DESC
        """)

        wardens = cursor.fetchall()

        # MySQL datetime objects can't be JSON-serialised directly.
        # Convert them to strings so jsonify() works.
        for w in wardens:
            if w.get('created_at'):
                w['created_at'] = str(w['created_at'])

        print(f"[GET /api/wardens] Returned {len(wardens)} wardens")
        return jsonify(wardens), 200

    except mysql.connector.Error as err:
        print(f"[ERROR /api/wardens] {err}")
        return jsonify({'error': str(err)}), 500

    finally:
        # Always close cursor and connection to avoid memory leaks
        if cursor:
            cursor.close()
        conn.close()


# ─────────────────────────────────────────────────────────
# ROUTE 3 — POST /api/add_warden
#
# What it does:
#   Receives warden form data (name, email, phone, block)
#   as JSON from the frontend.
#   Validates all fields.
#   Checks for duplicate email (unique constraint).
#   Inserts a new row into the wardens table.
#   Returns success or detailed error message.
#
# Request body (JSON):
#   {
#     "name":  "Mr. John",
#     "email": "john@hostel.edu",
#     "phone": "9876543212",
#     "block": "D"
#   }
#
# Response (success):
#   { "success": true, "message": "Warden added!", "warden_id": 3 }
#
# Response (error):
#   { "success": false, "message": "Email already registered!" }
# ─────────────────────────────────────────────────────────
@app.route('/api/add_warden', methods=['POST'])
def add_warden():
    conn = get_db()
    if not conn:
        return jsonify({
            'success': False,
            'message': 'Database connection failed. Is MySQL running? Check terminal.'
        }), 500

    cursor = None
    try:
        # Read JSON body sent from the frontend fetch() call
        data = request.get_json()

        if not data:
            return jsonify({'success': False, 'message': 'No data received. Send JSON body.'}), 400

        print(f"[POST /api/add_warden] Received: {data}")

        # ── Step 1: Validate all required fields ──────────────
        required_fields = ['name', 'email', 'phone', 'block']
        for field in required_fields:
            value = data.get(field, '').strip() if data.get(field) else ''
            if not value:
                return jsonify({
                    'success': False,
                    'message': f'Field "{field}" is required and cannot be empty.'
                }), 400

        # Strip whitespace from all values
        name  = data['name'].strip()
        email = data['email'].strip().lower()   # store email in lowercase
        phone = data['phone'].strip()
        block = data['block'].strip().upper()   # store block as uppercase D or L

        # ── Step 2: Validate block value ──────────────────────
        if block not in ('D', 'L'):
            return jsonify({
                'success': False,
                'message': f'Block must be "D" or "L". Received: "{block}"'
            }), 400

        # ── Step 3: Validate phone (must be digits, 7–15 chars) ──
        if not phone.replace('+', '').replace('-', '').replace(' ', '').isdigit():
            return jsonify({
                'success': False,
                'message': 'Phone number must contain only digits.'
            }), 400

        # ── Step 4: Validate email format (basic check) ───────
        if '@' not in email or '.' not in email.split('@')[-1]:
            return jsonify({
                'success': False,
                'message': 'Please enter a valid email address.'
            }), 400

        cursor = conn.cursor(dictionary=True)

        # ── Step 5: Check if email already exists ─────────────
        # We do this BEFORE INSERT to give a friendly message
        # (MySQL would throw a 1062 Duplicate Entry error otherwise)
        cursor.execute(
            "SELECT warden_id FROM wardens WHERE email = %s",
            (email,)
        )
        if cursor.fetchone():
            return jsonify({
                'success': False,
                'message': f'A warden with email "{email}" is already registered!'
            }), 409   # 409 = Conflict

        # ── Step 6: Insert new warden into database ────────────
        cursor.execute("""
            INSERT INTO wardens (name, email, phone, block)
            VALUES (%s, %s, %s, %s)
        """, (name, email, phone, block))

        conn.commit()   # Save the INSERT permanently

        # Get the auto-generated warden_id so we can return it
        new_warden_id = cursor.lastrowid

        print(f"[POST /api/add_warden] SUCCESS — warden_id={new_warden_id}, name={name}, block={block}")

        return jsonify({
            'success':   True,
            'message':   f'Warden "{name}" added successfully to {block} Block!',
            'warden_id': new_warden_id
        }), 201   # 201 = Created

    except mysql.connector.Error as err:
        # Rollback any partial changes if something went wrong
        conn.rollback()
        print(f"[ERROR /api/add_warden] MySQL Error {err.errno}: {err.msg}")

        # Give a friendly message for the most common MySQL errors
        if err.errno == 1062:
            return jsonify({'success': False, 'message': 'Duplicate entry — email already exists!'}), 409
        elif err.errno == 1366:
            return jsonify({'success': False, 'message': 'Invalid data type for one of the fields.'}), 400
        else:
            return jsonify({'success': False, 'message': f'Database error: {err.msg}'}), 500

    except Exception as ex:
        conn.rollback()
        print(f"[ERROR /api/add_warden] Unexpected: {ex}")
        return jsonify({'success': False, 'message': f'Unexpected error: {str(ex)}'}), 500

    finally:
        if cursor:
            cursor.close()
        conn.close()


# ─────────────────────────────────────────────────────────
# ROUTE 4 — PUT /api/update_warden
#
# What it does:
#   Updates an existing warden's details.
#   Useful if you want to change their phone or block.
#
# Request body (JSON):
#   {
#     "warden_id": 2,
#     "name":  "Mrs. Priya S",
#     "email": "priya@hostel.edu",
#     "phone": "9000000001",
#     "block": "L"
#   }
# ─────────────────────────────────────────────────────────
@app.route('/api/update_warden', methods=['PUT'])
def update_warden():
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed.'}), 500

    cursor = None
    try:
        data = request.get_json()

        if not data or not data.get('warden_id'):
            return jsonify({'success': False, 'message': 'warden_id is required.'}), 400

        warden_id = int(data['warden_id'])
        name      = data.get('name',  '').strip()
        email     = data.get('email', '').strip().lower()
        phone     = data.get('phone', '').strip()
        block     = data.get('block', '').strip().upper()

        if not all([name, email, phone, block]):
            return jsonify({'success': False, 'message': 'All fields are required.'}), 400

        if block not in ('D', 'L'):
            return jsonify({'success': False, 'message': 'Block must be D or L.'}), 400

        cursor = conn.cursor(dictionary=True)

        # Check warden exists
        cursor.execute("SELECT warden_id FROM wardens WHERE warden_id = %s", (warden_id,))
        if not cursor.fetchone():
            return jsonify({'success': False, 'message': f'Warden ID {warden_id} not found.'}), 404

        # Check email not taken by another warden
        cursor.execute(
            "SELECT warden_id FROM wardens WHERE email = %s AND warden_id != %s",
            (email, warden_id)
        )
        if cursor.fetchone():
            return jsonify({'success': False, 'message': 'Email is already used by another warden.'}), 409

        cursor.execute("""
            UPDATE wardens
            SET name=%s, email=%s, phone=%s, block=%s
            WHERE warden_id=%s
        """, (name, email, phone, block, warden_id))

        conn.commit()
        print(f"[PUT /api/update_warden] Updated warden_id={warden_id}")
        return jsonify({'success': True, 'message': 'Warden updated successfully!'}), 200

    except mysql.connector.Error as err:
        conn.rollback()
        print(f"[ERROR /api/update_warden] {err}")
        return jsonify({'success': False, 'message': f'Database error: {err.msg}'}), 500

    finally:
        if cursor: cursor.close()
        conn.close()


# ─────────────────────────────────────────────────────────
# ROUTE 5 — DELETE /api/delete_warden
#
# What it does:
#   Deletes a warden by warden_id.
#   Students linked to this warden will have warden_id set to NULL
#   (because of ON DELETE SET NULL in the FK constraint).
#
# Request body (JSON):
#   { "warden_id": 3 }
# ─────────────────────────────────────────────────────────
@app.route('/api/delete_warden', methods=['DELETE'])
def delete_warden():
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed.'}), 500

    cursor = None
    try:
        data      = request.get_json()
        warden_id = data.get('warden_id') if data else None

        if not warden_id:
            return jsonify({'success': False, 'message': 'warden_id is required.'}), 400

        cursor = conn.cursor()
        cursor.execute("DELETE FROM wardens WHERE warden_id = %s", (int(warden_id),))
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({'success': False, 'message': f'Warden ID {warden_id} not found.'}), 404

        print(f"[DELETE /api/delete_warden] Deleted warden_id={warden_id}")
        return jsonify({'success': True, 'message': 'Warden deleted successfully.'}), 200

    except mysql.connector.Error as err:
        conn.rollback()
        print(f"[ERROR /api/delete_warden] {err}")
        return jsonify({'success': False, 'message': f'Database error: {err.msg}'}), 500

    finally:
        if cursor: cursor.close()
        conn.close()


# ═════════════════════════════════════════════════════════
#  ROOM ALLOCATION ROUTES
# ═════════════════════════════════════════════════════════

# ─────────────────────────────────────────────────────────
# ROUTE 6 — GET /api/room_stats
# Returns { block, floor, room_number, student_count }
# for every room that has at least 1 student.
# Frontend uses this to colour rooms green/yellow/red.
# ─────────────────────────────────────────────────────────
@app.route('/api/room_stats', methods=['GET'])
def room_stats():
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database connection failed.'}), 500

    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT
                block,
                floor,
                room_number,
                COUNT(*) AS student_count
            FROM students
            GROUP BY block, floor, room_number
        """)
        rows = cursor.fetchall()
        print(f"[GET /api/room_stats] {len(rows)} rooms have students")
        return jsonify(rows), 200

    except mysql.connector.Error as err:
        print(f"[ERROR /api/room_stats] {err}")
        return jsonify({'error': str(err)}), 500

    finally:
        if cursor: cursor.close()
        conn.close()


# ─────────────────────────────────────────────────────────
# ROUTE 7 — POST /api/allocate_room
#
# Steps inside this route:
#   1. Validate all required fields
#   2. Check room is not already full (max 3 students)
#   3. Check student_id is not duplicate
#   4. Check roll_number is not duplicate
#   5. Insert parent record (if new parent_id)
#   6. Insert student record linked to parent
# ─────────────────────────────────────────────────────────
@app.route('/api/allocate_room', methods=['POST'])
def allocate_room():
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed.'}), 500

    cursor = None
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': 'No JSON body received.'}), 400

        print(f"[POST /api/allocate_room] Received: {data}")

        # Validate all required fields
        required = [
            'student_id', 'name', 'roll_number', 'dept', 'year', 'phone',
            'parent_id', 'parent_name', 'parent_phone',
            'block', 'floor', 'room_number'
        ]
        for field in required:
            if not data.get(field) or str(data[field]).strip() == '':
                return jsonify({'success': False, 'message': f'Missing required field: {field}'}), 400

        cursor = conn.cursor(dictionary=True)

        # Check 1: Room full?
        cursor.execute("""
            SELECT COUNT(*) AS total FROM students
            WHERE block = %s AND floor = %s AND room_number = %s
        """, (data['block'], int(data['floor']), int(data['room_number'])))
        if cursor.fetchone()['total'] >= 3:
            return jsonify({'success': False, 'message': 'This room is already full! (Max 3 students)'}), 409

        # Check 2: Duplicate student_id?
        cursor.execute("SELECT student_id FROM students WHERE student_id = %s", (data['student_id'],))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': f"Student ID '{data['student_id']}' already exists!"}), 409

        # Check 3: Duplicate roll_number?
        cursor.execute("SELECT roll_number FROM students WHERE roll_number = %s", (data['roll_number'],))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': f"Roll number '{data['roll_number']}' is already registered!"}), 409

        # Check 4: Does parent_id already exist?
        cursor.execute("SELECT parent_id FROM parents WHERE parent_id = %s", (data['parent_id'],))
        if not cursor.fetchone():
            # Insert parent first (FK requires parent to exist before student)
            cursor.execute("""
                INSERT INTO parents (parent_id, name, phone, relation)
                VALUES (%s, %s, %s, %s)
            """, (
                data['parent_id'].strip(),
                data['parent_name'].strip(),
                data['parent_phone'].strip(),
                data.get('parent_relation', 'Parent')
            ))
            print(f"[POST /api/allocate_room] Inserted parent: {data['parent_id']}")

        # Insert student
        cursor.execute("""
            INSERT INTO students
                (student_id, name, roll_number, dept, year, phone,
                 block, floor, room_number, parent_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data['student_id'].strip(),
            data['name'].strip(),
            data['roll_number'].strip(),
            data['dept'].strip(),
            data['year'].strip(),
            data['phone'].strip(),
            data['block'].strip(),
            int(data['floor']),
            int(data['room_number']),
            data['parent_id'].strip()
        ))

        conn.commit()
        print(f"[POST /api/allocate_room] SUCCESS student={data['student_id']} room={data['room_number']} block={data['block']}")
        return jsonify({
            'success': True,
            'message': f"Room {data['room_number']} ({data['block']} Block) allocated to {data['name']}!"
        }), 201

    except mysql.connector.Error as err:
        conn.rollback()
        print(f"[ERROR /api/allocate_room] {err.errno}: {err.msg}")
        if err.errno == 1062:
            return jsonify({'success': False, 'message': 'Duplicate entry detected.'}), 409
        return jsonify({'success': False, 'message': f'Database error: {err.msg}'}), 500

    finally:
        if cursor: cursor.close()
        conn.close()


# ─────────────────────────────────────────────────────────
# ROUTE 8 — GET /api/students
# Returns all students joined with their parent info.
# Useful for admin dashboard or future reports page.
# ─────────────────────────────────────────────────────────
@app.route('/api/students', methods=['GET'])
def get_students():
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database connection failed.'}), 500

    cursor = None
    try:
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT
                s.student_id, s.name, s.roll_number, s.dept,
                s.year, s.phone, s.block, s.floor, s.room_number,
                s.created_at,
                p.name      AS parent_name,
                p.phone     AS parent_phone,
                p.relation  AS parent_relation
            FROM students s
            LEFT JOIN parents p ON s.parent_id = p.parent_id
            ORDER BY s.created_at DESC
        """)
        students = cursor.fetchall()
        for s in students:
            if s.get('created_at'):
                s['created_at'] = str(s['created_at'])
        print(f"[GET /api/students] Returned {len(students)} students")
        return jsonify(students), 200

    except mysql.connector.Error as err:
        print(f"[ERROR /api/students] {err}")
        return jsonify({'error': str(err)}), 500

    finally:
        if cursor: cursor.close()
        conn.close()


# ─────────────────────────────────────────────────────────
# ROUTE 9 — GET /api/room_students
# Returns students inside one specific room.
# Usage: /api/room_students?block=D&floor=0&room=5
# ─────────────────────────────────────────────────────────
@app.route('/api/room_students', methods=['GET'])
def room_students():
    conn = get_db()
    if not conn:
        return jsonify({'error': 'Database connection failed.'}), 500

    cursor = None
    try:
        block = request.args.get('block')
        floor = request.args.get('floor')
        room  = request.args.get('room')

        if not all([block, floor, room]):
            return jsonify({'error': 'block, floor and room query params are required.'}), 400

        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT
                s.student_id, s.name, s.roll_number,
                s.dept, s.year, s.phone,
                p.name     AS parent_name,
                p.phone    AS parent_phone,
                p.relation AS parent_relation
            FROM students s
            LEFT JOIN parents p ON s.parent_id = p.parent_id
            WHERE s.block = %s AND s.floor = %s AND s.room_number = %s
        """, (block, int(floor), int(room)))

        return jsonify(cursor.fetchall()), 200

    except mysql.connector.Error as err:
        print(f"[ERROR /api/room_students] {err}")
        return jsonify({'error': str(err)}), 500

    finally:
        if cursor: cursor.close()
        conn.close()


# ─────────────────────────────────────────────────────────
# ROUTE 10 — DELETE /api/remove_student
# Removes a student (frees their room slot).
# Body: { "student_id": "STU001" }
# ─────────────────────────────────────────────────────────
@app.route('/api/remove_student', methods=['DELETE'])
def remove_student():
    conn = get_db()
    if not conn:
        return jsonify({'success': False, 'message': 'Database connection failed.'}), 500

    cursor = None
    try:
        data       = request.get_json()
        student_id = data.get('student_id') if data else None

        if not student_id:
            return jsonify({'success': False, 'message': 'student_id is required.'}), 400

        cursor = conn.cursor()
        cursor.execute("DELETE FROM students WHERE student_id = %s", (student_id,))
        conn.commit()

        if cursor.rowcount == 0:
            return jsonify({'success': False, 'message': f'Student "{student_id}" not found.'}), 404

        print(f"[DELETE /api/remove_student] Removed student_id={student_id}")
        return jsonify({'success': True, 'message': f'Student "{student_id}" removed successfully.'}), 200

    except mysql.connector.Error as err:
        conn.rollback()
        print(f"[ERROR /api/remove_student] {err}")
        return jsonify({'success': False, 'message': f'Database error: {err.msg}'}), 500

    finally:
        if cursor: cursor.close()
        conn.close()


# ─────────────────────────────────────────────────────────
# START THE SERVER
# debug=True  → Flask restarts automatically when you save app.py
# port=5000   → open http://localhost:5000 in browser
# ─────────────────────────────────────────────────────────
if __name__ == '__main__':
    print("\n" + "=" * 55)
    print("   HOSTEL MANAGEMENT SYSTEM — Backend Running")
    print("   Open  →  http://localhost:5000")
    print("=" * 55)
    print("\n  Routes available:")
    print("  GET  /api/wardens       — list all wardens")
    print("  POST /api/add_warden    — add new warden")
    print("  PUT  /api/update_warden — update warden")
    print("  DEL  /api/delete_warden — delete warden")
    print("  GET  /api/room_stats    — room occupancy")
    print("  POST /api/allocate_room — register student")
    print("  GET  /api/students      — all students")
    print("=" * 55 + "\n")
    app.run(debug=True, port=5000)
