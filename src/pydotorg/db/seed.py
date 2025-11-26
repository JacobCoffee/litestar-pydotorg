"""Database seeding script for development and testing."""

from __future__ import annotations

import asyncio
import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from passlib.hash import bcrypt
from polyfactory.factories.sqlalchemy_factory import SQLAlchemyFactory
from sqlalchemy import select

from pydotorg.core.database.session import async_session_factory
from pydotorg.domains.downloads.models import OS, Release, ReleaseFile
from pydotorg.domains.pages.models import Page
from pydotorg.domains.sponsors.models import Sponsor, Sponsorship, SponsorshipStatus
from pydotorg.domains.users.models import EmailPrivacy, Membership, MembershipType, SearchVisibility, User

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession


class UserFactory(SQLAlchemyFactory[User]):
    __model__ = User
    __set_relationships__ = False

    @classmethod
    def password_hash(cls) -> str:
        return bcrypt.hash("password123")

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


class OSFactory(SQLAlchemyFactory[OS]):
    __model__ = OS
    __set_relationships__ = False


class ReleaseFactory(SQLAlchemyFactory[Release]):
    __model__ = Release
    __set_relationships__ = False

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


class SponsorshipFactory(SQLAlchemyFactory[Sponsorship]):
    __model__ = Sponsorship
    __set_relationships__ = False

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
        password_hash=bcrypt.hash("admin123"),
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
        password_hash=bcrypt.hash("test123"),
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
            else MembershipType.CONTRIBUTING if i == 1 else MembershipType.SUPPORTING if i == 2 else MembershipType.BASIC
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
            votes=i < 3,
            last_vote_affirmation=datetime.date.today() if i < 3 else None,
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
    count: int = 5,
) -> list[Release]:
    """Seed Python releases."""
    releases = []

    release_data = [
        ("3.13.0", True, False),
        ("3.12.7", False, False),
        ("3.11.10", False, False),
        ("3.10.15", False, False),
        ("3.14.0a1", False, True),
    ]

    for i, (name, is_latest, pre_release) in enumerate(release_data[:count]):
        release = Release(
            name=name,
            slug=name.lower().replace(".", "-"),
            is_latest=is_latest,
            is_published=True,
            pre_release=pre_release,
            show_on_download_page=not pre_release,
            release_date=datetime.date.today() - datetime.timedelta(days=i * 30),
            release_notes_url=f"https://docs.python.org/3/whatsnew/{name.split('.')[1]}.html",
            content=f"# Python {name}\n\nThis is the release notes for Python {name}.",
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

    for i, name in enumerate(sponsor_data[:count]):
        sponsor = Sponsor(
            name=name,
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


async def seed_sponsorships(
    session: AsyncSession,
    users: list[User],
    sponsors: list[Sponsor],
) -> list[Sponsorship]:
    """Seed sponsorships."""
    sponsorships = []

    for i, sponsor in enumerate(sponsors):
        sponsorship = Sponsorship(
            sponsor_id=sponsor.id,
            submitted_by_id=users[1].id if len(users) > 1 else users[0].id,
            status=SponsorshipStatus.FINALIZED if i < 3 else SponsorshipStatus.APPROVED,
            locked=False,
            start_date=datetime.date.today() - datetime.timedelta(days=365),
            end_date=datetime.date.today() + datetime.timedelta(days=365),
            applied_on=datetime.date.today() - datetime.timedelta(days=400),
            approved_on=datetime.date.today() - datetime.timedelta(days=380),
            finalized_on=datetime.date.today() - datetime.timedelta(days=370) if i < 3 else None,
            year=datetime.date.today().year,
            sponsorship_fee=Decimal("10000.00") if i < 2 else Decimal("5000.00"),
            for_modified_package=False,
            renewal=i > 0,
            creator_id=users[0].id,
        )
        session.add(sponsorship)
        sponsorships.append(sponsorship)

    await session.flush()
    return sponsorships


async def seed_database() -> None:
    """Main seeding function."""
    async with async_session_factory() as session:
        result = await session.execute(select(User).limit(1))
        existing_users = result.scalars().all()

        if existing_users:
            print("Database already seeded. Skipping...")
            return

        print("Seeding database...")

        users = await seed_users(session, count=10)
        print(f"Created {len(users)} users")

        memberships = await seed_memberships(session, users)
        print(f"Created {len(memberships)} memberships")

        pages = await seed_pages(session, users, count=15)
        print(f"Created {len(pages)} pages")

        os_list = await seed_operating_systems(session, users)
        print(f"Created {len(os_list)} operating systems")

        releases = await seed_releases(session, users, os_list, count=5)
        print(f"Created {len(releases)} releases")

        sponsors = await seed_sponsors(session, users, count=5)
        print(f"Created {len(sponsors)} sponsors")

        sponsorships = await seed_sponsorships(session, users, sponsors)
        print(f"Created {len(sponsorships)} sponsorships")

        await session.commit()
        print("Database seeded successfully!")


async def clear_database() -> None:
    """Clear all data from the database."""
    async with async_session_factory() as session:
        print("Clearing database...")

        await session.execute(ReleaseFile.__table__.delete())
        await session.execute(Release.__table__.delete())
        await session.execute(OS.__table__.delete())

        await session.execute(Page.__table__.delete())

        await session.execute(Sponsorship.__table__.delete())
        await session.execute(Sponsor.__table__.delete())

        await session.execute(Membership.__table__.delete())
        await session.execute(User.__table__.delete())

        await session.commit()
        print("Database cleared!")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "clear":
        asyncio.run(clear_database())
    else:
        asyncio.run(seed_database())
