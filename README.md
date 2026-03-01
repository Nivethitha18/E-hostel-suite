# 🏢 Hostel Management System
For admin login use uname="admin" pass="admin123"

A full-stack web application for managing hostel room allocations, students, wardens, and parent records.

---

## 📁 Project Folder Structure

```
hostel_management/
│
├── index.html          ← Frontend  (HTML + CSS + JavaScript — all in one file)
├── app.py              ← Backend   (Python Flask web server + MySQL API)
├── database.sql        ← Database  (MySQL schema — run this once)
├── requirements.txt    ← Python packages list
└── README.md           ← This guide
```

---

## 🛠️ SOFTWARE TO INSTALL FIRST

### 1. Python 3.x
- Download: https://www.python.org/downloads/
- ⚠️ During install → tick **"Add Python to PATH"** checkbox

### 2. MySQL + MySQL Workbench
- Download: https://dev.mysql.com/downloads/installer/
- Choose **Developer Default** setup
- Set a root password (e.g. `root123`) — remember it!

### 3. VS Code
- Download: https://code.visualstudio.com/

---

## 🗄️ STEP 1 — Set Up the Database

1. Open **MySQL Workbench**
2. Connect using your root password
3. Click **File → Open SQL Script** → select `database.sql`
4. Press **Ctrl + Shift + Enter** to run it
5. You should see ✅ green ticks — `hostel_db` is now created with 4 tables

**Tables created:**
| Table | Purpose |
|---|---|
| `wardens` | Stores warden details for D and L blocks |
| `parents` | Stores parent/guardian contact information |
| `students` | Main table — room allocations + FK links to wardens & parents |
| `complaints` | Student complaints linked to students table |

---

## ⚙️ STEP 2 — Configure Your Password

Open `app.py` in VS Code and find this section at the top:

```python
DB_CONFIG = {
    'host':     '127.0.0.1',
    'port':     3306,
    'user':     'root',
    'password': 'Mysql@123',   ← CHANGE THIS to your MySQL password
    'database': 'hostel_db'
}
```

Press **Ctrl + S** to save.

---

## 📦 STEP 3 — Install Python Packages

Open VS Code → open Terminal (Ctrl + `) → type:

```bash
python -m pip install -r requirements.txt
```

This installs:
- **flask** — web server framework
- **flask-cors** — allows HTML to talk to Flask
- **mysql-connector-python** — connects Python to MySQL

---

## ▶️ STEP 4 — Run the Project

In the VS Code terminal:

```bash
python app.py
```

You will see:

```
=======================================================
   HOSTEL MANAGEMENT SYSTEM — Backend Running
   Open  →  http://localhost:5000
=======================================================
  Routes available:
  GET  /api/wardens       — list all wardens
  POST /api/add_warden    — add new warden
  PUT  /api/update_warden — update warden
  DEL  /api/delete_warden — delete warden
  GET  /api/room_stats    — room occupancy
  POST /api/allocate_room — register student
  GET  /api/students      — all students
=======================================================
```

Open your browser and go to:
```
http://localhost:5000
```

---

## 🖥️ HOW TO USE THE WEBSITE

### Home Page
- Big "Welcome to Hostel Management" screen appears
- Two quick-action cards: **Room Allocation** and **Add Warden**
- Top-right corner has a ☰ menu button with same options

### Room Allocation
- Shows **D Block** and **L Block** as two big cards
- Each block has 3 floor buttons (Ground / First / Second Floor)
- Each floor button shows **Vacant** and **Filled** room counts
- Click any floor → see **Left Wing** and **Right Wing** rectangles
- Rooms are numbered sequentially:
  - Ground Floor: Rooms 1–29 (Left: 1–15, Right: 16–29)
  - First Floor: Rooms 30–58 (Left: 30–44, Right: 45–58)
  - Second Floor: Rooms 59–87 (Left: 59–73, Right: 74–87)
- 🟢 Green room = vacant (click to allocate)
- 🟡 Yellow room = partially filled (click to add more)
- 🔴 Red room = full (not clickable)

### Student Form (when clicking a room)
- **Student Details**: ID, Roll Number, Name, Department, Year, Phone
- **Parent Details**: Parent ID, Parent Name, Parent Phone, Relation
- **Room Details**: Auto-filled (Block, Floor, Room Number)

### Add Warden Page
- Fill: Name, Email, Phone, Block (D or L)
- Existing wardens list shown below the form
- Validates for duplicate email before saving

---

## 🔗 HOW FRONTEND ↔ FLASK ↔ MYSQL CONNECTS

```
Browser (index.html)
    |
    |── GET  /api/room_stats ──────→ Flask reads students table
    |                                returns room occupancy JSON
    |
    |── POST /api/allocate_room ──→ Flask validates data
    |                                inserts parent (if new)
    |                                inserts student with parent FK
    |                                returns success/error
    |
    |── GET  /api/wardens ─────────→ Flask reads wardens table
    |                                returns warden list JSON
    |
    |── POST /api/add_warden ──────→ Flask validates
    |                                checks duplicate email
    |                                inserts into wardens table
    |                                returns success/error
    ↓
MySQL Database (hostel_db)
    ├── wardens    ← warden_id is FK in students table
    ├── parents    ← parent_id is FK in students table
    ├── students   ← main room allocation data
    └── complaints ← student_id is FK from students
```

---

## 🔁 EVERY TIME YOU WANT TO USE THE PROJECT

You only need 2 steps after first setup:

1. Open VS Code terminal → run:
```bash
python app.py
```

2. Open browser → go to:
```
http://localhost:5000
```

---

## ❌ TROUBLESHOOTING

| Error | Cause | Fix |
|---|---|---|
| `pip not recognized` | Python not in PATH | Use `python -m pip install -r requirements.txt` |
| `Access denied for user 'root'` | Wrong password in app.py | Update `DB_CONFIG` password in app.py |
| `Unknown database 'hostel_db'` | database.sql not run | Run database.sql in MySQL Workbench |
| `Can't connect to MySQL server` | MySQL not running | Open Services → Start MySQL80 |
| `ModuleNotFoundError: flask` | Packages not installed | Run `python -m pip install -r requirements.txt` |
| Website shows `--` for room counts | Flask not running | Run `python app.py` first |
| Red dot in navbar | Backend offline | Start Flask with `python app.py` |
| `Email already registered` | Duplicate warden email | Use a different email for the warden |
| Port 5000 already in use | Another app using port | Change `port=5000` to `port=5001` in app.py and visit `localhost:5001` |

---

## 🔮 FEATURES TO ADD NEXT

1. **Student Login** — students log in to see their own room details
2. **Warden Dashboard** — wardens can view all students in their block
3. **Complaints System** — students submit maintenance complaints
4. **Checkout / Vacate** — remove student when they leave
5. **Mess Fee Tracking** — record monthly fee payments
6. **PDF Reports** — download floor-wise student lists
7. **Email Notifications** — send room allocation emails
8. **Search & Filter** — find students by name, room, or department
9. **Parent Portal** — parents view their child's room info
10. **Visitor Log** — record hostel visitors for security

---

## 📊 DATABASE FOREIGN KEY RELATIONSHIPS

```
wardens (warden_id PK)
    ↑ FK (warden_id)
students (student_id PK) ──── FK (parent_id) ──→ parents (parent_id PK)
    ↑ FK (student_id)
complaints (complaint_id PK)
```

- Every **student** can be linked to one **warden** (optional)
- Every **student** can be linked to one **parent** (required when allocating)
- Every **complaint** must belong to an existing **student**
- Deleting a warden sets `warden_id = NULL` in students (safe delete)
- Deleting a student also deletes their complaints (cascade delete)
