# Nominations Domain

Domain for managing PSF board elections and nominations.

## Overview

The nominations domain provides functionality for:
- Managing board elections with nomination and voting periods
- Tracking nominees and their acceptance status
- Recording nominations with endorsements
- Automatic status calculation based on dates

## Models

### Election
- Represents a PSF board election
- Tracks nomination and voting periods
- Auto-calculates status based on dates
- Supports slug-based URLs

### Nominee
- Links a user to an election
- Tracks acceptance status
- Contains all nominations for the nominee

### Nomination
- Records who nominated whom
- Optional endorsement text
- Supports multiple nominations per nominee

## API Endpoints

### Elections
- `GET /api/v1/elections` - List all elections
- `GET /api/v1/elections/active` - List active elections
- `GET /api/v1/elections/{id}` - Get election by ID
- `POST /api/v1/elections` - Create election (staff only)
- `PUT /api/v1/elections/{id}` - Update election (staff only)
- `DELETE /api/v1/elections/{id}` - Delete election (staff only)

### Nominees
- `GET /api/v1/nominees` - List all nominees
- `GET /api/v1/nominees/{id}` - Get nominee by ID
- `GET /api/v1/nominees/elections/{election_id}/accepted` - List accepted nominees
- `POST /api/v1/nominees` - Create nominee
- `PATCH /api/v1/nominees/{id}/accept` - Accept nomination
- `PATCH /api/v1/nominees/{id}/decline` - Decline nomination
- `DELETE /api/v1/nominees/{id}` - Delete nominee

### Nominations
- `GET /api/v1/nominations` - List all nominations
- `GET /api/v1/nominations/{id}` - Get nomination by ID
- `POST /api/v1/nominations` - Create nomination
- `DELETE /api/v1/nominations/{id}` - Delete nomination

## HTML Pages

- `GET /nominations/` - Elections listing
- `GET /nominations/{slug}` - Election detail with nominees

## Status Lifecycle

Elections have automatic status calculation:
1. **UPCOMING** - Before nominations open
2. **NOMINATIONS_OPEN** - During nomination period
3. **VOTING_OPEN** - During voting period
4. **CLOSED** - After voting ends

## Workflows

### Nomination Flow
1. User is nominated for an election (creates Nominee)
2. User accepts or declines nomination
3. If accepted, others can endorse via Nomination records
4. Accepted nominees appear in election listings

### Election Management
1. Staff creates election with dates
2. System auto-calculates status based on dates
3. Nominees are added during nomination period
4. Accepted nominees are shown to voters

## Dependencies

- Users domain (for User model)
- Advanced Alchemy (repository/service layer)
- SQLAlchemy (database models)

## Testing

Run tests for this domain:
```bash
uv run pytest tests/domains/test_nominations.py
```

## Future Enhancements

- Vote tracking
- Ballot management
- Election results calculation
- Email notifications for nominations
- Nomination limits per election
