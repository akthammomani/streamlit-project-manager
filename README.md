<p align="center">
  <img src="https://github.com/user-attachments/assets/f53c9be5-61af-4433-9edc-1f519a7a0219"
       alt="Strivio logo" width="350" height="350" />
</p>

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

## **How to Use**
* Create / Open a Project
 * In the sidebar, open New project → set Name, Start, End, and optional member emails (comma-separated).
 * Your project appears in Open project. Select it to load.

* Manage Members
 * Go to the Members tab.
 * Paste emails (comma-separated) and click Add Members. All added users can open this project by signing in with the same email. (Current input expects commas. If you prefer semicolons, a tiny parser can be added later).

* Add Tasks & Subtasks
 * In Tasks tab → “Add / Edit Task”. Set Status, Start/End, Assignee (email), and Progress%.
 * Add subtasks in Subtasks (select a parent task first).
 * Edit by choosing an existing item in “Edit existing (optional)” and saving.
 * Delete controls appear beneath each table.

* Timeline (Gantt)
 * Open Gantt tab to see Tasks + Subtasks.
 * Bars span through each finish day for a clear schedule view.



