# Database Style

## Scope

Applies to all SQL migrations, queries, and database-related code. Database is **optional** (in-memory state by default) but these rules apply when PostgreSQL persistence is added.

## Database Engine

PostgreSQL 17+ (Alpine image in Docker Compose).

## Migration Rules

- Migrations live in a dedicated migrations directory
- Numbered sequentially: `0001_initial.sql`, `0002_add_sessions.sql`, etc.
- **Every migration must be reversible** -- include a corresponding `DOWN` migration or document why it is not possible
- **No data loss migrations** without explicit human approval (human gate)
- **No `DROP TABLE`** in production migrations without a deprecation period
- Test migrations against a clean database AND against the previous schema version

## Naming Conventions

| Element            | Convention                          | Example                                         |
| ------------------ | ----------------------------------- | ----------------------------------------------- |
| Tables             | `snake_case`, plural                | `user_sessions`, `audit_events`                 |
| Columns            | `snake_case`                        | `user_id`, `created_at`, `token_count`          |
| Primary keys       | `id` (UUID v7)                      | `id UUID PRIMARY KEY DEFAULT gen_random_uuid()` |
| Foreign keys       | `<table_singular>_id`               | `session_id`, `user_id`                         |
| Indexes            | `idx_<table>_<columns>`             | `idx_user_sessions_user_id`                     |
| Unique constraints | `uq_<table>_<columns>`              | `uq_user_sessions_user_id_provider`             |
| Timestamps         | `created_at`, `updated_at`          | Always `TIMESTAMPTZ`, never `TIMESTAMP`         |
| Boolean columns    | `is_<adjective>` or verb past tense | `is_active`, `completed`                        |
| Enums              | PostgreSQL `CREATE TYPE`            | `CREATE TYPE status AS ENUM (...)`              |

## SQL Style

- **Keywords**: UPPERCASE (`SELECT`, `FROM`, `WHERE`, `INSERT INTO`)
- **Identifiers**: lowercase snake_case (never quoted unless absolutely necessary)
- **No `SELECT *`** in application queries -- list columns explicitly
- **No marker comments** -- forbidden in `.sql` files (T-003 enforced)
- **Parameterized queries only** -- never interpolate user input into SQL strings
- **Use `TIMESTAMPTZ`** -- never bare `TIMESTAMP` (timezone-aware required)

## Indexing

- Every foreign key gets an index (PostgreSQL does not auto-index FK columns)
- Queries in hot paths must have a covering index
- Explain plans for new queries touching > 1000 rows

## Security

- **No credentials in migration files** -- use environment variables
- **No `SUPERUSER` operations** in application migrations
- Application database user has minimal privileges
- API keys are **never stored in the database**

## Testing

- Integration tests use a dedicated test database (separate from dev)
- Each test suite creates a fresh schema (or uses transactions with rollback)
- `docker compose` provides the test PostgreSQL instance
