"""Nominations domain URL constants."""

from typing import Final

ELECTIONS: Final[str] = "/api/v1/elections"
ELECTIONS_ACTIVE: Final[str] = "/api/v1/elections/active"
ELECTION_BY_ID: Final[str] = "/api/v1/elections/{election_id:uuid}"

NOMINEES: Final[str] = "/api/v1/nominees"
NOMINEE_BY_ID: Final[str] = "/api/v1/nominees/{nominee_id:uuid}"
NOMINEES_ACCEPTED: Final[str] = "/api/v1/nominees/elections/{election_id:uuid}/accepted"
NOMINEE_ACCEPT: Final[str] = "/api/v1/nominees/{nominee_id:uuid}/accept"
NOMINEE_DECLINE: Final[str] = "/api/v1/nominees/{nominee_id:uuid}/decline"

NOMINATIONS: Final[str] = "/api/v1/nominations"
NOMINATION_BY_ID: Final[str] = "/api/v1/nominations/{nomination_id:uuid}"

NOMINATIONS_HTML: Final[str] = "/nominations"
ELECTION_HTML: Final[str] = "/nominations/{slug:str}"
