from sqlalchemy import inspect

try:
    from database import engine, Base
except ImportError:
    # For safety if run in different context
    from .database import engine, Base


def ensure_users_table_columns() -> None:
    # Create tables that don't exist
    Base.metadata.create_all(bind=engine)

    inspector = inspect(engine)
    try:
        columns = {c["name"] for c in inspector.get_columns("users")}
    except Exception:
        columns = set()

    statements = []

    if "first_name" not in columns:
        statements.append(
            "ALTER TABLE users ADD COLUMN first_name VARCHAR(100) NOT NULL DEFAULT ''"
        )
        statements.append(
            "ALTER TABLE users ALTER COLUMN first_name DROP DEFAULT"
        )

    if "last_name" not in columns:
        statements.append(
            "ALTER TABLE users ADD COLUMN last_name VARCHAR(100) NOT NULL DEFAULT ''"
        )
        statements.append(
            "ALTER TABLE users ALTER COLUMN last_name DROP DEFAULT"
        )

    if "password_hash" not in columns:
        statements.append(
            "ALTER TABLE users ADD COLUMN password_hash VARCHAR(255) NOT NULL DEFAULT ''"
        )
        statements.append(
            "ALTER TABLE users ALTER COLUMN password_hash DROP DEFAULT"
        )

    if "created_at" not in columns:
        statements.append(
            "ALTER TABLE users ADD COLUMN created_at TIMESTAMPTZ DEFAULT NOW()"
        )

    # Ensure unique constraint on email if not present
    uniques = {u.get("name") for u in inspector.get_unique_constraints("users")}
    indexes = {i.get("name") for i in inspector.get_indexes("users")}
    if "users_email_key" not in uniques and "ix_users_email" not in indexes:
        statements.append(
            "ALTER TABLE users ADD CONSTRAINT users_email_key UNIQUE (email)"
        )

    if not statements:
        print("No changes needed.")
        return

    with engine.begin() as conn:
        for stmt in statements:
            conn.exec_driver_sql(stmt)
    print("Users table migrated.")


if __name__ == "__main__":
    ensure_users_table_columns()



