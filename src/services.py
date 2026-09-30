import sqlite3
import pandas as pd
from datetime import date, datetime
from .db import get_conn

STATUSES = ["Backlog", "To Do", "In Progress", "Review", "Done"]
PRIORITIES = ["Low", "Medium", "High", "Critical"]

def df_query(sql, params=()):
    conn = get_conn()
    df = pd.read_sql_query(sql, conn, params=params)
    conn.close()
    return df

def users_df():
    return df_query("SELECT id,name,email,role,avatar FROM users ORDER BY name")

def teams_df():
    return df_query("SELECT * FROM teams ORDER BY name")

def tasks_df():
    return df_query("""
    SELECT t.*, u.name assignee_name, u.avatar assignee_avatar, tm.name team_name
    FROM tasks t
    LEFT JOIN users u ON u.id=t.assignee_id
    LEFT JOIN teams tm ON tm.id=t.team_id
    ORDER BY CASE t.status WHEN 'In Progress' THEN 1 WHEN 'Review' THEN 2 WHEN 'To Do' THEN 3 WHEN 'Backlog' THEN 4 ELSE 5 END,
             CASE t.priority WHEN 'Critical' THEN 1 WHEN 'High' THEN 2 WHEN 'Medium' THEN 3 ELSE 4 END,
             t.due_date
    """)

def add_task(data, user_id):
    conn = get_conn()
    cur = conn.execute("""INSERT INTO tasks(title,description,status,priority,assignee_id,team_id,due_date,estimate_hours,labels,created_by)
                          VALUES(?,?,?,?,?,?,?,?,?,?)""",
                       (data["title"],data["description"],data["status"],data["priority"],data["assignee_id"],
                        data["team_id"],data["due_date"],data["estimate_hours"],data["labels"],user_id))
    task_id = cur.lastrowid
    conn.execute("INSERT INTO activity(user_id,action,task_id,details) VALUES(?,?,?,?)",
                 (user_id,"Created task",task_id,data["title"]))
    conn.commit(); conn.close()
    return task_id

def update_task(task_id, data, user_id):
    conn = get_conn()
    old = conn.execute("SELECT status,title FROM tasks WHERE id=?", (task_id,)).fetchone()
    conn.execute("""UPDATE tasks SET title=?,description=?,status=?,priority=?,assignee_id=?,team_id=?,
                    due_date=?,estimate_hours=?,labels=?,updated_at=CURRENT_TIMESTAMP WHERE id=?""",
                 (data["title"],data["description"],data["status"],data["priority"],data["assignee_id"],
                  data["team_id"],data["due_date"],data["estimate_hours"],data["labels"],task_id))
    details = f'{data["title"]} | status: {old["status"] if old else "?"} → {data["status"]}'
    conn.execute("INSERT INTO activity(user_id,action,task_id,details) VALUES(?,?,?,?)",
                 (user_id,"Updated task",task_id,details))
    conn.commit(); conn.close()

def set_status(task_id, status, user_id):
    conn = get_conn()
    row = conn.execute("SELECT title,status FROM tasks WHERE id=?", (task_id,)).fetchone()
    if row and row["status"] != status:
        conn.execute("UPDATE tasks SET status=?,updated_at=CURRENT_TIMESTAMP WHERE id=?", (status,task_id))
        conn.execute("INSERT INTO activity(user_id,action,task_id,details) VALUES(?,?,?,?)",
                     (user_id,"Changed status",task_id,f'{row["title"]}: {row["status"]} → {status}'))
        conn.commit()
    conn.close()

def delete_task(task_id, user_id):
    conn = get_conn()
    row = conn.execute("SELECT title FROM tasks WHERE id=?", (task_id,)).fetchone()
    conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
    conn.execute("INSERT INTO activity(user_id,action,details) VALUES(?,?,?)",
                 (user_id,"Deleted task",f"Task #{task_id}: {row['title'] if row else ''}"))
    conn.commit(); conn.close()

def add_team(name, description, user_id):
    conn = get_conn()
    try:
        cur = conn.execute("INSERT INTO teams(name,description) VALUES(?,?)", (name.strip(),description.strip()))
        tid = cur.lastrowid
        conn.execute("INSERT INTO team_members(team_id,user_id) VALUES(?,?)", (tid,user_id))
        conn.execute("INSERT INTO activity(user_id,action,details) VALUES(?,?,?)",
                     (user_id,"Created team",name.strip()))
        conn.commit()
        return True, None
    except sqlite3.IntegrityError:
        return False, "A team with this name already exists."
    finally:
        conn.close()

def add_member(team_id, user_id, actor_id):
    conn = get_conn()
    try:
        conn.execute("INSERT OR IGNORE INTO team_members(team_id,user_id) VALUES(?,?)", (team_id,user_id))
        conn.execute("INSERT INTO activity(user_id,action,details) VALUES(?,?,?)",
                     (actor_id,"Added team member",f"user #{user_id} to team #{team_id}"))
        conn.commit()
        return True
    finally:
        conn.close()

def team_members_df(team_id):
    return df_query("""SELECT u.id,u.name,u.email,u.role,u.avatar
                       FROM team_members m JOIN users u ON u.id=m.user_id
                       WHERE m.team_id=? ORDER BY u.name""", (team_id,))

def activity_df():
    return df_query("""SELECT a.*, u.name user_name, t.title task_title
                       FROM activity a
                       LEFT JOIN users u ON u.id=a.user_id
                       LEFT JOIN tasks t ON t.id=a.task_id
                       ORDER BY a.created_at DESC LIMIT 250""")

def kpis():
    df = tasks_df()
    total = len(df)
    done = int((df.status == "Done").sum()) if total else 0
    overdue = int(((pd.to_datetime(df.due_date, errors="coerce").dt.date < date.today()) & (df.status != "Done")).sum()) if total else 0
    return total, done, overdue, round(done/total*100,1) if total else 0
