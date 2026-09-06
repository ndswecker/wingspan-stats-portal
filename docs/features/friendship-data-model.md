# Friendship Data Model Specification and Roadmap

## 1. Purpose

This document defines the target database model and migration roadmap
for Player handles, friend requests, and friendships in the Wingspan
Portal.

It is the authoritative persistence design for the future Friends
feature. User-facing workflows, views, forms, and game-entry behavior
belong in the Friends feature specification and should reference this
document rather than duplicate the data-model rules.

## 2. Design Principles

-   `Player.name` is the Player's normal display name and is not unique.
-   `Player.handle` is the Player's required, unique public identifier
    for friend discovery and disambiguation.
-   Handles locate Players; Player primary keys establish relationships.
-   Changing a handle must not change existing friendships, game
    results, or other Player relationships.
-   Friend requests are directional.
-   Accepted friendships are mutual.
-   Friend-request and friendship history is preserved rather than
    deleted during normal lifecycle operations.
-   Database constraints should enforce relationship invariants wherever
    practical.

## 3. Target Player Model

The existing Player model remains conceptually intact with the addition
of `handle` and removal of the uniqueness requirement from `name`.

``` text
Player
------
id
user
name
handle
is_active
```

### 3.1 `name`

`name` is the Player's display name.

Requirements:

-   Required.
-   Not unique.
-   Multiple Players may have the same name.
-   Existing application behavior may continue to present `name` as the
    primary human-facing identity.

Example:

``` text
name="Nick", handle="nick_w"
name="Nick", handle="nick_pdx"
```

### 3.2 `handle`

`handle` is the Player's public discovery identifier.

Requirements:

-   Required in the target state.
-   Unique across all Players.
-   Used for friend discovery.
-   Used as secondary identification where duplicate Player names would
    otherwise be ambiguous.
-   May be changed by the Player.
-   Changing a handle does not change the Player's database identity or
    any existing relationships.
-   Friendships, friend requests, game results, and other domain
    relationships must reference the Player primary key rather than the
    handle.

Conceptually:

``` text
@amani
   |
   | lookup
   v
Player.id
   |
   +-- FriendRequest
   +-- Friendship
   +-- GameResult
```

Handle validation and normalization rules must be established before the
handle field reaches its final required state.

## 4. FriendRequest Model

A `FriendRequest` records a directional request from one Player to
another.

``` text
FriendRequest
-------------
id
requestor
requestee
status
requested_at
resolved_at
```

Django ForeignKey fields such as `requestor` and `requestee` will
naturally produce database columns such as `requestor_id` and
`requestee_id`.

### 4.1 `requestor`

The Player who initiated the friend request.

### 4.2 `requestee`

The Player who received the friend request.

### 4.3 `status`

The current or final state of the friend request.

Initial lifecycle values:

``` text
PENDING
ACCEPTED
DECLINED
CANCELLED
```

A request begins as `PENDING`.

Acceptance changes the request to `ACCEPTED` and establishes a
Friendship.

Declining changes the request to `DECLINED`.

Cancellation by the requestor changes the request to `CANCELLED`.

Resolved requests remain in the database as historical records.

### 4.4 `requested_at`

Timestamp at which the friend request was made.

### 4.5 `resolved_at`

Timestamp at which the request left the `PENDING` state.

`resolved_at` is null while the request is pending.

## 5. Friendship Model

A `Friendship` records a period during which two Players have an
accepted, mutual friendship.

``` text
Friendship
----------
id
player_a
player_b
established_at
ended_at
ended_by_player
```

Django ForeignKey fields will naturally produce database columns such as
`player_a_id`, `player_b_id`, and `ended_by_player_id`.

### 5.1 `player_a` and `player_b`

The two Players participating in the friendship.

The relationship is symmetric. Neither column represents ownership,
initiation, priority, or permissions.

The pair is stored in canonical order:

``` text
player_a.id < player_b.id
```

For Players with IDs 4 and 12, the only valid representation is:

``` text
player_a = 4
player_b = 12
```

The reverse representation is not valid.

This canonical ordering gives every unordered Player pair one
deterministic database representation. Pair-based friendship checks can
therefore canonicalize the supplied Player IDs and perform a single
exact lookup.

### 5.2 `established_at`

Timestamp at which the friendship became active.

### 5.3 `ended_at`

Timestamp at which the friendship ceased to be active.

An active friendship has:

``` text
ended_at = NULL
```

Unfriending ends the current Friendship rather than deleting it.

### 5.4 `ended_by_player`

The Player who ended the friendship.

For an active friendship this value is null.

## 6. Historical Model

Friend requests and friendships are retained as historical records.

### 6.1 Request history

Accepting, declining, or cancelling a FriendRequest updates its
lifecycle state rather than deleting the row.

Example:

``` text
Nick -> Amani
status: ACCEPTED
requested_at: Sep 6
resolved_at: Sep 7
```

### 6.2 Friendship history

Unfriending does not delete the Friendship row. It populates `ended_at`
and `ended_by_player`.

Example:

``` text
Amani <-> Nick
established_at: Sep 7
ended_at: Oct 10
ended_by_player: Amani
```

### 6.3 Re-friending

A later friend request creates a new FriendRequest record.

If accepted, it creates a new Friendship record rather than reopening
the historical Friendship.

Therefore the same Player pair may have multiple historical request and
friendship records while having at most one active friendship.

This history supports future auditing of authorization decisions,
including determining whether two Players were friends when a game
result was submitted.

## 7. Data Integrity Requirements

The final schema and service layer must enforce the following
invariants.

### Player

-   Every Player has a `name`.
-   `name` is not unique.
-   Every Player has a `handle`.
-   Every handle is unique.
-   Handles satisfy the established validation and normalization rules.

### FriendRequest

-   A Player cannot request friendship with themselves.
-   `requestor` and `requestee` are distinct Players.
-   A pending request grants no friendship permissions.
-   `resolved_at` is null while `status` is `PENDING`.
-   A resolved request records its resolution timestamp.
-   The system must prevent conflicting or duplicate simultaneous
    pending requests between the same Player pair.

Historical requests between the same Players are permitted.

### Friendship

-   A Player cannot be friends with themselves.
-   `player_a` and `player_b` are distinct Players.
-   `player_a.id < player_b.id`.
-   There may be at most one active Friendship for a Player pair.
-   Multiple ended historical Friendships for the same pair are
    permitted.
-   An active Friendship has `ended_at = NULL`.
-   Ending a friendship records when it ended and which Player ended it.

The final PostgreSQL/Django implementation should use database
constraints for these invariants wherever practical, including check
constraints and conditional uniqueness constraints.

## 8. Relationship Overview

``` text
Django User
     |
     | one-to-one
     v
   Player
     |
     |-- name
     |-- handle
     |
     +-----------------------+
     |                       |
     v                       v
FriendRequest            Friendship
-------------            ----------
requestor                player_a
requestee                player_b
status                   established_at
requested_at             ended_at
resolved_at              ended_by_player
```

`FriendRequest` is directional.

`Friendship` is symmetric and uses canonical Player ordering.

## 9. Migration Roadmap

The transition from the current Player schema to the target schema must
be incremental so that existing production data remains valid throughout
deployment.

### Phase 1 --- Introduce Player Handle

1.  Add `Player.handle` as nullable/non-required.
2.  Create and apply the schema migration.
3.  Do not automatically generate handles.
4.  Manually assign a valid handle to every existing Player.
5.  Verify that all existing Players have handles and that the proposed
    values are unique.

This intermediate nullable state exists only to permit a controlled
production migration.

### Phase 2 --- Finalize Player Identity

After all existing Players have handles:

1.  Establish the final handle validation and normalization rules.
2.  Make `Player.handle` required.
3.  Enforce handle uniqueness.
4.  Remove the uniqueness requirement from `Player.name`.
5.  Update Player creation workflows so every new Player receives a
    valid handle.
6.  Audit application code for assumptions that `Player.name` uniquely
    identifies a Player.
7.  Update identity-sensitive lookups to use Player primary keys or
    handles as appropriate.

The migration should not permit duplicate Player names until application
code that depends on name uniqueness has been reviewed.

### Phase 3 --- Add Friendship Persistence

Create the `FriendRequest` and `Friendship` models.

Implement:

-   Foreign-key relationships.
-   FriendRequest lifecycle state.
-   Request and resolution timestamps.
-   Canonical Friendship ordering.
-   Friendship start/end history.
-   Self-relationship prevention.
-   Active-friendship uniqueness.
-   Pending-request integrity.
-   Appropriate indexes and database constraints.

### Phase 4 --- Friends Feature Integration

Once the persistence layer is established, the Friends feature
specification can implement:

-   Exact Player discovery by handle.
-   Sending friend requests.
-   Viewing incoming and outgoing pending requests.
-   Accepting, declining, and cancelling requests.
-   Viewing accepted friends.
-   Unfriending.
-   Player disambiguation using handles where necessary.
-   Game-entry authorization based on active friendships.

Detailed UI, service, form, view, and authorization behavior belongs in
the Friends feature specification.

## 10. Migration Verification

Before each migration phase is considered complete, verify the relevant
database invariants directly.

Before making handles required:

``` text
No Player has a NULL/blank handle.
No duplicate handles exist.
All handles satisfy final validation rules.
```

Before allowing duplicate Player names:

``` text
No application path relies on Player.name as a unique lookup key.
Player-selection interfaces can disambiguate Players with identical names.
```

Before enabling friendship-based authorization:

``` text
FriendRequest constraints are active.
Friendship canonical ordering is enforced.
Only one active Friendship can exist per Player pair.
Service-layer authorization uses Player relationships rather than names or handles.
```

## 11. Explicit Non-Goals

This data-model design does not introduce:

-   Handle-change cooldowns.
-   Handle-reuse policies.
-   Handle-less Players in the target state.
-   Friendship storage based on handles or Player names.
-   A globally browseable Player directory.
-   UI implementation details.
-   Game-entry implementation details.

These concerns may be specified separately if future requirements
justify them.

## 12. Target-State Summary

The target persistence model is:

``` text
Player
------
id
user
name
handle
is_active


FriendRequest
-------------
id
requestor
requestee
status
requested_at
resolved_at


Friendship
----------
id
player_a
player_b
established_at
ended_at
ended_by_player
```

The central identity rule is:

> Handles locate Players. Player primary keys establish relationships.

The central friendship rule is:

> Friend requests are directional historical workflow records;
> friendships are symmetric historical relationship periods.

The central migration rule is:

> Introduce the new identity infrastructure incrementally, validate
> existing production data, and only then enforce the final constraints.
