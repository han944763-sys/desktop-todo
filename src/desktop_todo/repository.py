from __future__ import annotations

import shutil
import sqlite3
from datetime import date, datetime, timezone
from pathlib import Path

from desktop_todo.models import Project, Task


LATEST_SCHEMA_VERSION = 1


class DatabaseError(RuntimeError):
    """Raised when the application database cannot be used safely."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _parse_datetime(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


class TodoRepository:
    def __init__(self, db_path: Path | str):
        self.db_path = Path(db_path)
        self._connection: sqlite3.Connection | None = None
        self._had_existing_database = (
            self.db_path.exists() and self.db_path.stat().st_size > 0
        )
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._connection = sqlite3.connect(self.db_path)
            self._connection.row_factory = sqlite3.Row
            self._connection.execute("PRAGMA foreign_keys = ON")
            self._connection.execute("PRAGMA busy_timeout = 3000")
            self._connection.execute("PRAGMA journal_mode = WAL")
            self._migrate()
        except (OSError, sqlite3.Error) as exc:
            self.close()
            raise DatabaseError(f"无法打开或初始化数据库：{exc}") from exc

    @property
    def connection(self) -> sqlite3.Connection:
        if self._connection is None:
            raise DatabaseError("数据库连接已经关闭")
        return self._connection

    def _migrate(self) -> None:
        version = int(self.connection.execute("PRAGMA user_version").fetchone()[0])
        if version > LATEST_SCHEMA_VERSION:
            raise DatabaseError(
                f"数据库版本 {version} 高于程序支持的版本 {LATEST_SCHEMA_VERSION}"
            )
        if version == LATEST_SCHEMA_VERSION:
            return

        if self._had_existing_database:
            backup_name = f"{self.db_path.name}.backup-{datetime.now():%Y%m%d-%H%M%S}"
            try:
                shutil.copy2(self.db_path, self.db_path.with_name(backup_name))
            except OSError as exc:
                raise DatabaseError(f"数据库升级前备份失败：{exc}") from exc

        try:
            with self.connection:
                if version < 1:
                    self._create_schema_v1()
                self.connection.execute(f"PRAGMA user_version = {LATEST_SCHEMA_VERSION}")
        except sqlite3.Error as exc:
            raise DatabaseError(f"数据库升级失败：{exc}") from exc

    def _create_schema_v1(self) -> None:
        statements = (
            """
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL CHECK(length(trim(name)) BETWEEN 1 AND 120),
                goal TEXT NOT NULL DEFAULT '',
                current_stage TEXT NOT NULL DEFAULT '',
                next_action TEXT NOT NULL DEFAULT '',
                is_archived INTEGER NOT NULL DEFAULT 0 CHECK(is_archived IN (0, 1)),
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL CHECK(length(trim(title)) BETWEEN 1 AND 300),
                task_date TEXT NOT NULL,
                is_completed INTEGER NOT NULL DEFAULT 0 CHECK(is_completed IN (0, 1)),
                completed_at TEXT,
                project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL,
                source_action TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_tasks_date_order
            ON tasks(task_date, created_at, id)
            """,
            """
            CREATE INDEX IF NOT EXISTS idx_tasks_project_completed
            ON tasks(project_id, is_completed, completed_at)
            """,
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_project_action_day
            ON tasks(project_id, task_date, source_action)
            WHERE project_id IS NOT NULL AND source_action IS NOT NULL
            """,
        )
        for statement in statements:
            self.connection.execute(statement)

    @staticmethod
    def _clean_required(value: str, label: str, maximum: int) -> str:
        cleaned = value.strip()
        if not cleaned:
            raise ValueError(f"{label}不能为空")
        if len(cleaned) > maximum:
            raise ValueError(f"{label}不能超过 {maximum} 个字符")
        return cleaned

    @staticmethod
    def _clean_optional(value: str, maximum: int = 1000) -> str:
        cleaned = value.strip()
        if len(cleaned) > maximum:
            raise ValueError(f"内容不能超过 {maximum} 个字符")
        return cleaned

    def list_tasks(self, task_date: date) -> list[Task]:
        rows = self.connection.execute(
            "SELECT * FROM tasks WHERE task_date = ? ORDER BY created_at, id",
            (task_date.isoformat(),),
        ).fetchall()
        return [self._task_from_row(row) for row in rows]

    def task_dates(self, start: date, end: date) -> set[date]:
        rows = self.connection.execute(
            "SELECT DISTINCT task_date FROM tasks WHERE task_date BETWEEN ? AND ?",
            (start.isoformat(), end.isoformat()),
        ).fetchall()
        return {date.fromisoformat(row[0]) for row in rows}

    def create_task(
        self,
        title: str,
        task_date: date,
        *,
        project_id: int | None = None,
        source_action: str | None = None,
    ) -> Task:
        title = self._clean_required(title, "任务标题", 300)
        source_action = source_action.strip() if source_action else None
        timestamp = _now()
        try:
            with self.connection:
                cursor = self.connection.execute(
                    """
                    INSERT INTO tasks(
                        title, task_date, project_id, source_action, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        title,
                        task_date.isoformat(),
                        project_id,
                        source_action,
                        timestamp,
                        timestamp,
                    ),
                )
            return self.get_task(int(cursor.lastrowid))
        except sqlite3.Error as exc:
            raise DatabaseError(f"保存任务失败：{exc}") from exc

    def get_task(self, task_id: int) -> Task:
        row = self.connection.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if row is None:
            raise KeyError(f"任务不存在：{task_id}")
        return self._task_from_row(row)

    def rename_task(self, task_id: int, title: str) -> Task:
        title = self._clean_required(title, "任务标题", 300)
        with self.connection:
            cursor = self.connection.execute(
                "UPDATE tasks SET title = ?, updated_at = ? WHERE id = ?",
                (title, _now(), task_id),
            )
        if cursor.rowcount != 1:
            raise KeyError(f"任务不存在：{task_id}")
        return self.get_task(task_id)

    def set_task_completed(self, task_id: int, completed: bool) -> Task:
        timestamp = _now()
        completed_at = timestamp if completed else None
        with self.connection:
            cursor = self.connection.execute(
                """
                UPDATE tasks
                SET is_completed = ?, completed_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (int(completed), completed_at, timestamp, task_id),
            )
        if cursor.rowcount != 1:
            raise KeyError(f"任务不存在：{task_id}")
        return self.get_task(task_id)

    def delete_task(self, task_id: int) -> None:
        with self.connection:
            cursor = self.connection.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        if cursor.rowcount != 1:
            raise KeyError(f"任务不存在：{task_id}")

    def list_projects(self, *, include_archived: bool = False) -> list[Project]:
        where = "" if include_archived else "WHERE is_archived = 0"
        rows = self.connection.execute(
            f"SELECT * FROM projects {where} ORDER BY created_at, id"
        ).fetchall()
        return [self._project_from_row(row) for row in rows]

    def get_project(self, project_id: int) -> Project:
        row = self.connection.execute(
            "SELECT * FROM projects WHERE id = ?", (project_id,)
        ).fetchone()
        if row is None:
            raise KeyError(f"长期项目不存在：{project_id}")
        return self._project_from_row(row)

    def create_project(
        self, name: str, goal: str, current_stage: str, next_action: str
    ) -> Project:
        name = self._clean_required(name, "项目名称", 120)
        goal = self._clean_optional(goal)
        current_stage = self._clean_optional(current_stage, 300)
        next_action = self._clean_optional(next_action, 300)
        timestamp = _now()
        with self.connection:
            cursor = self.connection.execute(
                """
                INSERT INTO projects(
                    name, goal, current_stage, next_action, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (name, goal, current_stage, next_action, timestamp, timestamp),
            )
        return self.get_project(int(cursor.lastrowid))

    def update_project(
        self,
        project_id: int,
        *,
        name: str,
        goal: str,
        current_stage: str,
        next_action: str,
    ) -> Project:
        name = self._clean_required(name, "项目名称", 120)
        goal = self._clean_optional(goal)
        current_stage = self._clean_optional(current_stage, 300)
        next_action = self._clean_optional(next_action, 300)
        with self.connection:
            cursor = self.connection.execute(
                """
                UPDATE projects
                SET name = ?, goal = ?, current_stage = ?, next_action = ?, updated_at = ?
                WHERE id = ?
                """,
                (name, goal, current_stage, next_action, _now(), project_id),
            )
        if cursor.rowcount != 1:
            raise KeyError(f"长期项目不存在：{project_id}")
        return self.get_project(project_id)

    def set_project_archived(self, project_id: int, archived: bool = True) -> Project:
        with self.connection:
            cursor = self.connection.execute(
                "UPDATE projects SET is_archived = ?, updated_at = ? WHERE id = ?",
                (int(archived), _now(), project_id),
            )
        if cursor.rowcount != 1:
            raise KeyError(f"长期项目不存在：{project_id}")
        return self.get_project(project_id)

    def add_next_action_to_date(
        self, project_id: int, task_date: date
    ) -> tuple[Task, bool]:
        project = self.get_project(project_id)
        action = self._clean_required(project.next_action, "下一步行动", 300)
        try:
            return (
                self.create_task(
                    action,
                    task_date,
                    project_id=project_id,
                    source_action=action,
                ),
                True,
            )
        except DatabaseError as exc:
            if "UNIQUE constraint failed" not in str(exc):
                raise
            row = self.connection.execute(
                """
                SELECT * FROM tasks
                WHERE project_id = ? AND task_date = ? AND source_action = ?
                """,
                (project_id, task_date.isoformat(), action),
            ).fetchone()
            if row is None:
                raise
            return self._task_from_row(row), False

    def recent_completed_tasks(self, project_id: int, limit: int = 3) -> list[Task]:
        rows = self.connection.execute(
            """
            SELECT * FROM tasks
            WHERE project_id = ? AND is_completed = 1
            ORDER BY completed_at DESC, id DESC
            LIMIT ?
            """,
            (project_id, max(0, limit)),
        ).fetchall()
        return [self._task_from_row(row) for row in rows]

    @staticmethod
    def _task_from_row(row: sqlite3.Row) -> Task:
        return Task(
            id=int(row["id"]),
            title=str(row["title"]),
            task_date=date.fromisoformat(row["task_date"]),
            is_completed=bool(row["is_completed"]),
            completed_at=_parse_datetime(row["completed_at"]),
            project_id=row["project_id"],
            source_action=row["source_action"],
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    @staticmethod
    def _project_from_row(row: sqlite3.Row) -> Project:
        return Project(
            id=int(row["id"]),
            name=str(row["name"]),
            goal=str(row["goal"]),
            current_stage=str(row["current_stage"]),
            next_action=str(row["next_action"]),
            is_archived=bool(row["is_archived"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )

    def close(self) -> None:
        if self._connection is not None:
            self._connection.close()
            self._connection = None

    def __enter__(self) -> TodoRepository:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
