"""Database seeding script for development and testing."""

from __future__ import annotations

import asyncio
import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory
from sqlalchemy import select

from pydotorg.core.auth.password import password_service
from pydotorg.core.database.session import async_session_factory
from pydotorg.domains.banners.models import Banner
from pydotorg.domains.blogs.models import BlogEntry, Feed, FeedAggregate, RelatedBlog
from pydotorg.domains.codesamples.models import CodeSample
from pydotorg.domains.community.models import Link, Photo, Post, Video
from pydotorg.domains.downloads.models import OS, PythonVersion, Release, ReleaseFile, ReleaseStatus
from pydotorg.domains.events.models import Calendar, Event, EventCategory, EventLocation, EventOccurrence
from pydotorg.domains.jobs.models import Job, JobCategory, JobReviewComment, JobStatus, JobType
from pydotorg.domains.minutes.models import Minutes
from pydotorg.domains.nominations.models import Election, Nomination, Nominee
from pydotorg.domains.pages.models import ContentType, Page
from pydotorg.domains.sponsors.models import Sponsor, Sponsorship, SponsorshipLevel, SponsorshipStatus
from pydotorg.domains.successstories.models import Story, StoryCategory
from pydotorg.domains.users.models import EmailPrivacy, Membership, MembershipType, SearchVisibility, User
from pydotorg.domains.work_groups.models import WorkGroup

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

VOTING_THRESHOLD = 3
SPONSOR_THRESHOLD = 3
FEE_THRESHOLD = 2
MEMBERSHIP_SUPPORTING_INDEX = 2


class UserFactory(SQLAlchemyFactory[User]):
    __model__ = User
    __set_relationships__ = False

    @classmethod
    def password_hash(cls) -> str:
        return password_service.hash_password("password123")

    @classmethod
    def is_active(cls) -> bool:
        return True

    @classmethod
    def is_staff(cls) -> bool:
        return False

    @classmethod
    def is_superuser(cls) -> bool:
        return False

    @classmethod
    def search_visibility(cls) -> SearchVisibility:
        return SearchVisibility.PUBLIC

    @classmethod
    def email_privacy(cls) -> EmailPrivacy:
        return EmailPrivacy.PRIVATE

    @classmethod
    def public_profile(cls) -> bool:
        return True


class MembershipFactory(SQLAlchemyFactory[Membership]):
    __model__ = Membership
    __set_relationships__ = False

    @classmethod
    def membership_type(cls) -> MembershipType:
        return MembershipType.BASIC

    @classmethod
    def psf_code_of_conduct(cls) -> bool:
        return True

    @classmethod
    def psf_announcements(cls) -> bool:
        return False

    @classmethod
    def votes(cls) -> bool:
        return False


class PageFactory(SQLAlchemyFactory[Page]):
    __model__ = Page
    __set_relationships__ = False

    @classmethod
    def is_published(cls) -> bool:
        return True

    @classmethod
    def template_name(cls) -> str:
        return "pages/default.html"

    @classmethod
    def creator_id(cls) -> None:
        return None

    @classmethod
    def last_modified_by_id(cls) -> None:
        return None


class OSFactory(SQLAlchemyFactory[OS]):
    __model__ = OS
    __set_relationships__ = False

    @classmethod
    def creator_id(cls) -> None:
        return None

    @classmethod
    def last_modified_by_id(cls) -> None:
        return None


class ReleaseFactory(SQLAlchemyFactory[Release]):
    __model__ = Release
    __set_relationships__ = False

    @classmethod
    def creator_id(cls) -> None:
        return None

    @classmethod
    def last_modified_by_id(cls) -> None:
        return None

    @classmethod
    def release_page_id(cls) -> None:
        return None

    @classmethod
    def is_published(cls) -> bool:
        return True

    @classmethod
    def is_latest(cls) -> bool:
        return False

    @classmethod
    def pre_release(cls) -> bool:
        return False

    @classmethod
    def show_on_download_page(cls) -> bool:
        return True


class ReleaseFileFactory(SQLAlchemyFactory[ReleaseFile]):
    __model__ = ReleaseFile
    __set_relationships__ = False

    @classmethod
    def creator_id(cls) -> None:
        return None

    @classmethod
    def last_modified_by_id(cls) -> None:
        return None

    @classmethod
    def is_source(cls) -> bool:
        return False

    @classmethod
    def download_button(cls) -> bool:
        return False

    @classmethod
    def filesize(cls) -> int:
        return 50000000


class SponsorFactory(SQLAlchemyFactory[Sponsor]):
    __model__ = Sponsor
    __set_relationships__ = False

    @classmethod
    def creator_id(cls) -> None:
        return None

    @classmethod
    def last_modified_by_id(cls) -> None:
        return None


class SponsorshipFactory(SQLAlchemyFactory[Sponsorship]):
    __model__ = Sponsorship
    __set_relationships__ = False

    @classmethod
    def creator_id(cls) -> None:
        return None

    @classmethod
    def last_modified_by_id(cls) -> None:
        return None

    @classmethod
    def submitted_by_id(cls) -> None:
        return None

    @classmethod
    def status(cls) -> SponsorshipStatus:
        return SponsorshipStatus.APPROVED

    @classmethod
    def locked(cls) -> bool:
        return False

    @classmethod
    def sponsorship_fee(cls) -> Decimal:
        return Decimal("5000.00")

    @classmethod
    def for_modified_package(cls) -> bool:
        return False

    @classmethod
    def renewal(cls) -> bool:
        return False


async def seed_users(session: AsyncSession, count: int = 10) -> list[User]:
    """Seed user accounts."""
    users = []

    superuser = User(
        username="admin",
        email="admin@python.org",
        password_hash=password_service.hash_password("admin123"),
        first_name="Admin",
        last_name="User",
        is_active=True,
        is_staff=True,
        is_superuser=True,
        date_joined=datetime.datetime.now(tz=datetime.UTC),
        bio="System administrator",
        search_visibility=SearchVisibility.PUBLIC,
        email_privacy=EmailPrivacy.PRIVATE,
        public_profile=True,
    )
    session.add(superuser)
    users.append(superuser)

    test_user = User(
        username="testuser",
        email="test@python.org",
        password_hash=password_service.hash_password("test123"),
        first_name="Test",
        last_name="User",
        is_active=True,
        is_staff=False,
        is_superuser=False,
        date_joined=datetime.datetime.now(tz=datetime.UTC),
        bio="Test account",
        search_visibility=SearchVisibility.PUBLIC,
        email_privacy=EmailPrivacy.PRIVATE,
        public_profile=True,
    )
    session.add(test_user)
    users.append(test_user)

    for _ in range(count - 2):
        user = UserFactory.build()
        session.add(user)
        users.append(user)

    await session.flush()
    return users


async def seed_memberships(session: AsyncSession, users: list[User]) -> list[Membership]:
    """Seed user memberships."""
    memberships = []

    for i, user in enumerate(users[:5]):
        membership_type = (
            MembershipType.FELLOW
            if i == 0
            else MembershipType.CONTRIBUTING
            if i == 1
            else MembershipType.SUPPORTING
            if i == MEMBERSHIP_SUPPORTING_INDEX
            else MembershipType.BASIC
        )

        membership = Membership(
            user_id=user.id,
            membership_type=membership_type,
            legal_name=user.full_name,
            preferred_name=user.full_name,
            email_address=user.email,
            city="San Francisco",
            region="CA",
            country="USA",
            postal_code="94102",
            psf_code_of_conduct=True,
            psf_announcements=i % 2 == 0,
            votes=i < VOTING_THRESHOLD,
            last_vote_affirmation=datetime.datetime.now(tz=datetime.UTC).date() if i < VOTING_THRESHOLD else None,
        )
        session.add(membership)
        memberships.append(membership)

    await session.flush()
    return memberships


async def seed_pages(session: AsyncSession, users: list[User], count: int = 15) -> list[Page]:
    """Seed content pages."""
    pages = []

    home_page = Page(
        title="Welcome to Python.org",
        keywords="python, programming, language",
        description="The official home of the Python Programming Language",
        path="/",
        content="# Welcome to Python.org\n\nPython is a programming language that lets you work quickly and integrate systems more effectively.",
        is_published=True,
        template_name="pages/home.html",
        creator_id=users[0].id,
    )
    session.add(home_page)
    pages.append(home_page)

    about_page = Page(
        title="About Python",
        keywords="python, about, history",
        description="Learn about the Python programming language",
        path="/about",
        content="# About Python\n\nPython is a high-level, interpreted programming language.",
        is_published=True,
        template_name="pages/default.html",
        creator_id=users[0].id,
    )
    session.add(about_page)
    pages.append(about_page)

    downloads_page = Page(
        title="Download Python",
        keywords="python, download, install",
        description="Download the latest version of Python",
        path="/downloads",
        content="# Download Python\n\nGet started with Python today!",
        is_published=True,
        template_name="pages/downloads.html",
        creator_id=users[0].id,
    )
    session.add(downloads_page)
    pages.append(downloads_page)

    for i in range(count - 3):
        page = PageFactory.build(creator_id=users[i % len(users)].id)
        session.add(page)
        pages.append(page)

    await session.flush()
    return pages


async def seed_operating_systems(session: AsyncSession, users: list[User]) -> list[OS]:
    """Seed operating systems."""
    os_list = []

    os_data = [
        ("Windows", "windows"),
        ("macOS", "macos"),
        ("Linux", "linux"),
        ("Source", "source"),
    ]

    for name, slug in os_data:
        os_obj = OS(
            name=name,
            slug=slug,
            creator_id=users[0].id,
        )
        session.add(os_obj)
        os_list.append(os_obj)

    await session.flush()
    return os_list


async def seed_releases(
    session: AsyncSession,
    users: list[User],
    os_list: list[OS],
    count: int = 100,
) -> list[Release]:
    """Seed Python releases with accurate data from python.org."""
    releases = []

    release_data = [
        # Python 3.14 - Bugfix (latest)
        (
            "3.14.0",
            datetime.date(2025, 10, 7),
            ReleaseStatus.BUGFIX,
            datetime.date(2030, 10, 31),
            True,
            False,
            PythonVersion.PYTHON3,
        ),
        # Python 3.13 - Bugfix
        (
            "3.13.9",
            datetime.date(2025, 10, 14),
            ReleaseStatus.BUGFIX,
            datetime.date(2029, 10, 31),
            False,
            False,
            PythonVersion.PYTHON3,
        ),
        (
            "3.13.8",
            datetime.date(2025, 10, 7),
            ReleaseStatus.BUGFIX,
            datetime.date(2029, 10, 31),
            False,
            False,
            PythonVersion.PYTHON3,
        ),
        (
            "3.13.7",
            datetime.date(2025, 8, 14),
            ReleaseStatus.BUGFIX,
            datetime.date(2029, 10, 31),
            False,
            False,
            PythonVersion.PYTHON3,
        ),
        (
            "3.13.5",
            datetime.date(2025, 6, 11),
            ReleaseStatus.BUGFIX,
            datetime.date(2029, 10, 31),
            False,
            False,
            PythonVersion.PYTHON3,
        ),
        (
            "3.13.3",
            datetime.date(2025, 4, 8),
            ReleaseStatus.BUGFIX,
            datetime.date(2029, 10, 31),
            False,
            False,
            PythonVersion.PYTHON3,
        ),
        (
            "3.13.1",
            datetime.date(2024, 12, 3),
            ReleaseStatus.BUGFIX,
            datetime.date(2029, 10, 31),
            False,
            False,
            PythonVersion.PYTHON3,
        ),
        (
            "3.13.0",
            datetime.date(2024, 10, 7),
            ReleaseStatus.BUGFIX,
            datetime.date(2029, 10, 31),
            False,
            False,
            PythonVersion.PYTHON3,
        ),
        # Python 3.12 - Security
        (
            "3.12.12",
            datetime.date(2025, 10, 9),
            ReleaseStatus.SECURITY,
            datetime.date(2028, 10, 31),
            False,
            False,
            PythonVersion.PYTHON3,
        ),
        (
            "3.12.10",
            datetime.date(2025, 4, 8),
            ReleaseStatus.SECURITY,
            datetime.date(2028, 10, 31),
            False,
            False,
            PythonVersion.PYTHON3,
        ),
        (
            "3.12.8",
            datetime.date(2024, 12, 3),
            ReleaseStatus.SECURITY,
            datetime.date(2028, 10, 31),
            False,
            False,
            PythonVersion.PYTHON3,
        ),
        (
            "3.12.7",
            datetime.date(2024, 10, 1),
            ReleaseStatus.SECURITY,
            datetime.date(2028, 10, 31),
            False,
            False,
            PythonVersion.PYTHON3,
        ),
        (
            "3.12.4",
            datetime.date(2024, 6, 6),
            ReleaseStatus.SECURITY,
            datetime.date(2028, 10, 31),
            False,
            False,
            PythonVersion.PYTHON3,
        ),
        (
            "3.12.0",
            datetime.date(2023, 10, 2),
            ReleaseStatus.SECURITY,
            datetime.date(2028, 10, 31),
            False,
            False,
            PythonVersion.PYTHON3,
        ),
        # Python 3.11 - Security
        (
            "3.11.14",
            datetime.date(2025, 10, 9),
            ReleaseStatus.SECURITY,
            datetime.date(2027, 10, 31),
            False,
            False,
            PythonVersion.PYTHON3,
        ),
        (
            "3.11.11",
            datetime.date(2024, 12, 3),
            ReleaseStatus.SECURITY,
            datetime.date(2027, 10, 31),
            False,
            False,
            PythonVersion.PYTHON3,
        ),
        (
            "3.11.9",
            datetime.date(2024, 4, 2),
            ReleaseStatus.SECURITY,
            datetime.date(2027, 10, 31),
            False,
            False,
            PythonVersion.PYTHON3,
        ),
        (
            "3.11.0",
            datetime.date(2022, 10, 24),
            ReleaseStatus.SECURITY,
            datetime.date(2027, 10, 31),
            False,
            False,
            PythonVersion.PYTHON3,
        ),
        # Python 3.10 - Security
        (
            "3.10.19",
            datetime.date(2025, 10, 9),
            ReleaseStatus.SECURITY,
            datetime.date(2026, 10, 31),
            False,
            False,
            PythonVersion.PYTHON3,
        ),
        (
            "3.10.16",
            datetime.date(2024, 12, 3),
            ReleaseStatus.SECURITY,
            datetime.date(2026, 10, 31),
            False,
            False,
            PythonVersion.PYTHON3,
        ),
        (
            "3.10.14",
            datetime.date(2024, 3, 19),
            ReleaseStatus.SECURITY,
            datetime.date(2026, 10, 31),
            False,
            False,
            PythonVersion.PYTHON3,
        ),
        (
            "3.10.0",
            datetime.date(2021, 10, 4),
            ReleaseStatus.SECURITY,
            datetime.date(2026, 10, 31),
            False,
            False,
            PythonVersion.PYTHON3,
        ),
        # Python 3.9 - EOL
        (
            "3.9.25",
            datetime.date(2025, 10, 31),
            ReleaseStatus.EOL,
            datetime.date(2025, 10, 31),
            False,
            False,
            PythonVersion.PYTHON3,
        ),
        (
            "3.9.21",
            datetime.date(2024, 12, 3),
            ReleaseStatus.EOL,
            datetime.date(2025, 10, 31),
            False,
            False,
            PythonVersion.PYTHON3,
        ),
        (
            "3.9.19",
            datetime.date(2024, 3, 19),
            ReleaseStatus.EOL,
            datetime.date(2025, 10, 31),
            False,
            False,
            PythonVersion.PYTHON3,
        ),
        (
            "3.9.0",
            datetime.date(2020, 10, 5),
            ReleaseStatus.EOL,
            datetime.date(2025, 10, 31),
            False,
            False,
            PythonVersion.PYTHON3,
        ),
        # Python 3.8 - EOL
        (
            "3.8.20",
            datetime.date(2024, 9, 6),
            ReleaseStatus.EOL,
            datetime.date(2024, 10, 31),
            False,
            False,
            PythonVersion.PYTHON3,
        ),
        (
            "3.8.18",
            datetime.date(2023, 8, 24),
            ReleaseStatus.EOL,
            datetime.date(2024, 10, 31),
            False,
            False,
            PythonVersion.PYTHON3,
        ),
        (
            "3.8.0",
            datetime.date(2019, 10, 14),
            ReleaseStatus.EOL,
            datetime.date(2024, 10, 31),
            False,
            False,
            PythonVersion.PYTHON3,
        ),
        # Python 3.7 - EOL
        (
            "3.7.17",
            datetime.date(2023, 6, 6),
            ReleaseStatus.EOL,
            datetime.date(2023, 6, 27),
            False,
            False,
            PythonVersion.PYTHON3,
        ),
        (
            "3.7.0",
            datetime.date(2018, 6, 27),
            ReleaseStatus.EOL,
            datetime.date(2023, 6, 27),
            False,
            False,
            PythonVersion.PYTHON3,
        ),
        # Python 3.6 - EOL
        (
            "3.6.15",
            datetime.date(2021, 9, 4),
            ReleaseStatus.EOL,
            datetime.date(2021, 12, 23),
            False,
            False,
            PythonVersion.PYTHON3,
        ),
        (
            "3.6.0",
            datetime.date(2016, 12, 23),
            ReleaseStatus.EOL,
            datetime.date(2021, 12, 23),
            False,
            False,
            PythonVersion.PYTHON3,
        ),
        # Python 2.7 - EOL
        (
            "2.7.18",
            datetime.date(2020, 4, 20),
            ReleaseStatus.EOL,
            datetime.date(2020, 1, 1),
            False,
            False,
            PythonVersion.PYTHON2,
        ),
        (
            "2.7.17",
            datetime.date(2019, 10, 19),
            ReleaseStatus.EOL,
            datetime.date(2020, 1, 1),
            False,
            False,
            PythonVersion.PYTHON2,
        ),
        (
            "2.7.16",
            datetime.date(2019, 3, 4),
            ReleaseStatus.EOL,
            datetime.date(2020, 1, 1),
            False,
            False,
            PythonVersion.PYTHON2,
        ),
        (
            "2.7.0",
            datetime.date(2010, 7, 3),
            ReleaseStatus.EOL,
            datetime.date(2020, 1, 1),
            False,
            False,
            PythonVersion.PYTHON2,
        ),
        # Python 1.x - Ancient EOL releases
        (
            "1.6.1",
            datetime.date(2000, 9, 1),
            ReleaseStatus.EOL,
            datetime.date(2000, 9, 1),
            False,
            False,
            PythonVersion.PYTHON1,
        ),
        (
            "1.6",
            datetime.date(2000, 9, 5),
            ReleaseStatus.EOL,
            datetime.date(2000, 9, 5),
            False,
            False,
            PythonVersion.PYTHON1,
        ),
        (
            "1.5.2",
            datetime.date(1999, 4, 13),
            ReleaseStatus.EOL,
            datetime.date(1999, 4, 13),
            False,
            False,
            PythonVersion.PYTHON1,
        ),
        (
            "1.5.1",
            datetime.date(1998, 4, 14),
            ReleaseStatus.EOL,
            datetime.date(1998, 4, 14),
            False,
            False,
            PythonVersion.PYTHON1,
        ),
        (
            "1.5",
            datetime.date(1998, 1, 3),
            ReleaseStatus.EOL,
            datetime.date(1998, 1, 3),
            False,
            False,
            PythonVersion.PYTHON1,
        ),
        (
            "1.4",
            datetime.date(1996, 10, 25),
            ReleaseStatus.EOL,
            datetime.date(1996, 10, 25),
            False,
            False,
            PythonVersion.PYTHON1,
        ),
        (
            "1.3",
            datetime.date(1995, 10, 13),
            ReleaseStatus.EOL,
            datetime.date(1995, 10, 13),
            False,
            False,
            PythonVersion.PYTHON1,
        ),
        (
            "1.2",
            datetime.date(1995, 4, 13),
            ReleaseStatus.EOL,
            datetime.date(1995, 4, 13),
            False,
            False,
            PythonVersion.PYTHON1,
        ),
        (
            "1.1",
            datetime.date(1994, 10, 11),
            ReleaseStatus.EOL,
            datetime.date(1994, 10, 11),
            False,
            False,
            PythonVersion.PYTHON1,
        ),
        (
            "1.0.1",
            datetime.date(1994, 2, 15),
            ReleaseStatus.EOL,
            datetime.date(1994, 2, 15),
            False,
            False,
            PythonVersion.PYTHON1,
        ),
        (
            "1.0.0",
            datetime.date(1994, 1, 26),
            ReleaseStatus.EOL,
            datetime.date(1994, 1, 26),
            False,
            False,
            PythonVersion.PYTHON1,
        ),
        (
            "0.9.9",
            datetime.date(1993, 7, 29),
            ReleaseStatus.EOL,
            datetime.date(1993, 7, 29),
            False,
            False,
            PythonVersion.PYTHON1,
        ),
        (
            "0.9.8",
            datetime.date(1993, 1, 9),
            ReleaseStatus.EOL,
            datetime.date(1993, 1, 9),
            False,
            False,
            PythonVersion.PYTHON1,
        ),
        (
            "0.9.1",
            datetime.date(1991, 2, 1),
            ReleaseStatus.EOL,
            datetime.date(1991, 2, 1),
            False,
            False,
            PythonVersion.PYTHON1,
        ),
    ]

    def get_release_notes_url(version_name: str, python_version: PythonVersion) -> str:
        """Generate the appropriate release notes URL for a Python version."""
        parts = version_name.split(".")
        major = parts[0]
        minor = parts[1] if len(parts) > 1 else "0"
        minor_version = f"{major}.{minor}"

        if python_version == PythonVersion.PYTHON3:
            return f"https://docs.python.org/{minor_version}/whatsnew/{minor_version}.html"
        if python_version == PythonVersion.PYTHON2:
            return f"https://docs.python.org/{minor_version}/whatsnew/{minor_version}.html"
        if python_version == PythonVersion.PYTHON1:
            if version_name.startswith("0."):
                return "https://www.python.org/download/releases/early/"
            return f"https://docs.python.org/release/{minor_version}/"
        return f"https://www.python.org/downloads/release/python-{version_name.replace('.', '')}/"

    def get_release_content(
        version_name: str,
        python_version: PythonVersion,
        status: ReleaseStatus,
        release_notes_url: str,
    ) -> str:
        """Generate release notes content for a Python version."""
        parts = version_name.split(".")
        major = parts[0]
        minor = parts[1] if len(parts) > 1 else "0"
        patch = parts[2] if len(parts) > 2 else "0"
        minor_version = f"{major}.{minor}"

        # Special content for Python 3.14.0
        if version_name == "3.14.0":
            return """<p><img width="538" height="507" src="https://hugovk.dev/python-3.14.png" alt="Two snakes enjoying a pie with 3.14 on the top and π crimping"></p>

<h2>This is the stable release of Python 3.14.0</h2>
<p>Python 3.14.0 is the newest major release of the Python programming language, and it contains many new features and optimizations compared to Python 3.13.</p>

<h2>Major new features of the 3.14 series, compared to 3.13</h2>
<p>Some of the major new features and changes in Python 3.14 are:</p>

<h3>New features</h3>
<ul>
    <li><a href="https://docs.python.org/3.14/whatsnew/3.14.html#whatsnew314-pep779" class="python-link">PEP 779</a>: Free-threaded Python is officially supported</li>
    <li><a href="https://docs.python.org/3.14/whatsnew/3.14.html#whatsnew314-pep649" class="python-link">PEP 649</a>: The evaluation of annotations is now deferred, improving the semantics of using annotations.</li>
    <li><a href="https://docs.python.org/3.14/whatsnew/3.14.html#whatsnew314-pep750" class="python-link">PEP 750</a>: Template string literals (t-strings) for custom string processing, using the familiar syntax of f-strings.</li>
    <li><a href="https://docs.python.org/3.14/whatsnew/3.14.html#whatsnew314-pep734" class="python-link">PEP 734</a>: Multiple interpreters in the stdlib.</li>
    <li><a href="https://docs.python.org/3.14/whatsnew/3.14.html#whatsnew314-pep784" class="python-link">PEP 784</a>: A new module <code>compression.zstd</code> providing support for the Zstandard compression algorithm.</li>
    <li><a href="https://docs.python.org/3.14/whatsnew/3.14.html#whatsnew314-pep758" class="python-link">PEP 758</a>: <code>except</code> and <code>except*</code> expressions may now omit the brackets.</li>
    <li><a href="https://docs.python.org/3.14/whatsnew/3.14.html#whatsnew314-pyrepl-highlighting" class="python-link">Syntax highlighting in PyREPL</a>, and support for color in unittest, argparse, json and calendar CLIs.</li>
    <li><a href="https://docs.python.org/3.14/whatsnew/3.14.html#whatsnew314-pep768" class="python-link">PEP 768</a>: A zero-overhead external debugger interface for CPython.</li>
    <li><a href="https://docs.python.org/3.14/whatsnew/3.14.html#uuid" class="python-link">UUID versions 6-8</a> are now supported by the <code>uuid</code> module, and generation of versions 3-5 are up to 40% faster.</li>
    <li><a href="https://docs.python.org/3.14/whatsnew/3.14.html#whatsnew314-pep765" class="python-link">PEP 765</a>: Disallow <code>return</code>/<code>break</code>/<code>continue</code> that exit a <code>finally</code> block.</li>
    <li><a href="https://docs.python.org/3.14/whatsnew/3.14.html#whatsnew314-pep741" class="python-link">PEP 741</a>: An improved C API for configuring Python.</li>
    <li>A <a href="https://docs.python.org/3.14/whatsnew/3.14.html#whatsnew314-tail-call" class="python-link">new type of interpreter</a>. For certain newer compilers, this interpreter provides significantly better performance.</li>
    <li><a href="https://docs.python.org/3.14/whatsnew/3.14.html#improved-error-messages" class="python-link">Improved error messages.</a></li>
    <li><a href="https://docs.python.org/3.14/whatsnew/3.14.html#hmac" class="python-link">Builtin implementation of HMAC</a> with formally verified code from the HACL* project.</li>
    <li>A <a href="https://docs.python.org/3.14/whatsnew/3.14.html#asyncio-introspection-capabilities" class="python-link">new command-line interface</a> to inspect running Python processes using asynchronous tasks.</li>
    <li>The pdb module now supports <a href="https://docs.python.org/3.14/whatsnew/3.14.html#remote-attaching-to-a-running-python-process-with-pdb" class="python-link">remote attaching to a running Python process</a>.</li>
</ul>

<p>For more details on the changes to Python 3.14, see <a href="https://docs.python.org/3.14/whatsnew/3.14.html" class="python-link">What's new in Python 3.14</a>.</p>

<h3>Build changes</h3>
<ul>
    <li><a href="https://docs.python.org/3.14/whatsnew/3.14.html#whatsnew314-pep761" class="python-link">PEP 761</a>: Python 3.14 and onwards no longer provides PGP signatures for release artifacts. Instead, Sigstore is recommended for verifiers.</li>
    <li>Official macOS and Windows release binaries include an <a href="https://docs.python.org/3.14/whatsnew/3.14.html#whatsnew314-jit-compiler" class="python-link"><em>experimental</em> JIT compiler</a>.</li>
    <li>Official <a href="https://github.com/python/cpython/issues/137242" class="python-link">Android binary releases</a> are now available.</li>
</ul>

<h3>Incompatible changes, removals and new deprecations</h3>
<ul>
    <li><a href="https://docs.python.org/3.14/whatsnew/3.14.html#incompatible-changes" class="python-link">Incompatible changes</a></li>
    <li>Python <a href="https://docs.python.org/3.14/whatsnew/3.14.html#removed" class="python-link">removals</a> and <a href="https://docs.python.org/3.14/whatsnew/3.14.html#deprecated" class="python-link">deprecations</a></li>
    <li>C API <a href="https://docs.python.org/3.14/whatsnew/3.14.html#c-api-removed" class="python-link">removals</a> and <a href="https://docs.python.org/3.14/whatsnew/3.14.html#c-api-deprecated" class="python-link">deprecations</a></li>
    <li>Overview of all <a href="https://docs.python.org/3.14/deprecations/index.html" class="python-link">pending deprecations</a></li>
</ul>

<h2>Python install manager</h2>
<p>The installer we offer for Windows is being replaced by our new install manager, which can be installed from <a href="https://apps.microsoft.com/detail/9NQ7512CXL7T" class="python-link">the Windows Store</a> or from its <a href="https://www.python.org/downloads/latest/pymanager/" class="python-link">download page</a>. See <a href="https://docs.python.org/3.14/using/windows.html" class="python-link">our documentation</a> for more information.</p>

<h2>More resources</h2>
<ul>
    <li><a href="https://docs.python.org/3.14/" class="python-link">Online documentation</a></li>
    <li><a href="https://peps.python.org/pep-0745/" class="python-link">PEP 745</a>, 3.14 Release Schedule</li>
    <li>Report bugs at <a href="https://github.com/python/cpython/issues" class="python-link">github.com/python/cpython/issues</a></li>
    <li><a href="https://www.python.org/psf/donations/python-dev/" class="python-link">Help fund Python directly</a> (or via <a href="https://github.com/sponsors/python" class="python-link">GitHub Sponsors</a>) and support <a href="https://www.python.org/psf/donations/" class="python-link">the Python community</a></li>
</ul>

<h2>Enjoy the new release</h2>
<p>Thanks to all of the many volunteers who help make Python Development and these releases possible! Please consider supporting our efforts by volunteering yourself or through organisation contributions to the <a href="https://www.python.org/psf-landing/" class="python-link">Python Software Foundation</a>.</p>

<p><a href="https://docs.python.org/3.14/whatsnew/3.14.html" class="python-link">Full Changelog</a></p>"""

        status_text = {
            ReleaseStatus.PRERELEASE: "This is a <strong>pre-release</strong> version for testing purposes.",
            ReleaseStatus.BUGFIX: "This is an <strong>active bugfix</strong> release receiving regular updates.",
            ReleaseStatus.SECURITY: "This release branch receives <strong>security fixes only</strong>.",
            ReleaseStatus.EOL: "This release has reached <strong>end of life</strong> and no longer receives updates.",
        }.get(status, "")

        if python_version == PythonVersion.PYTHON3:
            content = f"""<p>Python {version_name} is a {"patch" if int(patch) > 0 else "feature"} release of the Python {minor_version} series.</p>

<p>{status_text}</p>

<h3>Highlights</h3>
<ul>
    <li>Improved performance and stability</li>
    <li>Bug fixes and security updates</li>
    <li>Enhanced standard library modules</li>
</ul>

<p>For the complete list of changes, see the <a href="{release_notes_url}" class="python-link" target="_blank" rel="noopener">What's New in Python {minor_version}</a> documentation.</p>

<p>Full changelog available in the <a href="https://docs.python.org/{minor_version}/whatsnew/changelog.html" class="python-link" target="_blank" rel="noopener">Python {minor_version} Changelog</a>.</p>"""

        elif python_version == PythonVersion.PYTHON2:
            content = f"""<p>Python {version_name} is part of the Python 2 series, which has reached end of life.</p>

<div class="alert alert-warning my-4">
    <svg xmlns="http://www.w3.org/2000/svg" class="stroke-current shrink-0 h-6 w-6" fill="none" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
    </svg>
    <span><strong>Python 2 has reached end of life.</strong> Please upgrade to Python 3.</span>
</div>

<p>For historical documentation, see the <a href="{release_notes_url}" class="python-link" target="_blank" rel="noopener">What's New in Python {minor_version}</a>.</p>"""

        elif python_version == PythonVersion.PYTHON1:
            if version_name.startswith("0."):
                content = f"""<p>Python {version_name} is one of the earliest releases of Python, created by Guido van Rossum.</p>

<p>These early versions laid the foundation for the Python language we know today.</p>

<p>For historical information about early Python releases, see the <a href="{release_notes_url}" class="python-link" target="_blank" rel="noopener">early releases archive</a>.</p>"""
            else:
                content = f"""<p>Python {version_name} is part of the Python 1.x series, the first major version of Python.</p>

<p>For historical documentation, see the <a href="{release_notes_url}" class="python-link" target="_blank" rel="noopener">Python {minor_version} release notes</a>.</p>"""

        else:
            content = f"""<p>Python {version_name} release.</p>

<p>See the <a href="{release_notes_url}" class="python-link" target="_blank" rel="noopener">release notes</a> for details.</p>"""

        return content

    for name, release_date, status, eol_date, is_latest, pre_release, version in release_data[:count]:
        notes_url = get_release_notes_url(name, version)
        release = Release(
            name=name,
            slug=f"python-{name.replace('.', '')}",
            version=version,
            status=status,
            is_latest=is_latest,
            is_published=True,
            pre_release=pre_release,
            show_on_download_page=True,
            release_date=release_date,
            eol_date=eol_date,
            release_notes_url=notes_url,
            content=get_release_content(name, version, status, notes_url),
            creator_id=users[0].id,
        )
        session.add(release)
        await session.flush()

        for j, os_obj in enumerate(os_list):
            release_file = ReleaseFile(
                name=f"Python-{name}-{os_obj.slug}",
                slug=f"python-{name}-{os_obj.slug}".lower().replace(".", "-"),
                release_id=release.id,
                os_id=os_obj.id,
                description=f"Python {name} for {os_obj.name}",
                is_source=os_obj.slug == "source",
                url=f"https://www.python.org/ftp/python/{name}/Python-{name}.tar.xz",
                gpg_signature_file=f"https://www.python.org/ftp/python/{name}/Python-{name}.tar.xz.asc",
                md5_sum="abcd1234efgh5678ijkl9012mnop3456",
                filesize=25000000 + (j * 1000000),
                download_button=j == 0,
                creator_id=users[0].id,
            )
            session.add(release_file)

        releases.append(release)

    await session.flush()
    return releases


async def seed_sponsors(session: AsyncSession, users: list[User], count: int = 5) -> list[Sponsor]:
    """Seed sponsors."""
    sponsors = []

    sponsor_data = [
        "Python Software Foundation",
        "JetBrains",
        "Microsoft",
        "Google",
        "Amazon Web Services",
    ]

    for _i, name in enumerate(sponsor_data[:count]):
        sponsor = Sponsor(
            name=name,
            slug=name.lower().replace(" ", "-"),
            description=f"{name} is a proud sponsor of Python.org",
            landing_page_url=f"https://{name.lower().replace(' ', '')}.com",
            twitter_handle=f"@{name.lower().replace(' ', '')}",
            web_logo=f"/media/sponsors/{name.lower().replace(' ', '-')}.png",
            primary_phone="+1-555-0100",
            city="San Francisco",
            state="CA",
            postal_code="94102",
            country="USA",
            creator_id=users[0].id,
        )
        session.add(sponsor)
        sponsors.append(sponsor)

    await session.flush()
    return sponsors


async def seed_sponsorship_levels(session: AsyncSession) -> list[SponsorshipLevel]:
    """Seed sponsorship levels."""
    levels = []

    level_data = [
        ("Visionary", "visionary", 0, 150000, 200),
        ("Sustainability", "sustainability", 1, 100000, 175),
        ("Maintaining", "maintaining", 2, 50000, 150),
        ("Contributing", "contributing", 3, 25000, 125),
        ("Supporting", "supporting", 4, 10000, 100),
        ("Partner", "partner", 5, 5000, 75),
    ]

    for name, slug, order, amount, logo_dim in level_data:
        level = SponsorshipLevel(
            name=name,
            slug=slug,
            order=order,
            sponsorship_amount=amount,
            logo_dimension=logo_dim,
        )
        session.add(level)
        levels.append(level)

    await session.flush()
    return levels


async def seed_sponsorships(
    session: AsyncSession,
    users: list[User],
    sponsors: list[Sponsor],
    levels: list[SponsorshipLevel],
) -> list[Sponsorship]:
    """Seed sponsorships."""
    sponsorships = []

    for i, sponsor in enumerate(sponsors):
        today = datetime.datetime.now(tz=datetime.UTC).date()
        level = levels[i % len(levels)]
        sponsorship = Sponsorship(
            sponsor_id=sponsor.id,
            level_id=level.id,
            submitted_by_id=users[1].id if len(users) > 1 else users[0].id,
            status=SponsorshipStatus.FINALIZED if i < SPONSOR_THRESHOLD else SponsorshipStatus.APPROVED,
            locked=False,
            start_date=today - datetime.timedelta(days=365),
            end_date=today + datetime.timedelta(days=365),
            applied_on=today - datetime.timedelta(days=400),
            approved_on=today - datetime.timedelta(days=380),
            finalized_on=today - datetime.timedelta(days=370) if i < SPONSOR_THRESHOLD else None,
            year=today.year,
            sponsorship_fee=level.sponsorship_amount,
            for_modified_package=False,
            renewal=i > 0,
            creator_id=users[0].id,
        )
        session.add(sponsorship)
        sponsorships.append(sponsorship)

    await session.flush()
    return sponsorships


async def seed_blogs(session: AsyncSession) -> tuple[list[Feed], list[BlogEntry]]:
    """Seed blog feeds and entries."""
    feeds = []
    entries = []

    feed_data = [
        (
            "Python Insider",
            "https://pythoninsider.blogspot.com",
            "https://pythoninsider.blogspot.com/feeds/posts/default",
        ),
        ("Real Python", "https://realpython.com", "https://realpython.com/atom.xml"),
        ("Planet Python", "https://planetpython.org", "https://planetpython.org/rss20.xml"),
    ]

    for name, website, feed_url in feed_data:
        feed = Feed(
            name=name,
            website_url=website,
            feed_url=feed_url,
            is_active=True,
        )
        session.add(feed)
        feeds.append(feed)

    await session.flush()

    for i, feed in enumerate(feeds):
        for j in range(3):
            entry = BlogEntry(
                feed_id=feed.id,
                title=f"Sample Blog Post {j + 1} from {feed.name}",
                summary=f"This is a summary of blog post {j + 1}",
                content=f"# Blog Post {j + 1}\n\nThis is the full content of the blog post.",
                url=f"{feed.website_url}/post-{j + 1}",
                pub_date=datetime.datetime.now(tz=datetime.UTC) - datetime.timedelta(days=j * 7 + i),
                guid=f"{feed.feed_url}#post-{j + 1}",
            )
            session.add(entry)
            entries.append(entry)

    await session.flush()
    return feeds, entries


async def seed_events(session: AsyncSession, users: list[User]) -> list[Event]:
    """Seed calendars and events."""
    events = []

    calendar = Calendar(
        name="Python Events",
        slug="python-events",
        creator_id=users[0].id,
    )
    session.add(calendar)
    await session.flush()

    location = EventLocation(
        name="Online",
        slug="online",
        url="https://python.org/events",
    )
    session.add(location)
    await session.flush()

    category = EventCategory(
        name="Conference",
        slug="conference",
        calendar_id=calendar.id,
    )
    session.add(category)
    await session.flush()

    event_data = [
        ("PyCon US 2025", "The largest Python conference in the world"),
        ("EuroPython 2025", "Europe's largest Python conference"),
        ("PyData Global", "A virtual conference for the PyData community"),
    ]

    for i, (title, description) in enumerate(event_data):
        event = Event(
            name=title.lower().replace(" ", "-"),
            slug=title.lower().replace(" ", "-"),
            title=title,
            description=description,
            calendar_id=calendar.id,
            venue_id=location.id if i == 2 else None,
            featured=i == 0,
            creator_id=users[0].id,
        )
        session.add(event)
        await session.flush()

        occurrence = EventOccurrence(
            event_id=event.id,
            dt_start=datetime.datetime.now(tz=datetime.UTC) + datetime.timedelta(days=30 + i * 60),
            dt_end=datetime.datetime.now(tz=datetime.UTC) + datetime.timedelta(days=33 + i * 60),
            all_day=False,
        )
        session.add(occurrence)
        events.append(event)

    await session.flush()
    return events


async def seed_jobs(session: AsyncSession, users: list[User]) -> list[Job]:
    """Seed job categories, types, and listings."""
    jobs = []

    category = JobCategory(name="Software Engineering", slug="software-engineering")
    session.add(category)

    job_types = [
        JobType(name="Full-time", slug="full-time"),
        JobType(name="Part-time", slug="part-time"),
        JobType(name="Contract", slug="contract"),
    ]
    for jt in job_types:
        session.add(jt)

    await session.flush()

    job_data = [
        ("Senior Python Developer", "TechCorp", "San Francisco", "CA", "USA", JobStatus.APPROVED),
        ("Django Backend Engineer", "StartupXYZ", "New York", "NY", "USA", JobStatus.APPROVED),
        ("Python Data Engineer", "DataCo", "Remote", None, "USA", JobStatus.REVIEW),
    ]

    for title, company, city, region, country, status in job_data:
        job = Job(
            slug=title.lower().replace(" ", "-"),
            creator_id=users[0].id,
            company_name=company,
            job_title=title,
            city=city,
            region=region,
            country=country,
            description=f"We are looking for a {title} to join our team.",
            requirements="5+ years of Python experience",
            email="jobs@example.com",
            status=status,
            telecommuting=city == "Remote",
            category_id=category.id,
        )
        session.add(job)
        jobs.append(job)

    await session.flush()
    return jobs


async def seed_minutes(session: AsyncSession, users: list[User]) -> list[Minutes]:
    """Seed PSF meeting minutes."""
    minutes_list = []

    for i in range(3):
        date = datetime.datetime.now(tz=datetime.UTC).date() - datetime.timedelta(days=30 * i)
        minutes = Minutes(
            slug=f"psf-board-meeting-{date.isoformat()}",
            date=date,
            content=f"# PSF Board Meeting - {date.isoformat()}\n\n## Attendees\n\n- Board Member 1\n- Board Member 2\n\n## Agenda\n\n1. Call to order\n2. Approval of minutes\n3. New business",
            content_type=ContentType.MARKDOWN,
            is_published=True,
            creator_id=users[0].id,
        )
        session.add(minutes)
        minutes_list.append(minutes)

    await session.flush()
    return minutes_list


async def seed_elections(session: AsyncSession, users: list[User]) -> list[Election]:
    """Seed elections and nominations."""
    elections = []

    today = datetime.datetime.now(tz=datetime.UTC).date()

    election = Election(
        slug="psf-board-2025",
        name="PSF Board Election 2025",
        description="Annual election for PSF Board of Directors",
        nominations_open=today - datetime.timedelta(days=30),
        nominations_close=today - datetime.timedelta(days=15),
        voting_open=today - datetime.timedelta(days=10),
        voting_close=today + datetime.timedelta(days=5),
    )
    session.add(election)
    await session.flush()

    for i, user in enumerate(users[:3]):
        nominee = Nominee(
            election_id=election.id,
            user_id=user.id,
            accepted=i < 2,
        )
        session.add(nominee)
        await session.flush()

        if i > 0:
            nomination = Nomination(
                nominee_id=nominee.id,
                nominator_id=users[0].id,
                endorsement=f"I nominate {user.full_name} for their excellent contributions.",
            )
            session.add(nomination)

    elections.append(election)
    await session.flush()
    return elections


async def seed_success_stories(session: AsyncSession, users: list[User]) -> list[Story]:
    """Seed success stories."""
    stories = []

    category = StoryCategory(name="Web Development", slug="web-development")
    session.add(category)
    await session.flush()

    story_data = [
        ("Instagram", "How Instagram scaled to millions using Python and Django"),
        ("Dropbox", "Dropbox's journey with Python from startup to enterprise"),
        ("NASA", "How NASA uses Python for space exploration"),
    ]

    for i, (company, title) in enumerate(story_data):
        story = Story(
            slug=company.lower(),
            name=title,
            company_name=company,
            company_url=f"https://{company.lower()}.com",
            category_id=category.id,
            content=f"# {title}\n\n{company} has been using Python extensively...",
            content_type=ContentType.MARKDOWN,
            is_published=True,
            featured=i == 0,
            creator_id=users[0].id,
        )
        session.add(story)
        stories.append(story)

    await session.flush()
    return stories


async def seed_work_groups(session: AsyncSession, users: list[User]) -> list[WorkGroup]:
    """Seed work groups."""
    groups = []

    group_data = [
        ("Packaging", "Improve Python packaging ecosystem", "https://wiki.python.org/psf/PackagingWG"),
        ("Diversity & Inclusion", "Foster diversity in Python community", "https://wiki.python.org/psf/DiversityWG"),
        ("Infrastructure", "Maintain Python.org infrastructure", "https://wiki.python.org/psf/InfrastructureWG"),
    ]

    for name, purpose, url in group_data:
        group = WorkGroup(
            slug=name.lower().replace(" & ", "-").replace(" ", "-"),
            name=name,
            purpose=purpose,
            active=True,
            url=url,
            creator_id=users[0].id,
        )
        session.add(group)
        groups.append(group)

    await session.flush()
    return groups


async def seed_code_samples(session: AsyncSession, users: list[User]) -> list[CodeSample]:
    """Seed code samples."""
    samples = []

    sample_data = [
        ("hello-world", "print('Hello, World!')", "The classic Hello World program"),
        (
            "fibonacci",
            "def fib(n):\n    a, b = 0, 1\n    for _ in range(n):\n        a, b = b, a + b\n    return a",
            "Calculate Fibonacci numbers",
        ),
        ("list-comprehension", "squares = [x**2 for x in range(10)]", "Example of list comprehension"),
    ]

    for slug, code, description in sample_data:
        sample = CodeSample(
            slug=slug,
            code=code,
            description=description,
            is_published=True,
            creator_id=users[0].id,
        )
        session.add(sample)
        samples.append(sample)

    await session.flush()
    return samples


async def seed_community(session: AsyncSession, users: list[User]) -> list[Post]:
    """Seed community posts."""
    posts = []

    post = Post(
        slug="welcome-to-python-community",
        title="Welcome to the Python Community!",
        content="# Welcome\n\nThe Python community is one of the most welcoming in tech.",
        content_type=ContentType.MARKDOWN,
        creator_id=users[0].id,
        is_published=True,
    )
    session.add(post)
    await session.flush()

    photo = Photo(
        post_id=post.id,
        image="/media/community/pycon-2024.jpg",
        caption="PyCon 2024 group photo",
        creator_id=users[0].id,
    )
    session.add(photo)

    video = Video(
        post_id=post.id,
        url="https://youtube.com/watch?v=example",
        title="Introduction to Python",
        creator_id=users[0].id,
    )
    session.add(video)

    link = Link(
        post_id=post.id,
        url="https://docs.python.org",
        title="Python Documentation",
        creator_id=users[0].id,
    )
    session.add(link)

    posts.append(post)
    await session.flush()
    return posts


async def seed_banners(session: AsyncSession) -> list[Banner]:
    """Seed site banners."""
    banners = []

    today = datetime.datetime.now(tz=datetime.UTC).date()

    banner = Banner(
        name="PyCon Announcement",
        title="PyCon US 2025",
        message="Registration is now open for PyCon US 2025!",
        link="https://us.pycon.org/2025",
        is_active=True,
        start_date=today - datetime.timedelta(days=30),
        end_date=today + datetime.timedelta(days=60),
    )
    session.add(banner)
    banners.append(banner)

    await session.flush()
    return banners


async def seed_database() -> None:
    """Main seeding function."""
    async with async_session_factory() as session:
        result = await session.execute(select(User).limit(1))
        existing_users = result.scalars().all()

        if existing_users:
            return

        users = await seed_users(session, count=10)
        await seed_memberships(session, users)
        await seed_pages(session, users, count=15)

        os_list = await seed_operating_systems(session, users)
        await seed_releases(session, users, os_list, count=100)

        sponsors = await seed_sponsors(session, users, count=5)
        levels = await seed_sponsorship_levels(session)
        await seed_sponsorships(session, users, sponsors, levels)

        await seed_blogs(session)
        await seed_events(session, users)
        await seed_jobs(session, users)
        await seed_minutes(session, users)
        await seed_elections(session, users)
        await seed_success_stories(session, users)
        await seed_work_groups(session, users)
        await seed_code_samples(session, users)
        await seed_community(session, users)
        await seed_banners(session)

        await session.commit()


async def clear_database() -> None:
    """Clear all data from the database."""
    async with async_session_factory() as session:
        await session.execute(Banner.__table__.delete())

        await session.execute(Link.__table__.delete())
        await session.execute(Video.__table__.delete())
        await session.execute(Photo.__table__.delete())
        await session.execute(Post.__table__.delete())

        await session.execute(CodeSample.__table__.delete())
        await session.execute(WorkGroup.__table__.delete())
        await session.execute(Story.__table__.delete())
        await session.execute(StoryCategory.__table__.delete())

        await session.execute(Nomination.__table__.delete())
        await session.execute(Nominee.__table__.delete())
        await session.execute(Election.__table__.delete())

        await session.execute(Minutes.__table__.delete())

        await session.execute(JobReviewComment.__table__.delete())
        await session.execute(Job.__table__.delete())
        await session.execute(JobType.__table__.delete())
        await session.execute(JobCategory.__table__.delete())

        await session.execute(EventOccurrence.__table__.delete())
        await session.execute(Event.__table__.delete())
        await session.execute(EventCategory.__table__.delete())
        await session.execute(EventLocation.__table__.delete())
        await session.execute(Calendar.__table__.delete())

        await session.execute(BlogEntry.__table__.delete())
        await session.execute(FeedAggregate.__table__.delete())
        await session.execute(Feed.__table__.delete())
        await session.execute(RelatedBlog.__table__.delete())

        await session.execute(ReleaseFile.__table__.delete())
        await session.execute(Release.__table__.delete())
        await session.execute(OS.__table__.delete())

        await session.execute(Page.__table__.delete())

        await session.execute(Sponsorship.__table__.delete())
        await session.execute(SponsorshipLevel.__table__.delete())
        await session.execute(Sponsor.__table__.delete())

        await session.execute(Membership.__table__.delete())
        await session.execute(User.__table__.delete())

        await session.commit()


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "clear":
        asyncio.run(clear_database())
    else:
        asyncio.run(seed_database())
