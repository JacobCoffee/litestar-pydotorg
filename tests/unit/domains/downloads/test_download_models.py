"""Unit tests for Download models."""

from __future__ import annotations

from datetime import date
from uuid import uuid4

from pydotorg.domains.downloads.models import OS, PythonVersion, Release, ReleaseFile


class TestPythonVersionEnum:
    def test_enum_values(self) -> None:
        assert PythonVersion.PYTHON1.value == "1"
        assert PythonVersion.PYTHON2.value == "2"
        assert PythonVersion.PYTHON3.value == "3"
        assert PythonVersion.PYMANAGER.value == "manager"

    def test_enum_members(self) -> None:
        members = list(PythonVersion)
        assert len(members) == 4
        assert PythonVersion.PYTHON1 in members
        assert PythonVersion.PYTHON2 in members
        assert PythonVersion.PYTHON3 in members
        assert PythonVersion.PYMANAGER in members


class TestOSModel:
    def test_create_os(self) -> None:
        os = OS(name="Windows", slug="windows")
        assert os.name == "Windows"
        assert os.slug == "windows"


class TestReleaseModel:
    def test_create_release(self) -> None:
        release = Release(
            name="3.12.0",
            slug="3-12-0",
            version=PythonVersion.PYTHON3,
        )
        assert release.name == "3.12.0"
        assert release.slug == "3-12-0"
        assert release.version == PythonVersion.PYTHON3

    def test_release_explicit_values(self) -> None:
        release = Release(
            name="3.12.0",
            slug="3-12-0",
            version=PythonVersion.PYTHON3,
            is_latest=False,
            is_published=False,
            pre_release=False,
            show_on_download_page=True,
            release_notes_url="",
            content="",
        )
        assert release.version == PythonVersion.PYTHON3
        assert release.is_latest is False
        assert release.is_published is False
        assert release.pre_release is False
        assert release.show_on_download_page is True
        assert release.release_date is None
        assert release.release_notes_url == ""
        assert release.content == ""

    def test_is_version_at_least_3_5(self) -> None:
        release = Release(name="3.12.0", slug="3-12-0", version=PythonVersion.PYTHON3)
        assert release.is_version_at_least((3, 5)) is True

    def test_is_version_at_least_3_12(self) -> None:
        release = Release(name="3.12.0", slug="3-12-0", version=PythonVersion.PYTHON3)
        assert release.is_version_at_least((3, 12)) is True

    def test_is_version_at_least_3_13(self) -> None:
        release = Release(name="3.12.0", slug="3-12-0", version=PythonVersion.PYTHON3)
        assert release.is_version_at_least((3, 13)) is False

    def test_is_version_at_least_property_3_5(self) -> None:
        release = Release(name="3.12.0", slug="3-12-0", version=PythonVersion.PYTHON3)
        assert release.is_version_at_least_3_5 is True

    def test_is_version_at_least_property_3_9(self) -> None:
        release = Release(name="3.12.0", slug="3-12-0", version=PythonVersion.PYTHON3)
        assert release.is_version_at_least_3_9 is True

    def test_is_version_at_least_property_3_14(self) -> None:
        release = Release(name="3.12.0", slug="3-12-0", version=PythonVersion.PYTHON3)
        assert release.is_version_at_least_3_14 is False

    def test_is_version_at_least_invalid_format(self) -> None:
        release = Release(name="invalid", slug="invalid", version=PythonVersion.PYTHON3)
        assert release.is_version_at_least((3, 5)) is False

    def test_is_version_at_least_python_2(self) -> None:
        release = Release(name="2.7.18", slug="2-7-18", version=PythonVersion.PYTHON2)
        assert release.is_version_at_least((2, 7)) is True
        assert release.is_version_at_least((3, 0)) is False

    def test_release_with_date(self) -> None:
        release_date = date(2024, 1, 1)
        release = Release(
            name="3.13.0",
            slug="3-13-0",
            version=PythonVersion.PYTHON3,
            release_date=release_date,
        )
        assert release.release_date == release_date

    def test_release_is_latest(self) -> None:
        release = Release(
            name="3.13.0",
            slug="3-13-0",
            version=PythonVersion.PYTHON3,
            is_latest=True,
        )
        assert release.is_latest is True

    def test_release_pre_release(self) -> None:
        release = Release(
            name="3.13.0rc1",
            slug="3-13-0rc1",
            version=PythonVersion.PYTHON3,
            pre_release=True,
        )
        assert release.pre_release is True

    def test_release_not_on_download_page(self) -> None:
        release = Release(
            name="3.0.0",
            slug="3-0-0",
            version=PythonVersion.PYTHON3,
            show_on_download_page=False,
        )
        assert release.show_on_download_page is False


class TestReleaseFileModel:
    def test_create_release_file(self) -> None:
        release_id = uuid4()
        os_id = uuid4()
        file = ReleaseFile(
            name="Python 3.12.0 Windows installer",
            slug="python-3-12-0-windows",
            release_id=release_id,
            os_id=os_id,
            url="https://www.python.org/ftp/python/3.12.0/python-3.12.0.exe",
        )
        assert file.name == "Python 3.12.0 Windows installer"
        assert file.release_id == release_id
        assert file.os_id == os_id
        assert file.url == "https://www.python.org/ftp/python/3.12.0/python-3.12.0.exe"

    def test_release_file_explicit_values(self) -> None:
        file = ReleaseFile(
            name="Test File",
            slug="test-file",
            release_id=uuid4(),
            os_id=uuid4(),
            url="https://example.com/file",
            description="",
            is_source=False,
            gpg_signature_file="",
            sigstore_signature_file="",
            sigstore_cert_file="",
            sigstore_bundle_file="",
            sbom_spdx2_file="",
            md5_sum="",
            filesize=0,
            download_button=False,
        )
        assert file.description == ""
        assert file.is_source is False
        assert file.gpg_signature_file == ""
        assert file.sigstore_signature_file == ""
        assert file.sigstore_cert_file == ""
        assert file.sigstore_bundle_file == ""
        assert file.sbom_spdx2_file == ""
        assert file.md5_sum == ""
        assert file.filesize == 0
        assert file.download_button is False

    def test_release_file_source(self) -> None:
        file = ReleaseFile(
            name="Python 3.12.0 source",
            slug="python-3-12-0-source",
            release_id=uuid4(),
            os_id=uuid4(),
            url="https://www.python.org/ftp/python/3.12.0/Python-3.12.0.tgz",
            is_source=True,
        )
        assert file.is_source is True

    def test_release_file_with_signatures(self) -> None:
        file = ReleaseFile(
            name="Test",
            slug="test",
            release_id=uuid4(),
            os_id=uuid4(),
            url="https://example.com/file",
            gpg_signature_file="https://example.com/file.asc",
            sigstore_signature_file="https://example.com/file.sig",
            sigstore_cert_file="https://example.com/file.crt",
            sigstore_bundle_file="https://example.com/file.sigstore",
            sbom_spdx2_file="https://example.com/file.spdx.json",
            md5_sum="abc123",
            filesize=1024000,
        )
        assert file.gpg_signature_file == "https://example.com/file.asc"
        assert file.sigstore_signature_file == "https://example.com/file.sig"
        assert file.sigstore_cert_file == "https://example.com/file.crt"
        assert file.sigstore_bundle_file == "https://example.com/file.sigstore"
        assert file.sbom_spdx2_file == "https://example.com/file.spdx.json"
        assert file.md5_sum == "abc123"
        assert file.filesize == 1024000

    def test_release_file_download_button(self) -> None:
        file = ReleaseFile(
            name="Test",
            slug="test",
            release_id=uuid4(),
            os_id=uuid4(),
            url="https://example.com/file",
            download_button=True,
        )
        assert file.download_button is True
