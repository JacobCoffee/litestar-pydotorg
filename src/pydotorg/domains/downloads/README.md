# Downloads Domain

The downloads domain handles Python releases, release files, and operating systems for the Python.org download pages.

## Structure

```
downloads/
├── __init__.py           # Domain exports
├── controllers.py        # API and page controllers
├── urls.py              # URL constants
├── dependencies.py      # Dependency injection providers
├── services.py          # Business logic layer
├── schemas.py           # Pydantic schemas
├── repositories.py      # Database access layer
├── models.py            # SQLAlchemy models
└── README.md            # This file
```

## Models

### OS
Represents an operating system (Windows, macOS, Linux, etc.)

**Fields:**
- `name`: OS display name
- `slug`: URL-safe identifier
- `releases`: Related release files

### Release
Represents a Python release version

**Fields:**
- `name`: Release name (e.g., "Python 3.12.0")
- `slug`: URL-safe identifier
- `version`: Python version (PythonVersion enum: PYTHON1, PYTHON2, PYTHON3, PYMANAGER)
- `is_latest`: Flag for latest release in version
- `is_published`: Publication status
- `pre_release`: Pre-release flag
- `show_on_download_page`: Display on download page
- `release_date`: Release date
- `release_page_id`: FK to pages domain
- `release_notes_url`: URL to release notes
- `content`: Markdown/HTML content
- `files`: Related release files

**Methods:**
- `is_version_at_least(min_version)`: Check version >= min_version
- `is_version_at_least_3_5`: Check if version >= 3.5
- `is_version_at_least_3_9`: Check if version >= 3.9
- `is_version_at_least_3_14`: Check if version >= 3.14
- `files_for_os(os_slug)`: Get files for specific OS
- `download_file_for_os(os_slug)`: Get download button file for OS

### ReleaseFile
Represents a downloadable file for a release

**Fields:**
- `release_id`: FK to Release
- `os_id`: FK to OS
- `name`: File display name
- `slug`: URL-safe identifier
- `description`: File description
- `is_source`: Source code flag
- `url`: Download URL
- `gpg_signature_file`: GPG signature URL
- `sigstore_signature_file`: Sigstore signature URL
- `sigstore_cert_file`: Sigstore certificate URL
- `sigstore_bundle_file`: Sigstore bundle URL
- `sbom_spdx2_file`: SBOM SPDX file URL
- `md5_sum`: MD5 checksum
- `filesize`: File size in bytes
- `download_button`: Primary download button flag

## API Endpoints

### OS Endpoints
- `GET /api/v1/os` - List all operating systems
- `GET /api/v1/os/{os_id}` - Get OS by ID
- `GET /api/v1/os/slug/{slug}` - Get OS by slug
- `POST /api/v1/os` - Create new OS
- `DELETE /api/v1/os/{os_id}` - Delete OS

### Release Endpoints
- `GET /api/v1/releases` - List all releases
- `GET /api/v1/releases/{release_id}` - Get release by ID
- `GET /api/v1/releases/slug/{slug}` - Get release by slug
- `GET /api/v1/releases/latest` - Get latest Python 3 release
- `GET /api/v1/releases/latest/{version}` - Get latest release for version
- `GET /api/v1/releases/published` - List published releases
- `GET /api/v1/releases/download-page` - List releases for download page
- `POST /api/v1/releases` - Create new release
- `PUT /api/v1/releases/{release_id}` - Update release
- `DELETE /api/v1/releases/{release_id}` - Delete release

### Release File Endpoints
- `GET /api/v1/files/{file_id}` - Get file by ID
- `GET /api/v1/files/release/{release_id}` - List files for release
- `GET /api/v1/files/os/{os_id}` - List files for OS
- `GET /api/v1/files/slug/{slug}` - Get file by slug
- `POST /api/v1/files` - Create new file
- `DELETE /api/v1/files/{file_id}` - Delete file

### Public Download Pages (HTML)
- `GET /downloads/` - Main downloads page
- `GET /downloads/release/{slug}/` - Release detail page
- `GET /downloads/source/` - Source downloads page
- `GET /downloads/windows/` - Windows downloads page
- `GET /downloads/macos/` - macOS downloads page

## Services

### OSService
Business logic for operating systems

**Methods:**
- `get_by_slug(slug)`: Get OS by slug

### ReleaseService
Business logic for releases with version comparison

**Methods:**
- `get_by_slug(slug)`: Get release by slug
- `get_latest(version)`: Get latest release for Python version
- `get_published(limit, offset)`: Get published releases
- `get_for_download_page(limit)`: Get releases for download page
- `get_by_version(version, limit)`: Get releases by Python version
- `get_files_grouped_by_os(release_id)`: Get files grouped by OS slug
- `mark_as_latest(release_id, version)`: Mark release as latest for version

### ReleaseFileService
Business logic for release files

**Methods:**
- `get_by_release_id(release_id)`: Get files for release
- `get_by_os_id(os_id, limit)`: Get files for OS
- `get_by_slug(slug)`: Get file by slug
- `get_source_files(release_id)`: Get source files for release
- `get_download_button_file(release_id, os_id)`: Get primary download file

## Repositories

### OSRepository
Database access for OS model

**Methods:**
- `get_by_slug(slug)`: Get OS by slug

### ReleaseRepository
Database access for Release model with optimized queries

**Methods:**
- `get_by_slug(slug)`: Get release by slug
- `get_latest(version)`: Get latest published release for version
- `get_published(limit, offset)`: Get published releases
- `get_for_download_page(limit)`: Get releases for download page
- `get_by_version(version, limit)`: Get releases by version

### ReleaseFileRepository
Database access for ReleaseFile model

**Methods:**
- `get_by_release_id(release_id)`: Get files for release
- `get_by_os_id(os_id, limit)`: Get files for OS
- `get_by_slug(slug)`: Get file by slug
- `get_source_files(release_id)`: Get source files

## Usage Examples

### Get Latest Python 3 Release
```python
latest = await release_service.get_latest(PythonVersion.PYTHON3)
```

### Get Files Grouped by OS
```python
files_by_os = await release_service.get_files_grouped_by_os(release_id)
# Returns: {"windows": [...], "macos": [...], "source": [...]}
```

### Check Version
```python
if release.is_version_at_least_3_9:
    # Use features available in Python 3.9+
    pass
```

### Get Download Button File
```python
download_file = release.download_file_for_os("windows")
```

## Dependencies

To use the downloads domain, register dependencies in your Litestar app:

```python
from pydotorg.domains.downloads import get_downloads_dependencies

app = Litestar(
    dependencies=get_downloads_dependencies(),
    # ...
)
```

## Templates

The page controllers expect the following Jinja2 templates:

- `downloads/index.html.jinja2` - Main downloads page
- `downloads/release.html.jinja2` - Release detail page
- `downloads/source.html.jinja2` - Source downloads page
- `downloads/windows.html.jinja2` - Windows downloads page
- `downloads/macos.html.jinja2` - macOS downloads page

## Version Comparison Logic

The `Release` model includes methods for version comparison:

```python
release = Release(name="Python 3.12.0")
release.is_version_at_least((3, 9))  # True
release.is_version_at_least_3_14     # False
```

Version parsing extracts the major and minor version numbers from the release name.

## Testing

All services and repositories are fully async and testable:

```python
async def test_get_latest_release():
    async with ReleaseService(repository=release_repository) as service:
        latest = await service.get_latest(PythonVersion.PYTHON3)
        assert latest is not None
        assert latest.is_latest is True
```
