import sqlite3
from pathlib import Path
from datetime import date, timedelta
import bcrypt

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "team_tasks.db"

def get_conn():
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_conn()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash BLOB NOT NULL,
        role TEXT NOT NULL DEFAULT 'Member',
        avatar TEXT DEFAULT '👤',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS teams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        description TEXT DEFAULT '',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS team_members (
        team_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        joined_at TEXT DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY(team_id, user_id),
        FOREIGN KEY(team_id) REFERENCES teams(id) ON DELETE CASCADE,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
    );

    CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT DEFAULT '',
        status TEXT NOT NULL DEFAULT 'To Do',
        priority TEXT NOT NULL DEFAULT 'Medium',
        assignee_id INTEGER,
        team_id INTEGER,
        due_date TEXT,
        estimate_hours REAL DEFAULT 0,
        labels TEXT DEFAULT '',
        created_by INTEGER,
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(assignee_id) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY(team_id) REFERENCES teams(id) ON DELETE SET NULL,
        FOREIGN KEY(created_by) REFERENCES users(id) ON DELETE SET NULL
    );

    CREATE TABLE IF NOT EXISTS activity (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action TEXT NOT NULL,
        task_id INTEGER,
        details TEXT DEFAULT '',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL,
        FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE SET NULL
    );
    """)
    conn.commit()
    conn.close()

def seed_demo():
    conn = get_conn()
    count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    if count:
        conn.close()
        return

    users = [
        ("Admin User", "admin@demo.com", "Admin@123", "Admin", "🛡️"),
        ("Maya Manager", "manager@demo.com", "Manager@123", "Manager", "👩‍💼"),
        ("Alex Developer", "developer@demo.com", "Developer@123", "Developer", "👨‍💻"),
        ("Priya Designer", "priya@demo.com", "Designer@123", "Designer", "🎨"),
        ("Rahul QA", "rahul@demo.com", "QA@123", "QA", "🧪"),
    ]
    for name, email, password, role, avatar in users:
        ph = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        conn.execute("INSERT INTO users(name,email,password_hash,role,avatar) VALUES(?,?,?,?,?)",
                     (name,email,ph,role,avatar))

    conn.execute("INSERT INTO teams(name,description) VALUES(?,?)",
                 ("Product Engineering", "Main product delivery team"))
    team_id = conn.execute("SELECT id FROM teams LIMIT 1").fetchone()[0]
    user_ids = {r["email"]: r["id"] for r in conn.execute("SELECT id,email FROM users")}
    for uid in user_ids.values():
        conn.execute("INSERT INTO team_members(team_id,user_id) VALUES(?,?)", (team_id, uid))

    today = date.today()
    tasks = [
        ("Design dashboard wireframes", "Create desktop and mobile dashboard wireframes.", "In Progress", "High", user_ids["priya@demo.com"], team_id, str(today+timedelta(days=2)), 8, "design,ui"),
        ("Build authentication API", "Implement login, logout and password validation.", "Review", "Critical", user_ids["developer@demo.com"], team_id, str(today+timedelta(days=1)), 12, "backend,auth"),
        ("Write test cases", "Prepare regression and smoke test coverage.", "To Do", "Medium", user_ids["rahul@demo.com"], team_id, str(today+timedelta(days=5)), 6, "qa,testing"),
        ("Project requirements", "Finalize MVP scope and acceptance criteria.", "Done", "High", user_ids["manager@demo.com"], team_id, str(today-timedelta(days=2)), 4, "planning"),
        ("Setup CI pipeline", "Configure automated checks for pull requests.", "Backlog", "Low", user_ids["developer@demo.com"], team_id, str(today+timedelta(days=8)), 5, "devops"),
    ]
    for t in tasks:
        conn.execute("""INSERT INTO tasks(title,description,status,priority,assignee_id,team_id,due_date,estimate_hours,labels,created_by)
                        VALUES(?,?,?,?,?,?,?,?,?,?)""", (*t, user_ids["manager@demo.com"]))
    conn.execute("INSERT INTO activity(user_id,action,details) VALUES(?,?,?)",
                 (user_ids["manager@demo.com"], "System initialized", "Demo workspace created"))
    conn.commit()
    conn.close()
