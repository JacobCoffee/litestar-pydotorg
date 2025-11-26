"""CLI entry point."""

from __future__ import annotations

import sys

import uvicorn


def main() -> int:
    uvicorn.run(
        "pydotorg.main:app",
        host="0.0.0.0",  # noqa: S104
        port=8000,
        reload=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
