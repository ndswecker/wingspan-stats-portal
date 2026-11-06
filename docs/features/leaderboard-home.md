# Wingspan Portal — Home Leaderboards Specification

**Status:** Approved for Implementation  
**Scope:** Home page leaderboard redesign  
**Target Version:** TBD

---

## 1. Objective

Redesign the Home page to provide two distinct leaderboards:

1. **Community Top 10** — A public leaderboard featuring the highest-ranked Public players.
2. **Friends Leaderboard** — A personalized leaderboard featuring the authenticated player and their active friends.

Both leaderboards will support selectable time periods and ranking metrics.

The feature must respect player privacy settings and include only fully confirmed games.

## 2. Leaderboard Visibility

### 2.1 Community Top 10

- Visible to all visitors, including anonymous users.
- Includes only players where `is_public=True` and `is_active=True`.
- Displays the top 10 qualifying players.
- Identical for all visitors, regardless of authentication, friendships, or staff privileges.
- Private players must never appear, including when viewed by staff.

### 2.2 Friends Leaderboard

- Visible only to authenticated users with a linked Player.
- Includes the authenticated player's own Player and their active friends.
- Includes friends regardless of their Public/Private status.
- Excludes former friends and inactive players.
- Displays all eligible friends initially, without a top-10 restriction.
- Staff and superusers follow the same friendship-based selection rules for this leaderboard.
- Authenticated users without a linked Player do not receive a Friends leaderboard.

### 2.3 Privacy Requirements

- Public visibility does not grant additional game-editing permissions.
- Username and email must never appear on either leaderboard.
- A private player's performance may appear only in their own Friends leaderboard or the Friends leaderboard of an active friend.
- No private player information may leak into the Community leaderboard through rankings or aggregate calculations.

## 3. Leaderboard Controls

Two shared controls will appear above both leaderboards.

### 3.1 Time Period

| Option | Definition |
|---|---|
| Last 30 Days | Games played within the rolling 30-day period |
| Last 90 Days | Games played within the rolling 90-day period |
| All Time | All eligible historical games |

**Default:** Last 90 Days.

Filtering uses the game's `date_played` field.

The selected time period applies to both leaderboards.

### 3.2 Ranking Metric

| Option | Calculation | Ranking |
|---|---|---|
| Average Score | Arithmetic mean of eligible game scores | Highest average first |
| Games Played | Count of eligible games played | Highest count first |

**Default:** Average Score.

The selected ranking metric applies to both leaderboards.

Both metrics remain displayed regardless of which metric determines the ranking.

No weighted or composite ranking formula will be introduced.

## 4. Game Eligibility

Only fully confirmed games contribute to leaderboard statistics.

A game qualifies when:

- Every associated `GameResult` has `is_confirmed=True`.
- Its `date_played` falls within the selected period.
- It meets the existing validity requirements for recorded games.

Both Solo and Competitive games are included.

Each player receives credit for one eligible game played and their own score from that game.

A game containing any unconfirmed result must be excluded entirely from both leaderboards, even for participants whose own results are confirmed.

## 5. Leaderboard Columns

Both leaderboards display the following information:

| Column | Description |
|---|---|
| Rank | Player's position according to the selected metric |
| Player | Player name and `@handle` |
| Games Played | Number of eligible games during the period |
| Average Score | Average score across eligible games, displayed to one decimal place |

Existing Game Wins and Night Wins columns will be removed.

### 5.1 Ranking and Ties

- Players are ranked in descending order by the selected metric.
- Equal metric values receive the same rank.
- A deterministic secondary sort order ensures consistent display.
- Rankings are calculated independently for each leaderboard.
- Players with zero eligible games are omitted from ranked positions for the selected period.
- No minimum-games qualification threshold is imposed beyond having at least one eligible game.

Average-score ranking uses the underlying numeric average, not the rounded display value, when ordering and identifying ties.

## 6. Community Top 10 Behavior

- Calculate rankings among all qualifying active Public players.
- Display no more than 10 players.
- Apply the selected time period and ranking metric.
- Do not include private players to fill missing positions.
- If fewer than 10 players qualify, display only those players.
- If no players qualify, show an appropriate empty-state message.

The Community leaderboard must not depend on the currently authenticated user.

## 7. Friends Leaderboard Behavior

- Calculate rankings independently among the authenticated player and their active friends.
- Display all qualifying players rather than restricting the table to 10 rows.
- Include both Public and Private friends.
- Apply the same time period and ranking metric as Community.
- Highlight the authenticated player's own row using a clear visual indicator such as **You**.
- The authenticated player's rank is based on the Friends leaderboard, not the Community leaderboard.
- If the authenticated player has eligible games, their position remains visible even if they rank below all friends.
- If no players have eligible games, display an appropriate empty-state message.

### 7.1 Friendships

Only friendships where `ended_at IS NULL` qualify as active.

Public players who are not friends must not appear in the Friends leaderboard.

## 8. User Interface

The Home page will display the following sections in order:

1. Existing site-wide Total Games Played statistic.
2. Shared Time Period selector.
3. Shared Ranking Metric selector.
4. Community Top 10 leaderboard.
5. Friends Leaderboard, for authenticated users with a linked Player.

The two leaderboards will be vertically stacked.

Controls must clearly communicate which time period and ranking metric are currently selected.

The interface should remain responsive on desktop and mobile.

### 8.1 Initial Control Values

- Time Period: **Last 90 Days**
- Rank By: **Average Score**

### 8.2 Empty States

When no qualifying games or players exist for a leaderboard, display a helpful message rather than an empty table or misleading ranking.

## 9. Architecture

### `portal/services/dashboard.py`

Responsible for:

- Retrieving eligible leaderboard players.
- Selecting fully confirmed game results.
- Applying the selected date period.
- Aggregating games played and average scores.
- Ranking and sorting players.
- Limiting Community results to the top 10.

Community player selection must explicitly filter for active Public players.

Friends player selection must use the authenticated player's identity and active friendship relationships.

The existing `get_viewable_players()` service must **not** be used directly for either leaderboard because its broader access rules do not match these two audiences.

### `portal/views/home.py`

Responsible for:

- Reading and validating time-period and ranking-metric selections.
- Requesting both leaderboards from the service layer.
- Passing leaderboard results and selected control values to the template.
- Omitting Friends leaderboard data for anonymous users or users without a linked Player.

The Home page must remain publicly accessible.

### `portal/templates/portal/home.html`

Responsible for:

- Rendering the shared controls.
- Displaying the stacked leaderboards.
- Conditionally rendering Friends leaderboard.
- Highlighting the authenticated player.
- Displaying appropriate empty states.

Business logic and authorization decisions should remain outside the template.

## 10. Testing Requirements

The feature should be tested for:

- Anonymous visitors seeing only the Community leaderboard.
- Community showing Public, active players exclusively.
- Private players never appearing in Community.
- Authenticated players seeing themselves and active friends in Friends.
- Private friends appearing correctly in Friends.
- Former friends and inactive players being excluded.
- Staff and superusers not bypassing Community visibility rules.
- All three date periods producing correct results.
- Both ranking metrics producing correct ordering.
- Ties producing consistent ranks.
- Solo and Competitive games both counting.
- Partially confirmed games being excluded entirely.
- Players with no eligible games being excluded from rankings.
- The authenticated player's row being correctly highlighted.
- Empty states being displayed correctly.
- Invalid or manipulated filter parameters being handled safely.
- Existing site-wide Total Games Played statistic remaining functional.

## 11. Out of Scope

The following are explicitly deferred:

- Composite or weighted ranking formulas.
- Minimum-games qualification thresholds.
- Additional scoring metrics.
- Separate Solo and Competitive leaderboards.
- Pagination of the Friends leaderboard.
- Player-ranking history or rank-change indicators.
- Notifications and leaderboard achievements.
- Public player directory.
- Broad Home page redesign beyond the specified leaderboard components.
- Changes to game-editing, confirmation, or friendship permissions.

## 12. Implementation Sequence

1. Update dashboard services to support the eligible player populations, confirmed-game filtering, time periods, aggregation, and ranking.
2. Update the Home view to support the shared controls and personalized Friends leaderboard.
3. Update the Home template to render both leaderboards.
4. Test anonymous, authenticated, staff, and privacy scenarios.
5. Verify ranking calculations and edge cases.
6. Promote the completed feature to production.

---

## Acceptance Criteria

The feature is complete when an anonymous visitor can view the Top 10 Public players, an authenticated player can additionally view and compare rankings with their active friends, and both leaderboards correctly respond to the shared time-period and ranking-metric selections.

All displayed statistics must derive exclusively from fully confirmed games, include Solo and Competitive results, and respect the visibility policies defined above.