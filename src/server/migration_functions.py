from datetime import datetime, timezone
from typing import Callable, List, Tuple
from pymongo.database import Database

from .model import MigrationRepository, Migration
from .debugLog import log

MigrationFunc = Callable[[Database], None]
MIGRATIONS: List[Tuple[int, MigrationFunc, str]] = []


def register_migration(version: int, description: str):
    """Decorator to register a migration function.

    Migration functions receive a `pymongo.database.Database` instance and
    should perform the required schema/data changes using pymongo or the
    repositories defined in `src/server/model.py`.
    """

    def decorator(func: MigrationFunc):
        MIGRATIONS.append((version, func, description))
        return func

    return decorator


def get_applied_versions(db: Database) -> set:
    repo = MigrationRepository(db)
    return set(m.version for m in repo.find_by({}))


def apply_migrations(db: Database, dry_run: bool = False) -> None:
    """Apply all registered migrations that haven't been applied yet.

    - `db` is a `pymongo.database.Database` instance (the same used by
      the repositories elsewhere in the project).
    - `dry_run` prints the migrations that would be applied without executing them.
    """

    repo = MigrationRepository(db)
    applied = get_applied_versions(db)

    to_apply = sorted([m for m in MIGRATIONS if m[0] not in applied], key=lambda x: x[0])

    for version, func, description in to_apply:
        if dry_run:
            print(f"[DRY RUN] Would apply migration {version}: {description}")
            continue

        log.info(f"Applying migration {version}: {description}")
        func(db)
        migration = Migration(version=version, description=description, applied_at=datetime.now(tz=timezone.utc))
        repo.save(migration)
        log.info(f"Applied migration {version}")


# Example:
#
# @register_migration(1, "Create indexes on recipes.name")
# def migration_001(db: Database):
#     db.get_collection('recipes').create_index('name')
#
# Then call `apply_migrations(db)` at application startup (once the Database is available).

# Try to import example migrations so they register automatically when the package is imported.
try:
    import server.migrations  # noqa: F401
except Exception:
    # Ignore if the example file is not present or fails to import.
    pass
