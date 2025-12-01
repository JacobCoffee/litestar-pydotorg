#!/usr/bin/env python
"""Import download data from pythondotorg Django fixtures.

This script imports OS, Release, and ReleaseFile data from the Django
fixtures file at python.org into our Litestar database.

Usage:
    uv run python scripts/import_downloads.py [--fixture-path PATH] [--dry-run]

The script:
1. Reads the Django fixture JSON file
2. Maps Django model fields to our SQLAlchemy models
3. Creates OS entries first (dependencies for ReleaseFile)
4. Creates Release entries
5. Creates ReleaseFile entries with proper foreign key relationships
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import click
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pydotorg.core.database import get_engine, get_async_session_factory  # noqa: E402
from pydotorg.domains.downloads.models import OS, PythonVersion, Release, ReleaseFile  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DEFAULT_FIXTURE_PATH = Path("/Users/coffee/git/internal/python/pythondotorg/fixtures/downloads.json")
PYTHON_ORG_BASE_URL = "https://www.python.org"


def map_version(django_version: int) -> PythonVersion:
    """Map Django integer version to our PythonVersion enum."""
    mapping = {
        1: PythonVersion.PYTHON1,
        2: PythonVersion.PYTHON2,
        3: PythonVersion.PYTHON3,
        100: PythonVersion.PYMANAGER,
    }
    return mapping.get(django_version, PythonVersion.PYTHON3)


def normalize_url(url: str) -> str:
    """Normalize URLs to include full domain if needed."""
    if not url:
        return ""
    if url.startswith("/"):
        return f"{PYTHON_ORG_BASE_URL}{url}"
    return url


def parse_datetime(dt_str: str | None) -> datetime | None:
    """Parse Django datetime string."""
    if not dt_str:
        return None
    try:
        return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
    except (ValueError, TypeError):
        return None


async def import_os_entries(
    session: AsyncSession,
    fixtures: list[dict[str, Any]],
    dry_run: bool = False,
) -> dict[int, OS]:
    """Import OS entries and return mapping of old pk to new model."""
    os_fixtures = [f for f in fixtures if f["model"] == "downloads.os"]
    pk_to_model: dict[int, OS] = {}

    logger.info(f"Found {len(os_fixtures)} OS entries to import")

    for fixture in os_fixtures:
        pk = fixture["pk"]
        fields = fixture["fields"]

        # Check if already exists
        existing = await session.execute(select(OS).where(OS.slug == fields["slug"]))
        existing_os = existing.scalar_one_or_none()

        if existing_os:
            logger.debug(f"OS '{fields['name']}' already exists, skipping")
            pk_to_model[pk] = existing_os
            continue

        if dry_run:
            logger.info(f"[DRY RUN] Would create OS: {fields['name']} ({fields['slug']})")
            continue

        os_entry = OS(
            name=fields["name"],
            slug=fields["slug"],
        )
        session.add(os_entry)
        await session.flush()
        pk_to_model[pk] = os_entry
        logger.info(f"Created OS: {fields['name']}")

    return pk_to_model


async def import_releases(
    session: AsyncSession,
    fixtures: list[dict[str, Any]],
    dry_run: bool = False,
) -> dict[int, Release]:
    """Import Release entries and return mapping of old pk to new model."""
    release_fixtures = [f for f in fixtures if f["model"] == "downloads.release"]
    pk_to_model: dict[int, Release] = {}

    logger.info(f"Found {len(release_fixtures)} Release entries to import")

    for fixture in release_fixtures:
        pk = fixture["pk"]
        fields = fixture["fields"]

        # Check if already exists
        existing = await session.execute(select(Release).where(Release.slug == fields["slug"]))
        existing_release = existing.scalar_one_or_none()

        if existing_release:
            logger.debug(f"Release '{fields['name']}' already exists, skipping")
            pk_to_model[pk] = existing_release
            continue

        if dry_run:
            logger.info(f"[DRY RUN] Would create Release: {fields['name']}")
            continue

        release_date = None
        if fields.get("release_date"):
            dt = parse_datetime(fields["release_date"])
            if dt:
                release_date = dt.date()

        release = Release(
            name=fields["name"],
            slug=fields["slug"],
            version=map_version(fields.get("version", 3)),
            is_latest=fields.get("is_latest", False),
            is_published=fields.get("is_published", True),
            pre_release=fields.get("pre_release", False),
            show_on_download_page=fields.get("show_on_download_page", True),
            release_date=release_date,
            release_notes_url=normalize_url(fields.get("release_notes_url", "")),
            content=fields.get("content", ""),
        )
        session.add(release)
        await session.flush()
        pk_to_model[pk] = release
        logger.debug(f"Created Release: {fields['name']}")

    logger.info(f"Imported {len([r for r in pk_to_model.values() if r.id])} new releases")
    return pk_to_model


async def import_release_files(
    session: AsyncSession,
    fixtures: list[dict[str, Any]],
    os_map: dict[int, OS],
    release_map: dict[int, Release],
    dry_run: bool = False,
) -> int:
    """Import ReleaseFile entries."""
    file_fixtures = [f for f in fixtures if f["model"] == "downloads.releasefile"]

    logger.info(f"Found {len(file_fixtures)} ReleaseFile entries to import")

    imported = 0
    skipped = 0
    errors = 0

    for fixture in file_fixtures:
        fields = fixture["fields"]

        os_pk = fields.get("os")
        release_pk = fields.get("release")

        if os_pk not in os_map:
            logger.warning(f"OS pk {os_pk} not found for file '{fields['name']}', skipping")
            errors += 1
            continue

        if release_pk not in release_map:
            logger.warning(f"Release pk {release_pk} not found for file '{fields['name']}', skipping")
            errors += 1
            continue

        os_entry = os_map[os_pk]
        release = release_map[release_pk]

        # Check if already exists by slug
        existing = await session.execute(select(ReleaseFile).where(ReleaseFile.slug == fields["slug"]))
        if existing.scalar_one_or_none():
            skipped += 1
            continue

        if dry_run:
            logger.debug(f"[DRY RUN] Would create ReleaseFile: {fields['name']}")
            imported += 1
            continue

        release_file = ReleaseFile(
            name=fields["name"],
            slug=fields["slug"],
            release_id=release.id,
            os_id=os_entry.id,
            description=fields.get("description", ""),
            is_source=fields.get("is_source", False),
            url=normalize_url(fields.get("url", "")),
            gpg_signature_file=normalize_url(fields.get("gpg_signature_file", "")),
            sigstore_signature_file=normalize_url(fields.get("sigstore_signature_file", "")),
            sigstore_cert_file=normalize_url(fields.get("sigstore_cert_file", "")),
            sigstore_bundle_file=normalize_url(fields.get("sigstore_bundle_file", "")),
            sbom_spdx2_file=normalize_url(fields.get("sbom_spdx2_file", "")),
            md5_sum=fields.get("md5_sum", ""),
            filesize=fields.get("filesize", 0),
            download_button=fields.get("download_button", False),
        )
        session.add(release_file)
        imported += 1

        # Flush periodically to avoid memory issues
        if imported % 100 == 0:
            await session.flush()
            logger.info(f"Progress: {imported} files imported...")

    logger.info(f"Imported {imported} release files, skipped {skipped}, errors {errors}")
    return imported


async def run_import(fixture_path: Path, dry_run: bool = False) -> None:
    """Run the full import process."""
    logger.info(f"Loading fixtures from {fixture_path}")

    if not fixture_path.exists():
        logger.error(f"Fixture file not found: {fixture_path}")
        sys.exit(1)

    with fixture_path.open() as f:
        fixtures = json.load(f)

    logger.info(f"Loaded {len(fixtures)} fixture entries")

    # Create database connection
    engine = get_engine()
    session_factory = get_async_session_factory()

    async with session_factory() as session:
        try:
            # Import in order: OS -> Release -> ReleaseFile
            os_map = await import_os_entries(session, fixtures, dry_run)
            release_map = await import_releases(session, fixtures, dry_run)
            await import_release_files(session, fixtures, os_map, release_map, dry_run)

            if not dry_run:
                await session.commit()
                logger.info("Import completed successfully!")
            else:
                logger.info("[DRY RUN] No changes made to database")

        except Exception:
            logger.exception("Import failed")
            await session.rollback()
            raise
        finally:
            await engine.dispose()


@click.command()
@click.option(
    "--fixture-path",
    type=click.Path(exists=True, path_type=Path),
    default=DEFAULT_FIXTURE_PATH,
    help="Path to Django fixture JSON file",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Show what would be imported without making changes",
)
def main(fixture_path: Path, dry_run: bool) -> None:
    """Import Python downloads data from Django fixtures."""
    asyncio.run(run_import(fixture_path, dry_run))


if __name__ == "__main__":
    main()
