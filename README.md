<img width="350" height="350" alt="Image" src="https://github.com/user-attachments/assets/f53c9be5-61af-4433-9edc-1f519a7a0219" />

# **Strivio - Project Manager**

Strivio is a lightweight, Streamlit-powered project manager for solo builders, students, and small teams. Create projects, add tasks and subtasks (with start/end dates, assignees, and status), and visualize timelines with a clean Plotly Gantt chart. It’s perfect for quickly organizing research, capstone projects, and MVP work without the overhead of a full PM suite.

## **Features**

* Email “profiles” (simple sign-in field)
* Projects: name, start & end dates, member list, rename/delete
* Tasks & Subtasks: Backlog / In-Progress / Completed, assignee (email), progress%, dates
* Timeline (Gantt): Tasks + Subtasks shown together; auto “end-of-day” finish for proper bars
* Persistence: SQLite (data.db) so your work is saved between sessions
* Multi-user: Invite collaborators by email; they can open and update the same project
* Export: Download the timeline as CSV from the Gantt tab (optional PNG export supported)
* Branding: Custom sidebar logo and app title (Strivio — Project Manager)

## **Tech Stack**

* Streamlit 1.50+
* Plotly for Gantt timelines
* SQLAlchemy + SQLite for data
* Pandas for table displays


