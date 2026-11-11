from __future__ import annotations

import sqlite3
from datetime import date, timedelta

import pytest

from desktop_todo.repository import DatabaseError, TodoRepository


@pytest.fixture
def repository(tmp_path):
    repo = TodoRepository(tmp_path / "todo.db")
    yield repo
    repo.close()


def test_new_database_has_current_schema_without_backup(tmp_path):
    db_path = tmp_path / "todo.db"
    with TodoRepository(db_path) as repo:
        assert repo.connection.execute("PRAGMA user_version").fetchone()[0] == 1
    assert list(tmp_path.glob("*.backup-*")) == []


def test_task_crud_keeps_creation_order_and_completion_position(repository):
    selected = date(2026, 9, 21)
    first = repository.create_task("第一项", selected)
    second = repository.create_task("第二项", selected)

    repository.set_task_completed(first.id, True)
    listed = repository.list_tasks(selected)
    assert [task.id for task in listed] == [first.id, second.id]
    assert listed[0].is_completed is True
    assert listed[0].completed_at is not None

    renamed = repository.rename_task(second.id, "修改后的第二项")
    assert renamed.title == "修改后的第二项"
    repository.delete_task(first.id)
    assert [task.id for task in repository.list_tasks(selected)] == [second.id]


def test_tasks_never_roll_over_to_another_date(repository):
    yesterday = date(2026, 9, 20)
    today = yesterday + timedelta(days=1)
    repository.create_task("留在昨天", yesterday)

    assert [task.title for task in repository.list_tasks(yesterday)] == ["留在昨天"]
    assert repository.list_tasks(today) == []


def test_project_next_action_is_unique_per_day_and_tracks_history(repository):
    project = repository.create_project(
        "自动回充", "完成实机回充", "结构验证", "完成红外建模"
    )
    selected = date(2026, 9, 21)

    first, created = repository.add_next_action_to_date(project.id, selected)
    duplicate, created_again = repository.add_next_action_to_date(project.id, selected)
    assert created is True
    assert created_again is False
    assert duplicate.id == first.id

    repository.set_task_completed(first.id, True)
    recent = repository.recent_completed_tasks(project.id)
    assert [task.title for task in recent] == ["完成红外建模"]

    repository.update_project(
        project.id,
        name=project.name,
        goal=project.goal,
        current_stage="实机准备",
        next_action="检查机械间隙",
    )
    second, created = repository.add_next_action_to_date(project.id, selected)
    assert created is True
    assert second.id != first.id


def test_archiving_project_keeps_linked_tasks(repository):
    project = repository.create_project("英语", "交流", "基础", "听力 20 分钟")
    task, _ = repository.add_next_action_to_date(project.id, date(2026, 9, 21))
    repository.set_project_archived(project.id)

    assert repository.list_projects() == []
    assert repository.list_projects(include_archived=True)[0].is_archived is True
    assert repository.get_task(task.id).project_id == project.id


@pytest.mark.parametrize("title", ["", "   ", "x" * 301])
def test_invalid_task_title_is_rejected(repository, title):
    with pytest.raises(ValueError):
        repository.create_task(title, date.today())


def test_existing_version_zero_database_is_backed_up(tmp_path):
    db_path = tmp_path / "todo.db"
    connection = sqlite3.connect(db_path)
    connection.execute("CREATE TABLE legacy(value TEXT)")
    connection.execute("INSERT INTO legacy VALUES ('keep me')")
    connection.commit()
    connection.close()

    with TodoRepository(db_path):
        pass

    backups = list(tmp_path.glob("todo.db.backup-*"))
    assert len(backups) == 1
    backup = sqlite3.connect(backups[0])
    assert backup.execute("SELECT value FROM legacy").fetchone()[0] == "keep me"
    backup.close()


def test_newer_schema_is_refused_without_overwrite(tmp_path):
    db_path = tmp_path / "todo.db"
    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA user_version = 99")
    connection.execute("CREATE TABLE future_data(value TEXT)")
    connection.execute("INSERT INTO future_data VALUES ('preserve')")
    connection.commit()
    connection.close()

    with pytest.raises(DatabaseError, match="高于程序支持"):
        TodoRepository(db_path)

    connection = sqlite3.connect(db_path)
    assert connection.execute("SELECT value FROM future_data").fetchone()[0] == "preserve"
    connection.close()

