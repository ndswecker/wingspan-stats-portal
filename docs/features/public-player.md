# Player Privacy & Public Visibility

**Feature specification:** v0.2  
**Updated:** November 1, 2026  
**Status:** Agreed functional scope; implementation pending

## Purpose

Allow players to make their confirmed Wingspan results and statistics visible to other authenticated users without changing who may create or edit their games. Preserve privacy by default, existing friendships, and score confirmation. Show a small public leaderboard on the Home page.

This document defines **what the feature must do**, not the complete implementation. Details can be determined while developing and testing each page.

## Core business rules

1. **Private by default.** All existing players and new players start Private. A player with a linked account may switch between Public and Private at any time from their Account page.
2. **Read access for ordinary authenticated users.** A user may view eligible results and statistics for themselves, their current friends, and Public players. They may not view a Private non-friend's results or statistics.
3. **Public is not write permission.** Game creation and editing continue to use existing friendship-based authorization, regardless of visibility setting.
4. **Confirmed data only in results and statistics.** The pages opened to broader viewing must exclude games unless **every associated GameResult is confirmed**. This applies to the selected player's own results and friends' results on Player Overview, not just to public non-friends. A player's private pending-confirmation workflow remains available to them; authorized game participants and staff may inspect unconfirmed games as described below.
5. **Individual results versus whole games.** Making a player's results Public does not expose every participant in the underlying game. Full Game Detail has its own access rule.
6. **Private handles still work for invitations.** Anyone who knows an active private player's exact handle can send a friend request. Visibility changes do not change friendships or pending invitations.
7. **Staff and superusers have read access to all players and games.** This exception is for viewing, including inspection of pending results, not for bypassing editing or confirmation rules. Analytical calculations retain their confirmation requirements.
8. **Anonymous access is limited.** Unauthenticated visitors can see the same public Home leaderboard as logged-in users, but not the detailed player-results pages or Game Detail.

## Access summary

| Viewer | Player results and statistics | Full Game Detail | Create/edit results |
| --- | --- | --- | --- |
| Ordinary authenticated player | Self, friends, Public players; eligible confirmed data | Only games they participated in | Existing self/friends rules |
| Staff or superuser | All players; confirmed data for general statistics, with inspection access to pending records as appropriate | Any game | Existing permissions; no new write privilege |
| Anonymous visitor | Home public leaderboard only | No | No |

A *game participant* is a player with a `GameResult` for that game. Friendship with a participant does not grant Game Detail access.

## Page requirements

### Account

- Add a **Player Privacy** section showing the current Public/Private setting and a deliberate Save action.
- Explain that Public exposes the player's confirmed results/statistics to logged-in users and places their name and handle on the public Home leaderboard.
- Only the user who owns the linked player account can change that player's setting. Accounts without a linked player do not receive these controls.
- Keep account information and the owner's pending-confirmation list unchanged. Username and email do not become public.

### Friends

- **No changes planned.** Keep exact-handle invitations, incoming/outgoing request management, and friend removal.
- Private players can continue receiving requests when they share their handles directly.
- Do not add a public-player directory to this page.

### Player Overview

- Player selection includes **self + active friends + active Public players**; staff/superusers may select all players.
- Both general statistics and the game-history table use only fully confirmed games, for **all viewers**.
- Keep game-type filters, dates, This Month/All Time, and existing statistics.
- A result can be visible without granting access to its Game Detail page. Do not offer a working detail link to a viewer who is neither a participant nor staff/superuser; enforce access on the destination regardless.

### Player Score Trends

- Both player dropdowns use the same viewable-player population; allow comparisons between any two selectable players, even if neither is a friend.
- Preserve existing charts, comparisons, filters, and confirmed-only analysis.

### Competitive History

- Both player dropdowns use the same viewable-player population; preserve existing history/comparison behavior and confirmed-only results.
- Game Detail links follow the separate participant/staff access rule.

### Feathered Foe

- **Out of scope; leave unchanged.** This is a friends-based rivalry feature, not a public-player comparison feature. Public non-friends are not added to its selectors.

### Home

- Keep Home accessible to anonymous and authenticated visitors, with the **same leaderboard** for both.
- Leaderboard contains **only active Public players** and shows **player name, handle, games played, average score**.
- Use only fully confirmed games for leaderboard calculations. Sort by **average score descending**; no game wins or night wins.
- Private players and their handles are absent. Leave the broader Home redesign (purpose, introduction, site navigation, new metrics) to a separate project.
- The existing anonymous site-wide total-games count can remain for now; its definition may be revisited with the Home redesign.

### Game Detail

- An authenticated user may open a complete game only if **they participated**, or they are **staff/superuser**.
- All other viewers, including anonymous users, friends who did not play, and public-result viewers who did not play, are denied access—even with a direct URL.
- Participants and staff/superusers may inspect an unconfirmed game as needed. This does not make its results eligible for general public statistics or analysis.
- The page remains a complete-game display; no partial redaction is required under this access model.

### Game Creation, Editing, and Confirmation

- **No functional change.** Preserve friendship-based entry/edit permissions and existing score-confirmation rules.
- Public status must never expand the allowed result-player list or grant score-confirmation authority.

## Architecture guidance (not a detailed design)

- **Model:** Store visibility on `Player` (proposed `is_public`, default `False`), not the Django authentication user. Apply a migration preserving all existing players as Private.
- **Permissions/service layer:** Maintain separate concepts for *who can be selected for game entry* and *whose results can be read*. The current `get_allowed_result_players()` remains a write-path concept; a dedicated viewable-player selector can serve read-oriented forms. Centralize staff/superuser and Game Detail read checks.
- **Forms/views:** Restrict player-selection querysets and validate server-side submissions. Do not trust a crafted URL, form value, or hidden link to authorize access.
- **Query and analysis services:** Apply fully confirmed-game filtering **before** producing both displayed results and their aggregates. Avoid spreading ad hoc visibility filtering into templates or chart calculations.
- **Templates:** Present privacy controls on Account, public-only leaderboard fields on Home, and Game Detail links only where access is available.

Relevant existing code areas include `models.py`, `forms.py`, the Account and Players views, `home.py`, `games.py`, `services/dashboard.py`, `services/game_result_selection.py`, `services/game_entry.py`, and the corresponding HTML templates. Exact function signatures and file organization can be decided during implementation.

## Implementation checkpoints

1. Add private-by-default player visibility and the Account setting.
2. Introduce shared read-access rules, including staff/superuser exceptions, without changing friendship-based write access.
3. Update Player Overview, Trends, and Competitive History selectors and fully confirmed result behavior.
4. Protect Game Detail by participation or staff/superuser access; adjust links from other pages.
5. Restrict and rank the anonymous Home leaderboard using confirmed results; display public handles.
6. Test transitions Private → Public → Private, relationships and non-relationships, direct URL access, staff read-only access, pending confirmations, and anonymous browsing.

## Deferred and outside this release

- Dedicated public-player directory and discovery UX.
- Broader Home page redesign and new dashboard metrics.
- Changes to Feathered Foe or game creation/editing workflows.
- Detailed implementation choices, query optimization, and cosmetic presentation beyond the requirements above.

**Release principle:** Implement read expansion deliberately and verify that every public output remains within its intended visibility and confirmation boundary.
