"""
============================================================
  HOSTEL MANAGEMENT SYSTEM — Flask Backend v2
  File : app.py  |  Run: python app.py  |  http://localhost:5000

  Admin    → username=admin  password=admin123
  Student  → roll_number + phone
  Parent   → phone + OTP (OTP shown in toast for demo)
  Warden   → warden_id
  Watchman → watchman_id
============================================================
"""
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import mysql.connector
from datetime import datetime, timedelta
import random, string

app = Flask(__name__, static_folder='.')
CORS(app)

DB_CONFIG = {
    'host': '127.0.0.1', 'port': 3306,
    'user': 'root', 'password': 'Mysql@123',   # ← YOUR PASSWORD
    'database': 'hostel_db'
}
ADMIN_CREDS = {'username': 'admin', 'password': 'admin123'}


def get_db():
    try:
        return mysql.connector.connect(**DB_CONFIG)
    except mysql.connector.Error as err:
        print(f"[DB ERROR] {err.errno}: {err.msg}")
        return None


def s(v): return str(v) if isinstance(v, datetime) else v
def sr(row): return {k: s(v) for k, v in row.items()}
def gen_otp(): return ''.join(random.choices(string.digits, k=6))


@app.route('/')
def serve_frontend():
    return send_from_directory('.', 'index.html')


# ══════════════════ AUTH ══════════════════

@app.route('/api/auth/login', methods=['POST'])
def auth_login():
    data = request.get_json() or {}
    role = data.get('role', '').lower()

    if role == 'admin':
        if data.get('username') == ADMIN_CREDS['username'] and data.get('password') == ADMIN_CREDS['password']:
            return jsonify({'success': True, 'role': 'admin', 'name': 'Administrator'})
        return jsonify({'success': False, 'message': 'Invalid admin credentials.'}), 401

    conn = get_db()
    if not conn: return jsonify({'success': False, 'message': 'DB failed'}), 500
    cur = None
    try:
        cur = conn.cursor(dictionary=True)
        if role == 'student':
            roll  = data.get('roll_number', '').strip()
            phone = data.get('phone', '').strip()
            if not roll or not phone:
                return jsonify({'success': False, 'message': 'Roll number and phone required.'}), 400
            cur.execute("""SELECT s.*,p.name AS parent_name,p.phone AS parent_phone,p.parent_id
                           FROM students s LEFT JOIN parents p ON s.parent_id=p.parent_id
                           WHERE s.roll_number=%s AND s.phone=%s""", (roll, phone))
            row = cur.fetchone()
            if not row: return jsonify({'success': False, 'message': 'Invalid roll number or phone.'}), 401
            return jsonify({'success': True, 'role': 'student', 'data': sr(row)})

        elif role == 'warden':
            wid = data.get('warden_id')
            if not wid: return jsonify({'success': False, 'message': 'Warden ID required.'}), 400
            cur.execute("SELECT * FROM wardens WHERE warden_id=%s", (int(wid),))
            row = cur.fetchone()
            if not row: return jsonify({'success': False, 'message': 'Warden not found.'}), 401
            return jsonify({'success': True, 'role': 'warden', 'data': sr(row)})

        elif role == 'watchman':
            wmid = data.get('watchman_id')
            if not wmid: return jsonify({'success': False, 'message': 'Watchman ID required.'}), 400
            cur.execute("SELECT * FROM watchmen WHERE watchman_id=%s AND active=1", (int(wmid),))
            row = cur.fetchone()
            if not row: return jsonify({'success': False, 'message': 'Watchman not found.'}), 401
            return jsonify({'success': True, 'role': 'watchman', 'data': sr(row)})

        return jsonify({'success': False, 'message': f'Unknown role: {role}'}), 400
    except mysql.connector.Error as err:
        return jsonify({'success': False, 'message': str(err)}), 500
    finally:
        if cur: cur.close()
        conn.close()


@app.route('/api/auth/parent/send-otp', methods=['POST'])
def parent_send_otp():
    data  = request.get_json() or {}
    phone = data.get('phone', '').strip()
    if not phone: return jsonify({'success': False, 'message': 'Phone required.'}), 400
    conn = get_db()
    if not conn: return jsonify({'success': False, 'message': 'DB failed'}), 500
    cur = None
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM parents WHERE phone=%s", (phone,))
        parent = cur.fetchone()
        if not parent: return jsonify({'success': False, 'message': 'No parent found with this phone number.'}), 404
        otp    = gen_otp()
        expiry = datetime.now() + timedelta(minutes=10)
        cur.execute("UPDATE parents SET otp=%s,otp_expiry=%s WHERE parent_id=%s",
                    (otp, expiry, parent['parent_id']))
        conn.commit()
        print(f"[OTP DEMO] phone={phone}  OTP={otp}")
        cur.execute("SELECT student_id,name,roll_number,dept,year,block,room_number FROM students WHERE parent_id=%s",
                    (parent['parent_id'],))
        students = cur.fetchall()
        return jsonify({'success': True, 'message': f'OTP sent to ****{phone[-4:]}',
                        'otp_demo': otp, 'parent_id': parent['parent_id'],
                        'parent_name': parent['name'], 'students': students})
    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({'success': False, 'message': str(err)}), 500
    finally:
        if cur: cur.close()
        conn.close()


@app.route('/api/auth/parent/verify-otp', methods=['POST'])
def parent_verify_otp():
    data      = request.get_json() or {}
    parent_id = data.get('parent_id')
    otp       = data.get('otp', '').strip()
    if not parent_id or not otp:
        return jsonify({'success': False, 'message': 'parent_id and otp required.'}), 400
    conn = get_db()
    if not conn: return jsonify({'success': False, 'message': 'DB failed'}), 500
    cur = None
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM parents WHERE parent_id=%s", (int(parent_id),))
        p = cur.fetchone()
        if not p: return jsonify({'success': False, 'message': 'Parent not found.'}), 404
        if p['otp'] != otp: return jsonify({'success': False, 'message': 'Invalid OTP.'}), 401
        if p['otp_expiry'] and datetime.now() > p['otp_expiry']:
            return jsonify({'success': False, 'message': 'OTP expired.'}), 401
        cur.execute("UPDATE parents SET otp=NULL,otp_expiry=NULL WHERE parent_id=%s", (int(parent_id),))
        conn.commit()
        cur.execute("SELECT student_id,name,roll_number,dept,year,block,room_number,phone FROM students WHERE parent_id=%s",
                    (int(parent_id),))
        students = cur.fetchall()
        return jsonify({'success': True, 'role': 'parent',
                        'data': {'parent_id': p['parent_id'], 'name': p['name'],
                                 'phone': p['phone'], 'students': students}})
    except mysql.connector.Error as err:
        conn.rollback()
        return jsonify({'success': False, 'message': str(err)}), 500
    finally:
        if cur: cur.close()
        conn.close()


# ══════════════════ ADMIN — WARDENS ══════════════════

@app.route('/api/admin/wardens', methods=['GET'])
def admin_get_wardens():
    conn = get_db()
    if not conn: return jsonify({'error': 'DB failed'}), 500
    cur = None
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM wardens ORDER BY year, warden_id")
        rows = cur.fetchall()
        for r in rows: r['created_at'] = str(r.get('created_at',''))
        return jsonify(rows)
    finally:
        if cur: cur.close()
        conn.close()


@app.route('/api/admin/add_warden', methods=['POST'])
def admin_add_warden():
    conn = get_db()
    if not conn: return jsonify({'success': False, 'message': 'DB failed'}), 500
    cur = None
    try:
        d = request.get_json() or {}
        name=d.get('name','').strip(); email=d.get('email','').strip().lower()
        phone=d.get('phone','').strip(); year=d.get('year','').strip()
        if not all([name,email,phone,year]): return jsonify({'success': False, 'message': 'All fields required.'}), 400
        if year not in ('1','2','3','4'): return jsonify({'success': False, 'message': 'Year 1–4 only.'}), 400
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT warden_id FROM wardens WHERE email=%s",(email,))
        if cur.fetchone(): return jsonify({'success': False, 'message': 'Email already exists!'}), 409
        cur.execute("INSERT INTO wardens(name,email,phone,year) VALUES(%s,%s,%s,%s)",(name,email,phone,year))
        conn.commit()
        return jsonify({'success': True, 'message': f'Warden "{name}" added for Year {year}!', 'warden_id': cur.lastrowid}), 201
    except mysql.connector.Error as err:
        conn.rollback(); return jsonify({'success': False, 'message': str(err)}), 500
    finally:
        if cur: cur.close()
        conn.close()


@app.route('/api/admin/delete_warden', methods=['DELETE'])
def admin_delete_warden():
    conn = get_db()
    if not conn: return jsonify({'success': False, 'message': 'DB failed'}), 500
    cur = None
    try:
        d = request.get_json() or {}
        wid = int(d.get('warden_id',0))
        cur = conn.cursor()
        cur.execute("DELETE FROM wardens WHERE warden_id=%s",(wid,))
        conn.commit()
        return jsonify({'success': cur.rowcount > 0, 'message': 'Warden deleted.' if cur.rowcount else 'Not found.'})
    except mysql.connector.Error as err:
        conn.rollback(); return jsonify({'success': False, 'message': str(err)}), 500
    finally:
        if cur: cur.close()
        conn.close()


# ══════════════════ ADMIN — WATCHMEN ══════════════════

@app.route('/api/admin/watchmen', methods=['GET'])
def admin_get_watchmen():
    conn = get_db()
    if not conn: return jsonify({'error': 'DB failed'}), 500
    cur = None
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM watchmen ORDER BY created_at DESC")
        rows = cur.fetchall()
        for r in rows: r['created_at'] = str(r.get('created_at',''))
        return jsonify(rows)
    finally:
        if cur: cur.close()
        conn.close()


@app.route('/api/admin/add_watchman', methods=['POST'])
def admin_add_watchman():
    conn = get_db()
    if not conn: return jsonify({'success': False, 'message': 'DB failed'}), 500
    cur = None
    try:
        d = request.get_json() or {}
        name=d.get('name','').strip(); phone=d.get('phone','').strip()
        email=d.get('email','').strip(); shift=d.get('shift','Morning')
        if not name or not phone: return jsonify({'success': False, 'message': 'Name & phone required.'}), 400
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT watchman_id FROM watchmen WHERE phone=%s",(phone,))
        if cur.fetchone(): return jsonify({'success': False, 'message': 'Phone already registered!'}), 409
        cur.execute("INSERT INTO watchmen(name,email,phone,shift) VALUES(%s,%s,%s,%s)",
                    (name,email or None,phone,shift))
        conn.commit()
        return jsonify({'success': True, 'message': f'Watchman "{name}" added!', 'watchman_id': cur.lastrowid}), 201
    except mysql.connector.Error as err:
        conn.rollback(); return jsonify({'success': False, 'message': str(err)}), 500
    finally:
        if cur: cur.close()
        conn.close()


@app.route('/api/admin/delete_watchman', methods=['DELETE'])
def admin_delete_watchman():
    conn = get_db()
    if not conn: return jsonify({'success': False, 'message': 'DB failed'}), 500
    cur = None
    try:
        d = request.get_json() or {}
        wmid = int(d.get('watchman_id',0))
        cur = conn.cursor()
        cur.execute("DELETE FROM watchmen WHERE watchman_id=%s",(wmid,))
        conn.commit()
        return jsonify({'success': cur.rowcount > 0, 'message': 'Watchman deleted.' if cur.rowcount else 'Not found.'})
    except mysql.connector.Error as err:
        conn.rollback(); return jsonify({'success': False, 'message': str(err)}), 500
    finally:
        if cur: cur.close()
        conn.close()


# ══════════════════ ROOM ALLOCATION ══════════════════

@app.route('/api/room_stats', methods=['GET'])
def room_stats():
    conn = get_db()
    if not conn: return jsonify({'error': 'DB failed'}), 500
    cur = None
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT block,floor,room_number,COUNT(*) AS student_count FROM students GROUP BY block,floor,room_number")
        return jsonify(cur.fetchall())
    finally:
        if cur: cur.close()
        conn.close()


@app.route('/api/allocate_room', methods=['POST'])
def allocate_room():
    conn = get_db()
    if not conn: return jsonify({'success': False, 'message': 'DB failed'}), 500
    cur = None
    try:
        d = request.get_json() or {}
        for f in ['student_id','name','roll_number','dept','year','phone','parent_name','parent_phone','block','floor','room_number']:
            if not str(d.get(f,'')).strip():
                return jsonify({'success': False, 'message': f'Missing: {f}'}), 400
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT COUNT(*) AS t FROM students WHERE block=%s AND floor=%s AND room_number=%s",
                    (d['block'],int(d['floor']),int(d['room_number'])))
        if cur.fetchone()['t'] >= 3: return jsonify({'success': False, 'message': 'Room is full!'}), 409
        cur.execute("SELECT student_id FROM students WHERE student_id=%s",(d['student_id'],))
        if cur.fetchone(): return jsonify({'success': False, 'message': 'Student ID exists!'}), 409
        cur.execute("SELECT roll_number FROM students WHERE roll_number=%s",(d['roll_number'],))
        if cur.fetchone(): return jsonify({'success': False, 'message': 'Roll number exists!'}), 409
        # Parent — find or create by phone
        cur.execute("SELECT parent_id FROM parents WHERE phone=%s",(d['parent_phone'].strip(),))
        par = cur.fetchone()
        if par:
            parent_id = par['parent_id']
        else:
            cur.execute("INSERT INTO parents(name,phone,relation) VALUES(%s,%s,%s)",
                        (d['parent_name'].strip(),d['parent_phone'].strip(),d.get('parent_relation','Parent')))
            parent_id = cur.lastrowid
        # Warden by year
        yr = d['year'].replace('st Year','').replace('nd Year','').replace('rd Year','').replace('th Year','').strip()
        cur.execute("SELECT warden_id FROM wardens WHERE year=%s LIMIT 1",(yr,))
        w = cur.fetchone(); warden_id = w['warden_id'] if w else None
        cur.execute("""INSERT INTO students(student_id,name,roll_number,dept,year,phone,block,floor,room_number,parent_id,warden_id)
                       VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                    (d['student_id'].strip(),d['name'].strip(),d['roll_number'].strip(),
                     d['dept'].strip(),d['year'].strip(),d['phone'].strip(),
                     d['block'].strip(),int(d['floor']),int(d['room_number']),parent_id,warden_id))
        conn.commit()
        return jsonify({'success': True, 'message': f"Room {d['room_number']} allocated to {d['name']}!"}), 201
    except mysql.connector.Error as err:
        conn.rollback()
        if err.errno==1062: return jsonify({'success': False, 'message': 'Duplicate entry.'}), 409
        return jsonify({'success': False, 'message': str(err)}), 500
    finally:
        if cur: cur.close()
        conn.close()


@app.route('/api/students', methods=['GET'])
def get_students():
    conn = get_db()
    if not conn: return jsonify({'error': 'DB failed'}), 500
    cur = None
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("""SELECT s.*,p.name AS parent_name,p.phone AS parent_phone
                       FROM students s LEFT JOIN parents p ON s.parent_id=p.parent_id ORDER BY s.created_at DESC""")
        rows = cur.fetchall()
        for r in rows: r['created_at']=str(r.get('created_at',''))
        return jsonify(rows)
    finally:
        if cur: cur.close()
        conn.close()


# ══════════════════ OUTPASS ══════════════════

@app.route('/api/outpass/apply', methods=['POST'])
def outpass_apply():
    conn = get_db()
    if not conn: return jsonify({'success': False, 'message': 'DB failed'}), 500
    cur = None
    try:
        d = request.get_json() or {}
        for f in ['student_id','destination','reason','leave_datetime','return_datetime']:
            if not str(d.get(f,'')).strip(): return jsonify({'success': False, 'message': f'Missing: {f}'}), 400
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT s.*,p.parent_id FROM students s LEFT JOIN parents p ON s.parent_id=p.parent_id WHERE s.student_id=%s",(d['student_id'],))
        stu = cur.fetchone()
        if not stu: return jsonify({'success': False, 'message': 'Student not found.'}), 404
        try:
            lv = datetime.strptime(d['leave_datetime'],'%Y-%m-%d %H:%M')
            rt = datetime.strptime(d['return_datetime'],'%Y-%m-%d %H:%M')
        except ValueError:
            return jsonify({'success': False, 'message': 'Date format: YYYY-MM-DD HH:MM'}), 400
        if rt <= lv: return jsonify({'success': False, 'message': 'Return must be after leave.'}), 400
        yr = stu['year'].replace('st Year','').replace('nd Year','').replace('rd Year','').replace('th Year','').strip()
        cur.execute("SELECT warden_id FROM wardens WHERE year=%s LIMIT 1",(yr,))
        w = cur.fetchone(); warden_id = w['warden_id'] if w else None
        cur.execute("""INSERT INTO outpasses(student_id,student_name,roll_number,dept,year,phone,block,
                       destination,reason,leave_datetime,return_datetime,status,parent_id,warden_id)
                       VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'PENDING',%s,%s)""",
                    (stu['student_id'],stu['name'],stu['roll_number'],stu['dept'],stu['year'],
                     stu['phone'],stu['block'],d['destination'].strip(),d['reason'].strip(),
                     lv,rt,stu.get('parent_id'),warden_id))
        conn.commit()
        return jsonify({'success': True, 'message': 'Outpass submitted! Pending parent approval.', 'outpass_id': cur.lastrowid}), 201
    except mysql.connector.Error as err:
        conn.rollback(); return jsonify({'success': False, 'message': str(err)}), 500
    finally:
        if cur: cur.close()
        conn.close()


@app.route('/api/outpass/student/<student_id>', methods=['GET'])
def outpass_student(student_id):
    conn = get_db()
    if not conn: return jsonify({'error': 'DB failed'}), 500
    cur = None
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("""SELECT o.*,p.name AS parent_name,w.name AS warden_name
                       FROM outpasses o LEFT JOIN parents p ON o.parent_id=p.parent_id
                       LEFT JOIN wardens w ON o.warden_id=w.warden_id
                       WHERE o.student_id=%s ORDER BY o.created_at DESC""",(student_id,))
        return jsonify([sr(r) for r in cur.fetchall()])
    finally:
        if cur: cur.close()
        conn.close()


@app.route('/api/outpass/parent/<int:parent_id>', methods=['GET'])
def outpass_parent(parent_id):
    conn = get_db()
    if not conn: return jsonify({'error': 'DB failed'}), 500
    cur = None
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("""SELECT o.*,p.name AS parent_name,w.name AS warden_name
                       FROM outpasses o LEFT JOIN parents p ON o.parent_id=p.parent_id
                       LEFT JOIN wardens w ON o.warden_id=w.warden_id
                       WHERE o.parent_id=%s ORDER BY o.created_at DESC""",(parent_id,))
        return jsonify([sr(r) for r in cur.fetchall()])
    finally:
        if cur: cur.close()
        conn.close()


@app.route('/api/outpass/parent/action', methods=['PUT'])
def parent_action():
    conn = get_db()
    if not conn: return jsonify({'success': False, 'message': 'DB failed'}), 500
    cur = None
    try:
        d=request.get_json() or {}
        oid=d.get('outpass_id'); pid=d.get('parent_id'); act=d.get('action','').upper(); rem=d.get('remarks','').strip()
        if not all([oid,pid,act]) or act not in ('APPROVE','REJECT'):
            return jsonify({'success': False, 'message': 'outpass_id, parent_id, action required.'}), 400
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM outpasses WHERE outpass_id=%s AND parent_id=%s",(int(oid),int(pid)))
        op = cur.fetchone()
        if not op: return jsonify({'success': False, 'message': 'Not found.'}), 404
        if op['status']!='PENDING': return jsonify({'success': False, 'message': f"Already: {op['status']}"}), 409
        ns = 'PARENT_APPROVED' if act=='APPROVE' else 'PARENT_REJECTED'
        cur.execute("UPDATE outpasses SET status=%s,parent_remarks=%s,parent_action_at=%s WHERE outpass_id=%s",
                    (ns,rem,datetime.now(),int(oid)))
        conn.commit()
        return jsonify({'success': True, 'message': f'Outpass {act.lower()}d.'})
    except mysql.connector.Error as err:
        conn.rollback(); return jsonify({'success': False, 'message': str(err)}), 500
    finally:
        if cur: cur.close()
        conn.close()


@app.route('/api/outpass/warden/<int:warden_id>', methods=['GET'])
def outpass_warden(warden_id):
    conn = get_db()
    if not conn: return jsonify({'error': 'DB failed'}), 500
    cur = None
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("""SELECT o.*,p.name AS parent_name,p.phone AS parent_phone
                       FROM outpasses o LEFT JOIN parents p ON o.parent_id=p.parent_id
                       WHERE o.warden_id=%s ORDER BY o.created_at DESC""",(warden_id,))
        return jsonify([sr(r) for r in cur.fetchall()])
    finally:
        if cur: cur.close()
        conn.close()


@app.route('/api/outpass/warden/action', methods=['PUT'])
def warden_action():
    conn = get_db()
    if not conn: return jsonify({'success': False, 'message': 'DB failed'}), 500
    cur = None
    try:
        d=request.get_json() or {}
        oid=d.get('outpass_id'); wid=d.get('warden_id'); act=d.get('action','').upper(); rem=d.get('remarks','').strip()
        if not all([oid,wid,act]) or act not in ('APPROVE','REJECT'):
            return jsonify({'success': False, 'message': 'outpass_id, warden_id, action required.'}), 400
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM outpasses WHERE outpass_id=%s AND warden_id=%s",(int(oid),int(wid)))
        op = cur.fetchone()
        if not op: return jsonify({'success': False, 'message': 'Not found.'}), 404
        if op['status']!='PARENT_APPROVED': return jsonify({'success': False, 'message': f"Status: {op['status']}"}), 409
        ns = 'WARDEN_APPROVED' if act=='APPROVE' else 'WARDEN_REJECTED'
        cur.execute("UPDATE outpasses SET status=%s,warden_remarks=%s,warden_action_at=%s WHERE outpass_id=%s",
                    (ns,rem,datetime.now(),int(oid)))
        conn.commit()
        return jsonify({'success': True, 'message': f'Outpass {act.lower()}d.'})
    except mysql.connector.Error as err:
        conn.rollback(); return jsonify({'success': False, 'message': str(err)}), 500
    finally:
        if cur: cur.close()
        conn.close()


@app.route('/api/outpass/watchman', methods=['GET'])
def outpass_watchman():
    conn = get_db()
    if not conn: return jsonify({'error': 'DB failed'}), 500
    cur = None
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("""SELECT o.*,w.name AS warden_name FROM outpasses o
                       LEFT JOIN wardens w ON o.warden_id=w.warden_id
                       WHERE o.status='WARDEN_APPROVED' ORDER BY o.leave_datetime""")
        return jsonify([sr(r) for r in cur.fetchall()])
    finally:
        if cur: cur.close()
        conn.close()


@app.route('/api/outpass/watchman/log', methods=['PUT'])
def watchman_log():
    conn = get_db()
    if not conn: return jsonify({'success': False, 'message': 'DB failed'}), 500
    cur = None
    try:
        d=request.get_json() or {}
        oid=d.get('outpass_id'); act=d.get('action','').upper(); note=d.get('note','').strip()
        if not oid or act not in ('EXIT','ENTRY'): return jsonify({'success': False, 'message': 'outpass_id + EXIT/ENTRY required.'}), 400
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT status FROM outpasses WHERE outpass_id=%s",(int(oid),))
        op=cur.fetchone()
        if not op: return jsonify({'success': False, 'message': 'Not found.'}), 404
        if op['status']!='WARDEN_APPROVED': return jsonify({'success': False, 'message': 'Not approved.'}), 409
        now=datetime.now()
        if act=='EXIT':
            cur.execute("UPDATE outpasses SET exit_time=%s,watchman_note=%s WHERE outpass_id=%s",(now,note,int(oid)))
            msg='Exit logged.'
        else:
            cur.execute("UPDATE outpasses SET entry_time=%s,watchman_note=%s WHERE outpass_id=%s",(now,note,int(oid)))
            msg='Return logged.'
        conn.commit()
        return jsonify({'success': True, 'message': msg})
    except mysql.connector.Error as err:
        conn.rollback(); return jsonify({'success': False, 'message': str(err)}), 500
    finally:
        if cur: cur.close()
        conn.close()


@app.route('/api/outpass/all', methods=['GET'])
def outpass_all():
    conn = get_db()
    if not conn: return jsonify({'error': 'DB failed'}), 500
    cur = None
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("""SELECT o.*,p.name AS parent_name,p.phone AS parent_phone,w.name AS warden_name
                       FROM outpasses o LEFT JOIN parents p ON o.parent_id=p.parent_id
                       LEFT JOIN wardens w ON o.warden_id=w.warden_id ORDER BY o.created_at DESC""")
        return jsonify([sr(r) for r in cur.fetchall()])
    finally:
        if cur: cur.close()
        conn.close()


if __name__ == '__main__':
    print("\n" + "="*55)
    print("  HOSTEL MANAGEMENT v2 — http://localhost:5000")
    print("  Admin: username=admin  password=admin123")
    print("="*55+"\n")
    app.run(debug=True, port=5000)
