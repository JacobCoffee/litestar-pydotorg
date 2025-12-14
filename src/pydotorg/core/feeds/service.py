"""RSS 2.0 and Atom 1.0 feed generation services."""

from __future__ import annotations

import datetime
import html
from typing import TYPE_CHECKING
from xml.etree import ElementTree as ET

if TYPE_CHECKING:
    from collections.abc import Sequence

    from pydotorg.domains.events.models import Event


def _escape_cdata(text: str) -> str:
    """Escape text for XML CDATA sections."""
    if not text:
        return ""
    return html.escape(text, quote=False)


def _format_rfc822(dt: datetime.datetime) -> str:
    """Format datetime as RFC 822 for RSS."""
    return dt.strftime("%a, %d %b %Y %H:%M:%S %z") if dt.tzinfo else dt.strftime("%a, %d %b %Y %H:%M:%S +0000")


def _format_rfc3339(dt: datetime.datetime) -> str:
    """Format datetime as RFC 3339 for Atom."""
    if dt.tzinfo:
        return dt.isoformat()
    return dt.replace(tzinfo=datetime.UTC).isoformat()


class RSSFeedService:
    """Service for generating RSS 2.0 feeds for events."""

    VERSION = "2.0"

    def __init__(
        self,
        title: str = "Python Events",
        link: str = "https://www.python.org/events/",
        description: str = "Upcoming Python community events",
        language: str = "en-us",
    ) -> None:
        self.title = title
        self.link = link
        self.description = description
        self.language = language

    def _create_item(
        self,
        event: Event,
        base_url: str = "https://www.python.org",
    ) -> ET.Element:
        """Create an RSS item element for an event."""
        item = ET.Element("item")

        title = ET.SubElement(item, "title")
        title.text = event.title

        link = ET.SubElement(item, "link")
        link.text = f"{base_url}/events/{event.slug}/"

        guid = ET.SubElement(item, "guid")
        guid.set("isPermaLink", "true")
        guid.text = f"{base_url}/events/{event.slug}/"

        if event.description:
            description = ET.SubElement(item, "description")
            description.text = _escape_cdata(event.description[:500])

        if event.occurrences:
            first_occurrence = min(event.occurrences, key=lambda o: o.dt_start)
            pub_date = ET.SubElement(item, "pubDate")
            pub_date.text = _format_rfc822(first_occurrence.dt_start)

        if event.categories:
            for cat in event.categories:
                category = ET.SubElement(item, "category")
                category.text = cat.name

        if event.venue:
            source = ET.SubElement(item, "source")
            source.set("url", f"{base_url}/events/")
            location_parts = [event.venue.name]
            if event.venue.address:
                location_parts.append(event.venue.address)
            source.text = ", ".join(location_parts)

        return item

    def generate_feed(
        self,
        events: Sequence[Event],
        base_url: str = "https://www.python.org",
        feed_url: str | None = None,
    ) -> str:
        """Generate RSS 2.0 feed XML for events.

        Args:
            events: Sequence of Event objects to include in feed
            base_url: Base URL for event links
            feed_url: URL of the feed itself (for self-reference)

        Returns:
            RSS 2.0 XML string
        """
        rss = ET.Element("rss")
        rss.set("version", self.VERSION)
        rss.set("xmlns:atom", "http://www.w3.org/2005/Atom")

        channel = ET.SubElement(rss, "channel")

        title = ET.SubElement(channel, "title")
        title.text = self.title

        link = ET.SubElement(channel, "link")
        link.text = self.link

        description = ET.SubElement(channel, "description")
        description.text = self.description

        language = ET.SubElement(channel, "language")
        language.text = self.language

        last_build = ET.SubElement(channel, "lastBuildDate")
        last_build.text = _format_rfc822(datetime.datetime.now(datetime.UTC))

        generator = ET.SubElement(channel, "generator")
        generator.text = "Python.org Litestar"

        if feed_url:
            atom_link = ET.SubElement(channel, "{http://www.w3.org/2005/Atom}link")
            atom_link.set("href", feed_url)
            atom_link.set("rel", "self")
            atom_link.set("type", "application/rss+xml")

        for event in events:
            channel.append(self._create_item(event, base_url))

        ET.register_namespace("atom", "http://www.w3.org/2005/Atom")
        return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(rss, encoding="unicode")


class AtomFeedService:
    """Service for generating Atom 1.0 feeds for events."""

    NAMESPACE = "http://www.w3.org/2005/Atom"

    def __init__(
        self,
        title: str = "Python Events",
        subtitle: str = "Upcoming Python community events",
        author_name: str = "Python Software Foundation",
        author_email: str = "webmaster@python.org",
    ) -> None:
        self.title = title
        self.subtitle = subtitle
        self.author_name = author_name
        self.author_email = author_email

    def _create_entry(
        self,
        event: Event,
        base_url: str = "https://www.python.org",
    ) -> ET.Element:
        """Create an Atom entry element for an event."""
        entry = ET.Element("entry")

        title = ET.SubElement(entry, "title")
        title.text = event.title

        link = ET.SubElement(entry, "link")
        link.set("href", f"{base_url}/events/{event.slug}/")
        link.set("rel", "alternate")
        link.set("type", "text/html")

        entry_id = ET.SubElement(entry, "id")
        entry_id.text = f"tag:python.org,2025:events/{event.id}"

        if event.occurrences:
            first_occurrence = min(event.occurrences, key=lambda o: o.dt_start)
            updated = ET.SubElement(entry, "updated")
            updated.text = _format_rfc3339(first_occurrence.dt_start)

            published = ET.SubElement(entry, "published")
            published.text = _format_rfc3339(first_occurrence.dt_start)

        if event.description:
            summary = ET.SubElement(entry, "summary")
            summary.set("type", "html")
            summary.text = _escape_cdata(event.description[:500])

            content = ET.SubElement(entry, "content")
            content.set("type", "html")
            content.text = _escape_cdata(event.description)

        if event.categories:
            for cat in event.categories:
                category = ET.SubElement(entry, "category")
                category.set("term", cat.slug)
                category.set("label", cat.name)

        if event.venue:
            location_parts = [event.venue.name]
            if event.venue.address:
                location_parts.append(event.venue.address)
            georss = ET.SubElement(entry, "georss:featurename")
            georss.text = ", ".join(location_parts)

        return entry

    def generate_feed(
        self,
        events: Sequence[Event],
        feed_id: str = "tag:python.org,2025:events",
        base_url: str = "https://www.python.org",
        feed_url: str | None = None,
    ) -> str:
        """Generate Atom 1.0 feed XML for events.

        Args:
            events: Sequence of Event objects to include in feed
            feed_id: Unique identifier for the feed
            base_url: Base URL for event links
            feed_url: URL of the feed itself (for self-reference)

        Returns:
            Atom 1.0 XML string
        """
        feed = ET.Element("feed")
        feed.set("xmlns", self.NAMESPACE)
        feed.set("xmlns:georss", "http://www.georss.org/georss")

        title = ET.SubElement(feed, "title")
        title.text = self.title

        subtitle = ET.SubElement(feed, "subtitle")
        subtitle.text = self.subtitle

        feed_id_elem = ET.SubElement(feed, "id")
        feed_id_elem.text = feed_id

        updated = ET.SubElement(feed, "updated")
        updated.text = _format_rfc3339(datetime.datetime.now(datetime.UTC))

        link_alt = ET.SubElement(feed, "link")
        link_alt.set("href", f"{base_url}/events/")
        link_alt.set("rel", "alternate")
        link_alt.set("type", "text/html")

        if feed_url:
            link_self = ET.SubElement(feed, "link")
            link_self.set("href", feed_url)
            link_self.set("rel", "self")
            link_self.set("type", "application/atom+xml")

        author = ET.SubElement(feed, "author")
        author_name = ET.SubElement(author, "name")
        author_name.text = self.author_name
        author_email = ET.SubElement(author, "email")
        author_email.text = self.author_email

        generator = ET.SubElement(feed, "generator")
        generator.set("uri", "https://github.com/litestar-org/litestar")
        generator.text = "Python.org Litestar"

        for event in events:
            feed.append(self._create_entry(event, base_url))

        return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(feed, encoding="unicode")
