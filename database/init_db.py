#!/usr/bin/env python3
"""Initialize SQLite database for the Smart To-Do List app.

This script is intended for the database container. It creates a fresh SQLite database
file (myapp.db) with tables that mirror the Android Room schema used by the app.

Tables:
- categories
- tasks

It also creates helpful indexes and inserts small seed data to ensure the app has
something to display on first launch.

Note:
- This script intentionally replaces the previous sample tables (users/app_info).
- Foreign keys are enabled.
"""

import os
import sqlite3

DB_NAME = "myapp.db"

# Kept for consistency with other templates; not used by SQLite.
DB_USER = "kaviasqlite"
DB_PASSWORD = "kaviadefaultpassword"
DB_PORT = "5000"


def _connect(db_path: str) -> sqlite3.Connection:
    """Create a SQLite connection with foreign keys enabled."""
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def _create_schema(cursor: sqlite3.Cursor) -> None:
    """Create the Smart To-Do schema (categories, tasks) and indexes."""
    # categories table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL COLLATE NOCASE,
            color TEXT,
            sort_order INTEGER NOT NULL DEFAULT 0,
            created_at INTEGER NOT NULL DEFAULT (strftime('%s','now')*1000),
            updated_at INTEGER NOT NULL DEFAULT (strftime('%s','now')*1000),
            UNIQUE(name)
        )
        """
    )

    # tasks table
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            description TEXT,
            due_at INTEGER,
            is_completed INTEGER NOT NULL DEFAULT 0 CHECK (is_completed IN (0,1)),
            completed_at INTEGER,
            category_id INTEGER,
            priority INTEGER NOT NULL DEFAULT 0,
            created_at INTEGER NOT NULL DEFAULT (strftime('%s','now')*1000),
            updated_at INTEGER NOT NULL DEFAULT (strftime('%s','now')*1000),
            FOREIGN KEY(category_id) REFERENCES categories(id)
                ON UPDATE CASCADE
                ON DELETE SET NULL,
            CHECK (completed_at IS NULL OR is_completed = 1),
            CHECK (due_at IS NULL OR due_at >= 0)
        )
        """
    )

    # Indexes to support typical app queries (filter by category/completion, sort by due date, etc.)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_category_id ON tasks(category_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_due_at ON tasks(due_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_is_completed ON tasks(is_completed)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_completed_at ON tasks(completed_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_created_at ON tasks(created_at)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_categories_sort_order ON categories(sort_order)")


def _seed_data(cursor: sqlite3.Cursor) -> None:
    """Insert seed categories and tasks (safe to run multiple times)."""
    # Categories: align with app theme accents.
    categories = [
        ("Personal", "#10B981", 0),
        ("Work", "#374151", 1),
        ("Shopping", "#9CA3AF", 2),
        ("Health", "#EF4444", 3),
    ]
    for name, color, sort_order in categories:
        cursor.execute(
            "INSERT OR IGNORE INTO categories (name, color, sort_order) VALUES (?, ?, ?)",
            (name, color, sort_order),
        )

    # Seed tasks: small starter content.
    # We intentionally do NOT use OR IGNORE here because tasks don't have a natural unique key.
    # Only insert tasks if the tasks table is empty.
    cursor.execute("SELECT COUNT(*) FROM tasks")
    task_count = cursor.fetchone()[0]
    if task_count == 0:
        cursor.execute(
            """
            INSERT INTO tasks (title, description, due_at, is_completed, category_id, priority)
            VALUES (?, ?, NULL, 0, (SELECT id FROM categories WHERE name = 'Personal'), 0)
            """,
            ("Welcome to Smart To-Do", "Tap a task to edit it. Use the + button to add more."),
        )
        cursor.execute(
            """
            INSERT INTO tasks (title, description, due_at, is_completed, category_id, priority)
            VALUES (?, ?, NULL, 0, (SELECT id FROM categories WHERE name = 'Work'), 1)
            """,
            ("Plan your week", "Add a few work tasks and set due dates."),
        )
        cursor.execute(
            """
            INSERT INTO tasks (title, description, due_at, is_completed, category_id, priority)
            VALUES (?, ?, NULL, 0, (SELECT id FROM categories WHERE name = 'Shopping'), 0)
            """,
            ("Buy groceries", "Milk, eggs, bread, fruit."),
        )


def _write_connection_files(db_path: str) -> None:
    """Write db_connection.txt and db_visualizer/sqlite.env to reflect current DB path."""
    current_dir = os.getcwd()
    connection_string = f"sqlite:///{current_dir}/{DB_NAME}"

    # db_connection.txt (used as source of truth for connection info)
    with open("db_connection.txt", "w", encoding="utf-8") as f:
        f.write("# SQLite connection methods:\n")
        f.write(f"# Python: sqlite3.connect('{DB_NAME}')\n")
        f.write(f"# Connection string: {connection_string}\n")
        f.write(f"# File path: {current_dir}/{DB_NAME}\n")

    # db_visualizer environment file
    os.makedirs("db_visualizer", exist_ok=True)
    with open("db_visualizer/sqlite.env", "w", encoding="utf-8") as f:
        f.write(f'export SQLITE_DB="{os.path.abspath(db_path)}"\n')


def main() -> None:
    """Entrypoint to initialize or validate the SQLite database."""
    print("Starting SQLite setup...")

    db_exists = os.path.exists(DB_NAME)
    if db_exists:
        print(f"SQLite database already exists at {DB_NAME}")
    else:
        print("Creating new SQLite database...")

    conn = _connect(DB_NAME)
    try:
        cursor = conn.cursor()

        # Create schema + indexes
        _create_schema(cursor)

        # Seed data
        _seed_data(cursor)

        conn.commit()

        # Stats
        cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
        table_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM categories")
        categories_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM tasks")
        tasks_count = cursor.fetchone()[0]

    finally:
        conn.close()

    _write_connection_files(DB_NAME)

    print("\nSQLite setup complete!")
    print(f"Database: {DB_NAME}")
    print(f"Location: {os.getcwd()}/{DB_NAME}")
    print("")
    print("To use with Node.js viewer, run: source db_visualizer/sqlite.env")
    print("\nTo connect to the database, use one of the following methods:")
    print(f"1. Python: sqlite3.connect('{DB_NAME}')")
    print(f"2. Connection string: sqlite:///{os.getcwd()}/{DB_NAME}")
    print(f"3. Direct file access: {os.getcwd()}/{DB_NAME}")
    print("")
    print("Database statistics:")
    print(f"  Tables: {table_count}")
    print(f"  Categories: {categories_count}")
    print(f"  Tasks: {tasks_count}")
    print("\nScript completed successfully.")


if __name__ == "__main__":
    main()
