# Architecture Decisions

## 1. Refresh tokens live in Redis, not Postgres
**Decision:** One Redis hash per login session (`refresh:{user_id}:{sid}`), plus a set
indexing each user's sessions. TTL = token lifetime.
**Why:** Any server instance can validate sessions, so the API scales horizontally.
Expiry is handled by Redis itself. Multi-device login and "logout everywhere" are cheap.
**Trade-off:** Sessions are lost if Redis loses data (users log in again). Acceptable,
since nothing permanent lives there.

## 2. Refresh rotation with reuse detection
**Decision:** Every refresh replaces the stored token hash atomically (Lua script).
Presenting an already-rotated token revokes all of that user's sessions.
**Why:** A stolen token that is replayed later is detected, not silently accepted.
**Trade-off:** The legitimate user is also logged out when reuse is detected.

## 3. Session id (`sid`) inside the access token
**Why:** `get_current_user` checks the session still exists, so logout and
revocation take effect immediately instead of waiting 15 minutes for expiry.
**Trade-off:** One Redis lookup per authenticated request.

## 4. bcrypt runs in a thread
**Why:** bcrypt is blocking; calling it directly inside `async def` would freeze every other request.