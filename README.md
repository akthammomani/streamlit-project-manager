<p align="left">
  <!-- Language / Core -->
  <img alt="Python" src="https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white">
  <img alt="Streamlit" src="https://img.shields.io/badge/Streamlit-1.50%2B-FF4B4B?logo=streamlit&logoColor=white">
  <img alt="Plotly" src="https://img.shields.io/badge/Plotly-5.x-3F4F75?logo=plotly&logoColor=white">
  <img alt="Pandas" src="https://img.shields.io/badge/Pandas-2.x-150458?logo=pandas&logoColor=white">
  <img alt="SQLAlchemy" src="https://img.shields.io/badge/SQLAlchemy-2.x-D71F00?logo=python&logoColor=white">
  <img alt="SQLite" src="https://img.shields.io/badge/SQLite-default%20persistence-003B57?logo=sqlite&logoColor=white">
  <img alt="Postgres" src="https://img.shields.io/badge/Postgres-optional-4169E1?logo=postgresql&logoColor=white">

  <!-- App / UX -->
  <img alt="Inline editing" src="https://img.shields.io/badge/Editing-Inline%20tables-10B981">
  <img alt="Project Analytics" src="https://img.shields.io/badge/Analytics-Project%20Insights-0EA5E9">
  <img alt="Gantt Timeline" src="https://img.shields.io/badge/Timeline-Gantt%20Chart-0EA5E9">
  <img alt="Status" src="https://img.shields.io/badge/Status-To--Do%20%7C%20In--Progress%20%7C%20Done-8B5CF6">
  <img alt="Progress" src="https://img.shields.io/badge/Progress-0%E2%80%93100%25-6366F1">
  <img alt="Assignees" src="https://img.shields.io/badge/Assignee-email--based-22C55E">

  <!-- Collaboration -->
  <img alt="Multi-user" src="https://img.shields.io/badge/Collaboration-multi--user-0EA5E9">
  <img alt="Access" src="https://img.shields.io/badge/Access-Invite%20by%20email-14B8A6">
  <img alt="Privacy" src="https://img.shields.io/badge/Privacy-Project%20PIN-F59E0B">
  <img alt="Roles" src="https://img.shields.io/badge/Roles-owner%20%7C%20editor%20%7C%20viewer-F472B6">

  <!-- Deploy / Ops -->
  <img alt="Deploy" src="https://img.shields.io/badge/Deploy-Streamlit%20Cloud-FF4B4B?logo=streamlit&logoColor=white">
  <img alt="Export" src="https://img.shields.io/badge/Export-CSV%20timeline-64748B">
  <img alt="License" src="https://img.shields.io/badge/License-MIT-000000">
  <img alt="Status" src="https://img.shields.io/badge/Status-Active-brightgreen">
</p>

<p align="center">
  <img src="https://github.com/user-attachments/assets/f53c9be5-61af-4433-9edc-1f519a7a0219"
       alt="Strivio logo" width="330" height="330" />
</p>

# **Strivio - Project Manager** [![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_red.svg)](https://strivio-pm.streamlit.app//)

**Strivio-PM** is a free, Streamlit-powered project manager for solo builders, students, and small teams. Create projects, manage tasks/subtasks **directly in editable tables**, and explore a **Project Analytics** view (timeline + status barcharts + workload) to stay on track. Ships with SQLite by default and can run on Postgres/Supabase via `DATABASE_URL`.

---

## Features

- **Simple sign-in**: type your email to enter.
- **Projects**  
  - Name, **start & end date editing**, invite members, rename, delete.  
  - Private via **Project PIN** or public toggle.
- **Tasks & Subtasks (inline table editing)**  
  - Add/modify rows directly in the grid (status, dates, assignee email, **progress %**).  
  - Clean tables (IDs hidden), dynamic add/remove, bulk CSV import.
- **Project Analytics (new)**  
  - **Timeline (Gantt)** for tasks + subtasks.  
  - **Distribution by Status** (horizontal bars).  
  - **Workload by Assignee** (horizontal bars).  
  - **Schedule health**: days elapsed/remaining, % complete, and **At-Risk / Hygiene** checks (shows "All good" if nothing concerning).
- **Collaboration**  
  - Multi-user via email invites (roles: owner, editor, viewer).
- **Persistence**  
  - Default: **SQLite** (`strivio.db`).  
  - Optional: **Postgres/Supabase** by setting `DATABASE_URL`.
- **Export**  
  - Download timeline CSV from Analytics.
- **Branding / UI**  
  - Polished tab pills, progress number in tables, centered branding, helpful sidebar **Contacts**.

---

## Tech Stack

- Streamlit 1.50+
- Plotly (timeline)
- Pandas (tables)
- SQLAlchemy + SQLite (default) or Postgres/Supabase (optional)

---

## Usage

- **Create / Open a project**
  - In the sidebar, **New project** -> set Name, Start, End, optional member emails, and public/PIN.
  - Use **Open project** to switch projects.
  - **Manage current project**: rename, **change start/end dates**, or delete.

- **Tasks & Subtasks (inline)**
  - Go to **Tasks** tab.
  - Edit directly in the grid (Status, Start/End, Assignee, **Progress %**).  
  - Add/remove rows; click **Save changes** to persist.  
  - **Subtasks**: pick a parent task, then edit its grid the same way.
  - CSV import supported (see on-screen column order).

- **Project Analytics**
  - Shows **Timeline**, **Distribution by Status**, **Workload by Assignee**, and a quick **health panel**.  
  - If no risks are detected, the panel explicitly states nothing is out of order.

---

## Data & Deployment

### Quick demo (recommended to try)
- Run locally: `pip install -r requirements.txt` -> `streamlit run main.py`.  
- Uses **SQLite** by default; no external setup.

### BYOS (Bring Your Own Supabase/Postgres) - for scale & data ownership
> Keep it simple: same code, just point to your DB.

- Create a Postgres/Supabase project.  
- Apply your schema/migrations (SQL file in `db/` or your existing tables).  
- Set environment variable: `DATABASE_URL=postgresql://...` (or use Supabase connection string).  
- (Optional but strongly recommended) enable RLS + minimal policies and/or quota triggers (e.g., project/task caps).  
- Deploy to Streamlit Cloud/Render/Vercel with that env var.

**Why this split?**  
- **Demo** keeps onboarding friction low.  
- **BYOS** gives teams full control, avoids quota limits, and keeps data private.

---

## Environment

- `DATABASE_URL` (optional): if not set, app falls back to SQLite.  
- `STREAMLIT_SECRETS` (optional) can also carry `DATABASE_URL` in hosted environments.

---

## Screenshots
*(Add a few: Tasks grid, Project Analytics, Members.)*

---

## License
MIT

---

## Roadmap
- Per-project burndown, due-soon alerts.
- Optional task templates / CSV export for tasks/subtasks.
- Supabase starter SQL + RLS policy snippets packaged in `/sql/`.

