"""CLI entry point."""

from __future__ import annotations

import sys

from granian import Granian


def main() -> int:
    server = Granian(
        "pydotorg.main:app",
        address="0.0.0.0",  # noqa: S104
        port=8000,
        interface="asgi",
        reload=True,
        reload_paths=["src"],
    )
    server.serve()
    return 0


if __name__ == "__main__":
    sys.exit(main())
