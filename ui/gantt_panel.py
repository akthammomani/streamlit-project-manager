# ui/gantt_panel.py
import streamlit as st
import pandas as pd
import plotly.express as px

from utils.timeline import timeline_df_for_project

def render_gantt_panel(project_id: int):
    st.subheader("Gantt Timeline")
    df = timeline_df_for_project(project_id)
    if df.empty:
        st.info("Add tasks/subtasks with dates to see the timeline.")
    else:
        fig = px.timeline(df, x_start="Start", x_end="Finish", y="Item",
                          color="Status", hover_data=["Type"])
        fig.update_yaxes(autorange="reversed")
        st.plotly_chart(fig, use_container_width=True)
