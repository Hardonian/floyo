"""
SQLite-compatible type decorators for JSONB and PGUUID columns.
Maps PostgreSQL-specific types to SQLite-compatible equivalents for testing.
"""
from sqlalchemy import JSON, String
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB, ARRAY as PGARRAY
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.types import TypeDecorator


class SQLiteJSONB(TypeDecorator):
    """JSONB column that works on both PostgreSQL and SQLite."""
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(JSONB())
        return dialect.type_descriptor(JSON())


class SQLitePGUUID(TypeDecorator):
    """PGUUID column that works on both PostgreSQL and SQLite."""
    impl = String(36)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PGUUID(as_uuid=True))
        return dialect.type_descriptor(String(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        # For SQLite, convert UUID to string
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        # For SQLite, return string
        return value


class SQLitePGARRAY(TypeDecorator):
    """PGARRAY column that works on both PostgreSQL and SQLite (stores as JSON)."""
    impl = JSON
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PGARRAY(String))
        return dialect.type_descriptor(JSON())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        return list(value) if value else []

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "postgresql":
            return value
        return value


# Compiler overrides for JSONB
@compiles(JSONB, "sqlite")
def compile_jsonb_sqlite(type_, compiler, **kw):
    return compiler.visit_JSON(type_, **kw)


@compiles(PGUUID, "sqlite")
def compile_pguuid_sqlite(type_, compiler, **kw):
    return compiler.visit_string(type_, **kw)


@compiles(PGARRAY, "sqlite")
def compile_pgarray_sqlite(type_, compiler, **kw):
    return compiler.visit_JSON(type_, **kw)