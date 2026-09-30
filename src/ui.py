import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import date, timedelta
from .services import *

def inject_css():
    st.markdown("""
    <style>
    .block-container{padding-top:1.5rem;max-width:1400px}
    .kpi{background:white;border:1px solid #e5e7eb;border-radius:16px;padding:18px 20px;box-shadow:0 2px 8px rgba(15,23,42,.04)}
    .kpi .label{font-size:13px;color:#64748b}.kpi .value{font-size:30px;font-weight:800;margin-top:3px}
    .task-card{background:white;border:1px solid #e5e7eb;border-radius:14px;padding:14px;margin-bottom:10px}
    .muted{color:#64748b;font-size:13px}
    </style>
    """, unsafe_allow_html=True)

def render_sidebar():
    inject_css()
    u = st.session_state.user
    with st.sidebar:
        st.markdown("# ✅ TaskFlow")
        st.caption("Team Task Management")
        st.divider()
        pages = ["Dashboard","Tasks","Kanban Board","Team","Analytics","Activity"]
        current = st.session_state.get("page","Dashboard")
        for p in pages:
            if st.button(p, use_container_width=True, type="primary" if current==p else "secondary"):
                st.session_state.page = p
                st.rerun()
        st.divider()
        st.markdown(f"**{u['avatar']} {u['name']}**")
        st.caption(f"{u['role']} · {u['email']}")
        if st.button("Log out", use_container_width=True):
            st.session_state.user = None
            st.rerun()

def kpi_card(label, value, icon):
    st.markdown(f'<div class="kpi"><div class="label">{icon} {label}</div><div class="value">{value}</div></div>', unsafe_allow_html=True)

def render_dashboard():
    st.title("Dashboard")
    st.caption(f"Welcome back, {st.session_state.user['name'].split()[0]}. Here is your team at a glance.")
    total, done, overdue, rate = kpis()
    df = tasks_df()
    c1,c2,c3,c4 = st.columns(4)
    with c1: kpi_card("Total tasks", total, "📋")
    with c2: kpi_card("Completed", done, "✅")
    with c3: kpi_card("Overdue", overdue, "⚠️")
    with c4: kpi_card("Completion rate", f"{rate}%", "📈")
    st.write("")
    left,right = st.columns([1.25,.75])
    with left:
        st.subheader("Work status")
        if len(df):
            counts = df["status"].value_counts().reindex(STATUSES, fill_value=0).reset_index()
            counts.columns=["Status","Tasks"]
            fig=px.bar(counts,x="Status",y="Tasks",text="Tasks")
            fig.update_layout(height=330,margin=dict(l=10,r=10,t=10,b=10))
            st.plotly_chart(fig,use_container_width=True)
    with right:
        st.subheader("Upcoming deadlines")
        upcoming = df[(df.status!="Done") & df.due_date.notna()].copy()
        if len(upcoming):
            upcoming["Due"] = pd.to_datetime(upcoming.due_date).dt.strftime("%d %b")
            for _,r in upcoming.sort_values("due_date").head(6).iterrows():
                st.markdown(f"**{r.title}**  \n<span class='muted'>{r.assignee_avatar or '👤'} {r.assignee_name or 'Unassigned'} · {r.Due}</span>", unsafe_allow_html=True)
                st.divider()
        else: st.info("No upcoming deadlines.")
    st.subheader("My assigned work")
    mine = df[df.assignee_id == st.session_state.user["id"]]
    if len(mine):
        st.dataframe(mine[["title","status","priority","due_date","estimate_hours","team_name"]], hide_index=True, use_container_width=True)
    else: st.info("No tasks assigned to you.")

def task_editor(task=None, key="task"):
    users = users_df(); teams = teams_df()
    is_edit = task is not None
    with st.form(f"{key}_{task['id'] if is_edit else 'new'}"):
        title = st.text_input("Task title", value=task["title"] if is_edit else "", placeholder="e.g. Implement user profile")
        desc = st.text_area("Description", value=task["description"] if is_edit else "", height=90)
        a,b,c = st.columns(3)
        with a:
            status = st.selectbox("Status", STATUSES, index=STATUSES.index(task["status"]) if is_edit and task["status"] in STATUSES else 1)
            priority = st.selectbox("Priority", PRIORITIES, index=PRIORITIES.index(task["priority"]) if is_edit and task["priority"] in PRIORITIES else 1)
        with b:
            user_options = ["Unassigned"] + [f"{r['avatar']} {r['name']} (#{r['id']})" for _,r in users.iterrows()]
            current = next((i for i,x in enumerate(user_options) if is_edit and f"(#{task['assignee_id']})" in x),0)
            assignee_label = st.selectbox("Assignee", user_options, index=current)
            assignee_id = None if assignee_label=="Unassigned" else int(assignee_label.split("#")[-1].rstrip(")"))
        with c:
            team_options = ["No team"] + [f"{r['name']} (#{r['id']})" for _,r in teams.iterrows()]
            current = next((i for i,x in enumerate(team_options) if is_edit and f"(#{task['team_id']})" in x),0)
            team_label = st.selectbox("Team", team_options, index=current)
            team_id = None if team_label=="No team" else int(team_label.split("#")[-1].rstrip(")"))
        d,e = st.columns(2)
        with d:
            due = st.date_input("Due date", value=pd.to_datetime(task["due_date"]).date() if is_edit and task["due_date"] else date.today()+timedelta(days=7))
        with e:
            estimate = st.number_input("Estimate (hours)", min_value=0.0, max_value=1000.0, value=float(task["estimate_hours"] if is_edit else 2), step=.5)
        labels = st.text_input("Labels", value=task["labels"] if is_edit else "", placeholder="frontend, api, urgent")
        submitted = st.form_submit_button("Update Task" if is_edit else "Create Task", type="primary", use_container_width=True)
    if submitted:
        if not title.strip():
            st.error("Task title is required.")
            return False
        data={"title":title.strip(),"description":desc.strip(),"status":status,"priority":priority,"assignee_id":assignee_id,
              "team_id":team_id,"due_date":str(due),"estimate_hours":estimate,"labels":labels.strip()}
        if is_edit: update_task(task["id"],data,st.session_state.user["id"])
        else: add_task(data,st.session_state.user["id"])
        st.success("Task saved.")
        st.rerun()
    return False

def render_tasks():
    st.title("Tasks")
    df=tasks_df()
    top1,top2=st.columns([1,5])
    with top1:
        if st.button("＋ New Task", type="primary", use_container_width=True):
            st.session_state.new_task=True
    if st.session_state.get("new_task"):
        with st.expander("Create a new task", expanded=True):
            task_editor(key="create")
        if st.button("Cancel creation"): st.session_state.new_task=False; st.rerun()
    st.divider()
    a,b,c,d = st.columns(4)
    search=a.text_input("Search", placeholder="Task title...")
    status=b.multiselect("Status", STATUSES)
    priority=c.multiselect("Priority", PRIORITIES)
    assignees=d.multiselect("Assignee", sorted(df.assignee_name.dropna().unique()) if len(df) else [])
    filtered=df.copy()
    if search: filtered=filtered[filtered.title.str.contains(search,case=False,na=False)]
    if status: filtered=filtered[filtered.status.isin(status)]
    if priority: filtered=filtered[filtered.priority.isin(priority)]
    if assignees: filtered=filtered[filtered.assignee_name.isin(assignees)]
    st.caption(f"Showing {len(filtered)} of {len(df)} tasks")
    for _, row in filtered.iterrows():
        with st.container(border=True):
            c1,c2,c3=st.columns([4,1.2,1.2])
            with c1:
                st.markdown(f"### {row.title}")
                st.caption(f"{row.description or 'No description'}")
                st.markdown(f"{row.assignee_avatar or '👤'} **{row.assignee_name or 'Unassigned'}** · {row.team_name or 'No team'} · Due **{row.due_date or '—'}** · {row.estimate_hours:g}h")
                if row.labels:
                    st.caption("🏷️ " + " · ".join(x.strip() for x in row.labels.split(",") if x.strip()))
            with c2:
                st.metric("Priority", row.priority)
            with c3:
                if st.button("Edit", key=f"edit{row.id}", use_container_width=True):
                    st.session_state[f"editing_{row.id}"]=True
                if st.button("Delete", key=f"del{row.id}", use_container_width=True):
                    delete_task(row.id,st.session_state.user["id"]); st.rerun()
            if st.session_state.get(f"editing_{row.id}"):
                task_editor(row.to_dict(), key="edit")
                if st.button("Close editor", key=f"close{row.id}"):
                    st.session_state[f"editing_{row.id}"]=False; st.rerun()

def render_kanban():
    st.title("Kanban Board")
    st.caption("Move work through the delivery pipeline.")
    df=tasks_df()
    cols=st.columns(len(STATUSES))
    for col,status in zip(cols,STATUSES):
        with col:
            st.markdown(f"### {status}  `{len(df[df.status==status])}`")
            subset=df[df.status==status]
            for _,r in subset.iterrows():
                overdue = r.due_date and r.status!="Done" and pd.to_datetime(r.due_date).date() < date.today()
                st.markdown(f"""<div class="task-card"><b>{r.title}</b><br>
                <span class="muted">{r.priority} · {r.assignee_avatar or '👤'} {r.assignee_name or 'Unassigned'}</span><br>
                <span class="muted">📅 {r.due_date or 'No due date'}{" · ⚠️ overdue" if overdue else ""}</span></div>""",unsafe_allow_html=True)
                choices=[s for s in STATUSES if s!=status]
                target=st.selectbox("Move",["Keep here"]+choices,key=f"move{r.id}",label_visibility="collapsed")
                if target!="Keep here":
                    set_status(r.id,target,st.session_state.user["id"]); st.rerun()

def render_team():
    st.title("Team")
    teams=teams_df(); users=users_df()
    left,right=st.columns([1,1.4])
    with left:
        st.subheader("Teams")
        for _,t in teams.iterrows():
            members=team_members_df(t.id)
            st.markdown(f"**{t.name}**  \n<span class='muted'>{t.description or 'No description'} · {len(members)} members</span>",unsafe_allow_html=True)
            if st.button("Select",key=f"team{t.id}"):
                st.session_state.selected_team=int(t.id); st.rerun()
            st.divider()
        with st.expander("＋ Create team"):
            with st.form("newteam"):
                n=st.text_input("Team name"); d=st.text_area("Description")
                if st.form_submit_button("Create",type="primary"):
                    ok,err=add_team(n,d,st.session_state.user["id"])
                    if ok: st.success("Team created."); st.rerun()
                    else: st.error(err)
    with right:
        tid=st.session_state.get("selected_team", int(teams.iloc[0].id) if len(teams) else None)
        if tid:
            team=teams[teams.id==tid].iloc[0]
            st.subheader(team["name"])
            members=team_members_df(tid)
            for _,m in members.iterrows():
                st.markdown(f"{m.avatar} **{m.name}** · {m.role} · {m.email}")
            st.divider()
            with st.form("addmember"):
                nonmembers=users[~users.id.isin(members.id)] if len(members) else users
                options=[f"{r['avatar']} {r['name']} (#{r['id']})" for _,r in nonmembers.iterrows()]
                choice=st.selectbox("Add member", options if options else ["Everyone is already a member"])
                if st.form_submit_button("Add Member", disabled=not options):
                    uid=int(choice.split("#")[-1].rstrip(")")); add_member(tid,uid,st.session_state.user["id"]); st.success("Member added."); st.rerun()
        else: st.info("Create a team to get started.")

def render_analytics():
    st.title("Analytics")
    df=tasks_df()
    if not len(df): st.info("No tasks yet."); return
    c1,c2=st.columns(2)
    with c1:
        counts=df.status.value_counts().reindex(STATUSES,fill_value=0).reset_index()
        counts.columns=["Status","Count"]
        st.plotly_chart(px.pie(counts,names="Status",values="Count",hole=.45,title="Tasks by status"),use_container_width=True)
    with c2:
        pc=df.priority.value_counts().reindex(PRIORITIES,fill_value=0).reset_index()
        pc.columns=["Priority","Count"]
        st.plotly_chart(px.bar(pc,x="Priority",y="Count",title="Priority distribution"),use_container_width=True)
    ass=df.groupby("assignee_name",dropna=False).agg(Tasks=("id","count"),Hours=("estimate_hours","sum")).reset_index()
    ass["assignee_name"]=ass.assignee_name.fillna("Unassigned")
    st.plotly_chart(px.bar(ass,x="assignee_name",y="Hours",text="Hours",title="Estimated workload by assignee"),use_container_width=True)
    done=df[df.status=="Done"].copy()
    if len(done):
        done["Completed Date"]=pd.to_datetime(done.updated_at).dt.date
        trend=done.groupby("Completed Date").size().reset_index(name="Completed")
        st.plotly_chart(px.line(trend,x="Completed Date",y="Completed",markers=True,title="Completion trend"),use_container_width=True)
    st.dataframe(ass.sort_values("Hours",ascending=False),hide_index=True,use_container_width=True)

def render_activity():
    st.title("Activity Log")
    st.caption("Recent workspace events and task changes.")
    df=activity_df()
    if len(df):
        for _,r in df.iterrows():
            st.markdown(f"**{r.user_name or 'System'}** · {r.action}  \n<span class='muted'>{r.details} · {r.created_at}</span>",unsafe_allow_html=True)
            st.divider()
    else: st.info("No activity yet.")
