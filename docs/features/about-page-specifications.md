
# About Page — Architecture and Content Specification

## Purpose

The About page is a publicly accessible, wiki-style introduction to Wingspan Stats Portal.

Its primary objectives are to:

- Demonstrate the application's value to prospective users.
- Explain major features through concise descriptions and screenshots.
- Provide lightweight guidance on how to use the application.
- Encourage active Wingspan players to join the beta.
- Remain accessible without authentication or access to private player data.

The target beta audience consists of active Wingspan players who typically play at least 15 games per month.

The page should balance product promotion with practical documentation. Content should emphasize the benefits of each feature before explaining how it works.

## Architecture

The About page uses Django templates, Bootstrap 5, and a small amount of page-specific CSS when necessary.

The implementation should remain lightweight and largely static.

### Template Organization

All About-related templates reside in:

`portal/templates/portal/about/`

The directory uses a flat structure:

```text
about/
├── about.html
├── _sidebar.html
├── _overview.html
├── _getting_started.html
├── _recording_games.html
├── _confirming_results.html
├── _game_history.html
├── _editing_games.html
├── _friends.html
├── _trends.html
└── _beta_invitation.html
```

Additional feature partials may be introduced as needed.

The leading underscore identifies templates intended to be included by the parent template.

### Parent Template

`about.html` is responsible for:

- Extending the shared `portal/base.html` template.
- Defining the overall Bootstrap layout.
- Including the navigation sidebar.
- Including feature partials in their intended reading order.

The parent template should not contain detailed feature documentation.

Feature sections are included using Django's standard include mechanism:

```django
{% include "portal/about/_recording_games.html" %}
```

### Feature Partials

Each feature partial is responsible for:

- One distinct user-facing concept or workflow.
- Its section heading and HTML anchor.
- Feature descriptions and lightweight instructions.
- Screenshots and supporting visual content.
- Internal layout and spacing.

Every feature partial must have one outer `<section>` element with a unique ID.

Example:

```html
<section id="recording-games" class="mb-5 pb-4 border-bottom">
    <h2>Recording Games</h2>

    <!-- Feature-specific content -->
</section>
```

Section IDs must match their corresponding sidebar links.

## Content Partitioning

Feature partials should represent individual user-facing concepts, not broad application categories.

A concept generally deserves its own partial when it has:

- A distinct user goal.
- A meaningful workflow.
- Unique functionality or permissions.
- Screenshots worth explaining independently.

Small interactions within a larger workflow should remain inside the relevant feature partial.

For example:

- Recording Games includes choosing game types, selecting players, and entering scores.
- Confirming Results is a separate partial because it represents a distinct player action.
- Editing and deleting games may share a partial because they are closely related maintenance operations.

Avoid creating excessively large partials or fragmenting simple workflows into unnecessary files.

## Navigation Structure

The About page uses a grouped sidebar for navigating a single continuous document.

The sidebar provides the organizational hierarchy, while individual feature partials provide the content.

Initial navigation groups:

### Introduction
- Overview
- Getting Started

### Managing Games
- Recording Games
- Confirming Results
- Game History
- Editing & Deleting Games

### Friends & Community
- Friends

### Statistics & Analysis
- Score Trends

### Beta
- Join the Beta

The navigation structure may evolve as features are documented.

Sidebar links use standard HTML anchors:

```html
<a class="nav-link" href="#recording-games">
    Recording Games
</a>
```

The corresponding partial contains:

```html
<section id="recording-games">
```

Navigation entries must correspond to existing sections before public release.

## Responsive Behavior

The page prioritizes mobile usability because most prospective users are expected to visit from mobile devices.

### Desktop

At Bootstrap's `lg` breakpoint (992px and wider):

- Display the navigation sidebar to the left of the content.
- Allocate approximately 25% of the layout to navigation.
- Allocate approximately 75% to the article.
- Use sticky positioning when implemented.
- Allow independent sidebar scrolling if navigation exceeds the viewport height.

### Mobile

Below 992px:

- Display navigation above the article.
- Collapse navigation by default.
- Provide an accessible "On This Page" toggle.
- Expand and collapse navigation using Bootstrap's built-in collapse component.
- Prioritize displaying actual page content without requiring users to scroll through the entire navigation menu.

The initial responsive collapse functionality is implemented.

Sticky positioning, automatic collapse after selecting a link, and active-section highlighting are optional subsequent enhancements.

## Feature Content Standards

Each feature should generally answer four questions:

1. **What is it?**
   Explain the feature in plain language.

2. **Why is it valuable?**
   Describe what the user gains from the feature.

3. **How does it work?**
   Provide a concise explanation of the primary workflow.

4. **What does it look like?**
   Demonstrate the feature through representative screenshots.

Content should:

- Lead with user benefits rather than technical implementation.
- Use concise, approachable language.
- Avoid developer terminology and database concepts.
- Explain permissions and confirmation requirements accurately.
- Emphasize features available to ordinary users.
- Avoid documenting capabilities that are incomplete or unavailable to beta testers.
- Avoid excessive procedural detail better suited to dedicated help documentation.

Not every section must follow an identical visual layout or length.

## Screenshots and Static Assets

Screenshots are stored in Django's static directory.

Recommended location:

`portal/static/portal/images/about/`

Organize screenshots by feature when appropriate.

Example:

```text
about/
├── recording-games/
│   ├── my-games.webp
│   └── add-game.webp
├── friends/
└── trends/
```

Screenshot guidelines:

- Prefer WebP when practical.
- Use descriptive filenames.
- Display images responsively.
- Provide meaningful alternative text.
- Use representative data that demonstrates the feature's value.
- Avoid exposing private player information.
- Avoid unnecessary browser chrome and development indicators.
- Consider an enlarged image viewer for complex interfaces.

Static images must not require authentication or dynamic database access.

## Security and Performance

The About page is publicly accessible at `/about/`.

It must:

- Render without authentication.
- Avoid querying private player data.
- Avoid generating statistics dynamically.
- Avoid exposing protected application endpoints.
- Use static screenshots instead of live player data.
- Remain lightweight enough to support potentially large volumes of anonymous traffic.

Public-page and static-asset caching should be evaluated before the beta launch.

Existing player privacy and authorization rules must remain unchanged.

## Development Workflow

The About page will be developed iteratively.

For each feature:

1. Load the relevant application source files.
2. Review the actual user workflow and permissions.
3. Identify the primary user benefits.
4. Determine which screenshots best demonstrate those benefits.
5. Agree on the feature's scope and messaging.
6. Implement or update its individual template partial.
7. Test desktop and mobile presentation.
8. Verify its sidebar anchor and navigation behavior.

Only the source files relevant to the current feature need to be loaded into the project context.

Avoid generating feature descriptions before understanding their actual implementation.

## Deferred Work

The Overview and Getting Started sections will be written after the major features are documented.

This allows their content to reflect the application's established capabilities and strongest selling points.

The final beta invitation will also be refined after the feature documentation is substantially complete.

## Guiding Principles

1. **One concept, one partial.** Keep feature documentation focused and maintainable.
2. **The sidebar owns navigation hierarchy.** Feature partials do not need to represent entire navigation categories.
3. **The parent owns reading order.** `about.html` determines where each feature appears.
4. **Mobile usability comes first.** Visitors should quickly understand the application's value.
5. **Show the application.** Screenshots should carry much of the explanation.
6. **Sell the benefit, explain the workflow.** The page is both a product showcase and a lightweight guide.
7. **Keep it static and secure.** Anonymous visitors must never require access to protected player data.
8. **Build incrementally.** Complete and validate individual sections without restructuring the entire page.
9. **Prefer existing tools.** Use Django templates and Bootstrap rather than introducing unnecessary dependencies.
10. **Maintain consistency.** New sections should follow these standards unless there is a clear reason to revise them.
