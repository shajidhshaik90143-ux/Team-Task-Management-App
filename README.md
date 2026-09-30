# Team Task Management App

A production-style local team productivity platform built with Python, Streamlit, SQLite, Pandas and Plotly.

## Features
- Secure registration/login with bcrypt password hashing
- Demo accounts and automatic SQLite database
- Team members and role management
- Create, edit and delete tasks
- Assign tasks to team members
- Priority, status, labels, due dates and estimates
- Kanban board: Backlog → To Do → In Progress → Review → Done
- Search and multi-filter task management
- Dashboard with KPIs and workload overview
- Analytics: status, priority, workload and completion trend
- Activity/audit log
- Responsive Streamlit interface
- No external database required

## Demo Accounts
- Admin: `admin@demo.com` / `Admin@123`
- Manager: `manager@demo.com` / `Manager@123`
- Developer: `developer@demo.com` / `Developer@123`

## Run on Windows PowerShell
```powershell
cd "Team Task Management App"
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

If PowerShell blocks activation:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

Then open:
`http://localhost:8501`

## Database
SQLite is stored in `data/team_tasks.db` and is created automatically.

To reset the demo database, stop Streamlit and delete:
`data/team_tasks.db`

## Project Structure
```text
Team Task Management App/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
├── .streamlit/
│   └── config.toml
├── data/
│   └── .gitkeep
└── src/
    ├── __init__.py
    ├── auth.py
    ├── db.py
    ├── services.py
    └── ui.py
```
