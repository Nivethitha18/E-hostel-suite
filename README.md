# 🏢 Hostel Management System — Complete Setup Guide

## 📁 Project Structure
```
hostel_management/
│
├── index.html       ← Frontend (all HTML + CSS + JavaScript in one file)
├── app.py           ← Python backend (Flask web server + MySQL connection)
├── database.sql     ← MySQL database setup (run this once)
├── requirements.txt ← Python packages to install
└── README.md        ← This guide
```

---

## 🛠️ STEP 1 — Install Required Software

Before starting, make sure these are installed on your computer:

### A. Python (version 3.8 or above)
- Download from: https://www.python.org/downloads/
- During installation, **tick the box** that says "Add Python to PATH"

### B. MySQL
- Download MySQL Community Server from: https://dev.mysql.com/downloads/mysql/
- Also install **MySQL Workbench** (a visual tool to manage your database)
- Remember the **root password** you set during installation

### C. VS Code (Code Editor)
- Download from: https://code.visualstudio.com/
- Install the **Python extension** from VS Code marketplace

---

## 🗄️ STEP 2 — Set Up the MySQL Database

### Open MySQL Workbench and run these steps:

1. Open **MySQL Workbench** → connect using your root password
2. Click the **SQL editor** (the + tab icon)
3. Open the file `database.sql` from this project folder
4. Click the **⚡ (lightning bolt)** button to run all the SQL commands
5. You should see `hostel_db` appear in the left panel under "Schemas"

### What the database creates:
- `wardens` table — stores hostel warden details
- `parents` table — stores parent/guardian contact info  
- `students` table — stores student + room allocation data (linked to wardens and parents via Foreign Keys)
- `complaints` table — stores student complaints (linked to students)

---

## 📦 STEP 3 — Install Python Packages

### Open VS Code, then open a Terminal inside VS Code:
`View → Terminal` (or press Ctrl + `)

```bash
# Navigate to your project folder (change path as needed)
cd path/to/hostel_management

# Install all required Python packages at once
pip install -r requirements.txt
```

This installs:
- **flask** — the web server framework
- **flask-cors** — allows HTML to talk to Flask
- **mysql-connector-python** — connects Python to MySQL

---

## ⚙️ STEP 4 — Configure Your Database Password

Open `app.py` in VS Code and find this section near the top:

```python
DB_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'your_password',   ← CHANGE THIS LINE
    'database': 'hostel_db'
}
```

Replace `'your_password'` with your actual MySQL root password. Save the file.

---

## 🚀 STEP 5 — Run the Project

### In the VS Code Terminal:
```bash
python app.py
```

You should see:
```
==================================================
 Hostel Management System - Backend Running
 Open http://localhost:5000 in your browser
==================================================
 * Running on http://127.0.0.1:5000
```

### Open your browser and go to:
```
http://localhost:5000
```

The website will load and show two big rectangles for D Block and L Block.

---

## 🖥️ HOW TO USE THE WEBSITE

### Main Page:
- You see two big building cards: **D Block** and **L Block**
- Each card has 3 floor buttons: Ground Floor, First Floor, Second Floor
- Each button shows **Vacant** and **Filled** room counts

### Floor View:
- Click any floor button → the page shows **29 rooms in a zigzag pattern**
- 🟢 Green room = vacant beds available (click to allocate)
- 🟡 Yellow room = partially filled (click to allocate more)
- 🔴 Red room = completely full (no click)
- Each room shows: number of vacant spots (V) and filled spots (F)

### Room Allocation:
- Click a green or yellow room → a form pops up
- Fill in: Student ID, Roll Number, Name, Department, Year, Phone
- Click **"Allocate Room"** → data is saved to MySQL database
- Room status updates automatically on screen

---

## 🔗 HOW THE PARTS CONNECT (Architecture)

```
Browser (index.html)
       │
       │ fetch('/api/room_stats')    ← GET request to load room data
       │ fetch('/api/allocate_room') ← POST request to save student
       ↓
Flask Server (app.py running on port 5000)
       │
       │ SELECT / INSERT SQL queries
       ↓
MySQL Database (hostel_db)
       ├── wardens   ← warden_id is FK in students table
       ├── parents   ← parent_id is FK in students table
       ├── students  ← main table with room allocation data
       └── complaints ← student_id is FK from students table
```

**Foreign Key explained simply:**
- A Foreign Key is like a reference. In `students` table, `warden_id` is a FK that points to the `wardens` table. This means every student must belong to a valid warden. The database will reject any student entry with a warden_id that doesn't exist in the wardens table.

---

## 🔧 LINE-BY-LINE CODE EXPLANATION

### index.html — Key JavaScript Functions:

```javascript
initRoomData()
// Creates an empty data structure in memory for all 6 floors
// roomData['D'][0][5] = { students: 2 }
//           ↑  ↑  ↑
//         block floor room

loadRoomStats()
// Fetches /api/room_stats from Flask
// Gets how many students are in each room from MySQL
// Updates the Vacant/Filled badges on main page

openFloor('D', 'Ground Floor', 0)
// Called when you click a floor button
// Hides the main building view
// Calls renderRooms() to draw 29 room boxes

renderRooms(block, floorIndex)
// Draws 29 room buttons in a ZIGZAG pattern
// Zigzag = rows of 5, alternating with a left offset
// Row 1: no offset, Row 2: shifted right, Row 3: no offset...
// Each room shows green/yellow/red based on occupancy

openModal(block, floorIndex, roomNum)
// Opens the student registration popup
// Pre-fills the Block and Room Number fields

submitForm(event)
// Collects form data
// Sends POST request to /api/allocate_room in Flask
// On success: updates room color + shows toast notification
```

### app.py — Key Routes:

```python
@app.route('/api/room_stats')
# Returns JSON list of rooms with student counts
# Frontend uses this to show vacancy numbers

@app.route('/api/allocate_room', methods=['POST'])
# 1. Checks if room already has 3 students (full)
# 2. Checks if student_id already exists
# 3. If both checks pass, INSERT into MySQL
# 4. Returns success/failure JSON to frontend
```

---

## ➕ FEATURES YOU CAN ADD NEXT

1. **Warden Login Panel** — separate admin page to view all students, manage complaints
2. **Parent Portal** — parents can view their child's room info and submit queries
3. **Complaint System** — students submit maintenance complaints, wardens resolve them
4. **Checkout / Vacate Room** — remove a student from a room when they leave
5. **Student Dashboard** — each student can login and see their room, messmates, complaints
6. **Mess Fee Tracking** — track monthly mess fees and payment status per student
7. **Visitor Log** — record when outsiders visit a student (security feature)
8. **Export to PDF/Excel** — download list of students per floor for records
9. **Email Notifications** — send room allocation confirmation to student/parent email
10. **Search & Filter** — search student by name, roll number, or room number

---

## ❓ TROUBLESHOOTING

| Problem | Solution |
|---|---|
| `ModuleNotFoundError: flask` | Run `pip install -r requirements.txt` again |
| `Access denied for user 'root'` | Check your MySQL password in `DB_CONFIG` in app.py |
| `Unknown database 'hostel_db'` | Run `database.sql` in MySQL Workbench first |
| Website shows `--` for room counts | Backend not running; start with `python app.py` |
| Port 5000 already in use | Change `port=5000` to `port=5001` in app.py, then visit `localhost:5001` |
| Form submitted but data not saved | Check terminal for error messages in app.py |
