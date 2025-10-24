<p align="left">
  <!-- Language / Core -->
  <img alt="Python" src="https://img.shields.io/badge/Python-3.10%2B-blue?logo=python&logoColor=white">
  <img alt="Streamlit" src="https://img.shields.io/badge/Streamlit-1.50%2B-FF4B4B?logo=streamlit&logoColor=white">
  <img alt="Plotly" src="https://img.shields.io/badge/Plotly-5.x-3F4F75?logo=plotly&logoColor=white">
  <img alt="Pandas" src="https://img.shields.io/badge/Pandas-2.x-150458?logo=pandas&logoColor=white">
  <img alt="SQLAlchemy" src="https://img.shields.io/badge/SQLAlchemy-2.x-D71F00?logo=python&logoColor=white">
  <img alt="SQLite" src="https://img.shields.io/badge/SQLite-persistence-003B57?logo=sqlite&logoColor=white">

  <!-- App / UX -->
  <img alt="Gantt Timeline" src="https://img.shields.io/badge/Timeline-Gantt%20Chart-0EA5E9">
  <img alt="Tasks & Subtasks" src="https://img.shields.io/badge/Tasks-Tasks%20%2B%20Subtasks-10B981">
  <img alt="Status" src="https://img.shields.io/badge/Status-To--Do%20%7C%20In--Progress%20%7C%20Done-8B5CF6">
  <img alt="Progress" src="https://img.shields.io/badge/Progress-0%E2%80%93100%25-6366F1">
  <img alt="Assignees" src="https://img.shields.io/badge/Assignee-email--based-22C55E">

  <!-- Collaboration -->
  <img alt="Multi-user" src="https://img.shields.io/badge/Collaboration-multi--user-0EA5E9">
  <img alt="Access" src="https://img.shields.io/badge/Access-Invite%20by%20email-14B8A6">
  <img alt="Privacy" src="https://img.shields.io/badge/Privacy-Project%20PIN%20-F59E0B">
  <img alt="Roles" src="https://img.shields.io/badge/Roles-owner%20%7C%20editor%20%7C%20viewer%20-F472B6">

  <!-- Deploy / Ops -->
  <img alt="Deploy" src="https://img.shields.io/badge/Deploy-Streamlit%20Cloud-FF4B4B?logo=streamlit&logoColor=white">
  <img alt="Export" src="https://img.shields.io/badge/Export-CSV%20timeline-64748B">
  <img alt="License" src="https://img.shields.io/badge/License-MIT-000000">
  <img alt="Status" src="https://img.shields.io/badge/Status-Active-brightgreen">
</p>


<p align="center">
  <img src="https://github.com/user-attachments/assets/f53c9be5-61af-4433-9edc-1f519a7a0219"
       alt="Strivio logo" width="350" height="350" />
</p>

# **Strivio - Project Manager**

Strivio-PM is a Free, Streamlit-powered project manager for solo builders, students, and small teams. Create projects, add tasks and subtasks (with start/end dates, assignees, and status), and visualize timelines with a clean Plotly Gantt chart. It's perfect for quickly organizing research and capstone projects.

## **Features**

* Email “profiles” (simple sign-in field)
* Projects: name, start & end dates, member list, rename/delete
* Tasks & Subtasks: To-Do / In Progress / Done, assignee (email), progress%, dates
* Timeline (Gantt): Tasks + Subtasks shown together; auto "end-of-day" finish for proper bars
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
  * In the sidebar, open New project -> set Name, Start, End, and optional member emails (comma-separated).
  * Your project appears in Open project. Select it to load.

* Manage Members
  * Go to the Members tab.
  * Paste emails (comma-separated) and click Add Members. All added users can open this project by signing in with the same email. (Current input expects commas).

* Add Tasks & Subtasks
  * In Tasks tab -> "Add / Edit Task". Set Status, Start/End, Assignee (email), and Progress%.
  * Add subtasks in Subtasks (select a parent task first).
  * Edit by choosing an existing item in "Edit existing (optional)" and saving.
  * Delete controls appear beneath each table.

* Timeline (Gantt)
  * Open Gantt tab to see Tasks + Subtasks.
  * Bars span through each finish day for a clear schedule view.



