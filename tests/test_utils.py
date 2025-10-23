# tests/test_utils.py
from models.task import Task
from models.subtask import Subtask
from utils.progress import compute_task_progress

def test_compute_task_progress():
    class DummySession:
        def exec(self, stmt):
            return [Subtask(percent_complete=40.0), Subtask(percent_complete=80.0)]

    dummy_task = Task(id=1)
    result = compute_task_progress(dummy_task, DummySession())
    assert result == 60.0
