import os
import json
import shutil
import zipfile
import subprocess
import logging
import asyncio
from datetime import datetime
from typing import Tuple, Optional
from urllib.parse import urlparse

from app.core.config import settings
from app.core.database import async_session
from sqlalchemy import select
from app.models import AppRelease, AppFeature, ShowcaseVideo, SiteSetting, SiteFaq, Admin, AuditLog, DownloadLog

logger = logging.getLogger("nextlevelcheat.backup_manager")


def find_pg_dump() -> Optional[str]:
    """Locate pg_dump binary on the host system."""
    potential_paths = [
        r"D:\Program\postresql\bin\pg_dump.exe",
        r"C:\Program Files\PostgreSQL\18\bin\pg_dump.exe",
        r"C:\Program Files\PostgreSQL\17\bin\pg_dump.exe",
        r"C:\Program Files\PostgreSQL\16\bin\pg_dump.exe",
        r"C:\Program Files\PostgreSQL\15\bin\pg_dump.exe",
        shutil.which("pg_dump"),
    ]
    for p in potential_paths:
        if p and os.path.isfile(p):
            return p
    return None


async def create_full_system_backup_archive() -> Tuple[str, str, int]:
    """
    Creates a 100% full production migration package:
    1. Complete PostgreSQL SQL dump (--clean --if-exists) for 1-click restore on any VPS.
    2. Complete JSON data tables dump for universal import.
    3. All uploaded media: APK binaries, showcase videos, and uploaded assets.
    4. Auto-generated RESTORE_GUIDE.md explaining how to import on any new VPS.

    Returns:
        (zip_file_path, filename, total_size_bytes)
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    static_dir = os.path.join(base_dir, "app", "static")
    uploads_dir = os.path.join(static_dir, "uploads")
    backup_dir = os.path.join(static_dir, "backups")
    os.makedirs(backup_dir, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    archive_name = f"NEXTLEVEL_FULL_VPS_BACKUP_{timestamp}.zip"
    archive_path = os.path.join(backup_dir, archive_name)

    # 1. Parse DB URL for pg_dump
    db_url = settings.DATABASE_URL
    clean_url = db_url.replace("postgresql+asyncpg://", "postgresql://")
    parsed = urlparse(clean_url)

    db_host = parsed.hostname or "localhost"
    db_port = str(parsed.port or 5432)
    db_user = parsed.username or "postgres"
    db_pass = parsed.password or ""
    db_name = parsed.path.lstrip("/") or "nextlevelcheat"

    sql_dump_file = os.path.join(backup_dir, f"database_dump_{timestamp}.sql")
    pg_dump_bin = find_pg_dump()

    if pg_dump_bin:
        try:
            env = os.environ.copy()
            if db_pass:
                env["PGPASSWORD"] = db_pass

            proc = await asyncio.to_thread(
                subprocess.run,
                [
                    pg_dump_bin,
                    "-U", db_user,
                    "-h", db_host,
                    "-p", db_port,
                    "--clean",
                    "--if-exists",
                    "--no-owner",
                    "--no-privileges",
                    db_name,
                ],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False
            )
            if proc.returncode == 0 and len(proc.stdout) > 0:
                with open(sql_dump_file, "wb") as f:
                    f.write(proc.stdout)
                logger.info(f"pg_dump SQL dump generated successfully: {len(proc.stdout)} bytes")
            else:
                logger.warning(f"pg_dump failed (code {proc.returncode}): {proc.stderr.decode('utf-8', errors='ignore')}")
        except Exception as e:
            logger.error(f"Error running pg_dump: {e}")

    # 2. JSON Data Dump for universal portability
    json_dump_file = os.path.join(backup_dir, f"tables_data_{timestamp}.json")
    try:
        async with async_session() as session:
            tables_data = {}
            for model, name in [
                (Admin, "admins"),
                (AppRelease, "releases"),
                (AppFeature, "features"),
                (ShowcaseVideo, "videos"),
                (SiteSetting, "site_settings"),
                (SiteFaq, "faqs"),
                (AuditLog, "audit_logs"),
                (DownloadLog, "download_logs"),
            ]:
                res = await session.execute(select(model))
                records = res.scalars().all()
                tables_data[name] = [
                    {c.name: getattr(r, c.name).isoformat() if isinstance(getattr(r, c.name), datetime) else getattr(r, c.name)
                     for c in r.__table__.columns}
                    for r in records
                ]

            with open(json_dump_file, "w", encoding="utf-8") as f:
                json.dump(tables_data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        logger.error(f"Failed to generate JSON dump: {e}")

    # 3. Create Migration Readme inside ZIP
    readme_content = f"""# NEXT LEVEL CHEAT - FULL DISASTER RECOVERY & VPS MIGRATION PACKAGE
Timestamp: {datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")}
Database Name: {db_name}

## WHAT THIS ARCHIVE CONTAINS:
1. `database_dump.sql` -> 100% Complete PostgreSQL SQL dump (schema, tables, indexes, rows).
2. `tables_data.json`  -> Standalone JSON format of all DB entries.
3. `uploads/`          -> All uploaded APKs, showcase video files, and media.

## HOW TO RESTORE ON A NEW VPS IN 2 MINUTES:
### Step 1: Restore Database
Create the database on your new PostgreSQL server:
```bash
createdb -U postgres {db_name}
```
Import the SQL dump directly:
```bash
psql -U postgres -d {db_name} -f database_dump.sql
```

### Step 2: Restore Media Files
Extract the `uploads` folder directly into:
`backend/app/static/uploads/`

Your entire website, admin settings, APK download links, videos, and analytics are immediately 100% live!
"""

    # 4. Assemble Complete Zip Archive
    with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
        # Include Readme
        zf.writestr("RESTORE_GUIDE.md", readme_content)

        # Include SQL Dump
        if os.path.exists(sql_dump_file):
            zf.write(sql_dump_file, arcname="database_dump.sql")

        # Include JSON Dump
        if os.path.exists(json_dump_file):
            zf.write(json_dump_file, arcname="tables_data.json")

        # Include all files from uploads/ (apks, videos, etc.)
        if os.path.exists(uploads_dir):
            for root, _, files in os.walk(uploads_dir):
                for file in files:
                    file_full_path = os.path.join(root, file)
                    rel_path = os.path.relpath(file_full_path, static_dir)
                    zf.write(file_full_path, arcname=rel_path)

    # Clean temporary uncompressed dump files
    if os.path.exists(sql_dump_file):
        os.remove(sql_dump_file)
    if os.path.exists(json_dump_file):
        os.remove(json_dump_file)

    archive_size = os.path.getsize(archive_path)
    logger.info(f"Full system backup zip created: {archive_path} ({archive_size} bytes)")
    return archive_path, archive_name, archive_size
