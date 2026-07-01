# Wingspan Stats Portal

## Project Context

---

# Project Overview

The **Wingspan Stats Portal** is a full-stack web application for recording, managing, analyzing, and visualizing statistics from the board game *Wingspan*.

Unlike a simple statistics dashboard, the application serves as the complete system of record for game results. Authenticated users can submit games through the web interface, manage historical data, and explore statistical analyses generated directly from the application's database.

The project has two primary goals:

1. Build a polished, production-quality statistics portal for personal use and public hosting.
2. Demonstrate modern full-stack software engineering practices suitable for a professional software development portfolio.

---

# Project Goals

The application should:

- Provide an intuitive interface for entering Wingspan game results.
- Store all application data within a relational database.
- Generate statistical analyses and interactive visualizations from live data.
- Support authenticated users with appropriate permissions.
- Be deployable as a complete containerized application on a Linux server.
- Follow maintainable, industry-standard software architecture.

---

# Technology Stack

## Backend

- Python
- Django
- Django ORM

## Database

- PostgreSQL

## Visualization

- Pandas
- Plotly

## Frontend

- Django Templates
- HTML5
- CSS
- Bootstrap 5
- JavaScript (minimal where practical)

## Infrastructure

- Docker
- Docker Compose
- Nginx
- Ubuntu Linux

## Hosting

- Domain Registration: Namecheap
- DNS Management: Namecheap
- Hosting Provider: DigitalOcean Ubuntu Droplet

## Version Control

- Git
- GitHub

---

# Architectural Philosophy

The project follows several guiding principles.

## Database First

PostgreSQL is the single source of truth.

CSV files are no longer considered the application's primary data store.

CSV import and export functionality may be provided for convenience, but all application functionality operates from data stored within PostgreSQL.

---

## Django Owns the Application

Django is responsible for:

- Authentication
- Authorization
- Data validation
- Business logic
- Administration
- Routing
- Templates

All statistical analyses originate from data stored within PostgreSQL.

---

## Containerized Development

Every major component of the application executes within its own Docker container.

The initial deployment consists of:

- Django
- PostgreSQL
- Nginx

Docker Compose orchestrates the application stack for both development and production.

---

## Incremental Development

The project should be developed through small, working milestones.

Every completed milestone should remain fully deployable.

Avoid unnecessary complexity until a requirement justifies it.

---

# Deployment Architecture

```
Internet
    │
Domain Name (Namecheap)
    │
DigitalOcean Ubuntu Droplet
    │
Docker Compose
    │
├── Nginx
├── Django
└── PostgreSQL
```

The production environment should closely mirror the local Docker development environment.

---

# Authentication

The application supports authenticated users.

Authentication should use Django's built-in authentication framework.

Initial user roles:

- Administrator
- Standard User

Only authenticated users may modify application data.

Anonymous visitors may be permitted to browse public statistics.

---

# Data Model

The initial application consists of two primary entities.

## Player

Represents a Wingspan player.

Possible attributes include:

- Name
- Display Name
- Active Status

---

## Game

Represents one completed Wingspan game.

Possible attributes include:

- Date Played
- Nick Score
- Nate Score
- Winner
- Notes

Game nights (sessions) are **not** stored as a separate entity.

Instead, they are derived dynamically by grouping games played on the same calendar date. Statistics such as night winners and session summaries should be computed from the underlying game records rather than stored separately.

---

# Statistical Features

The application should support analysis including:

- Win/Loss Records
- Win Percentage
- Average Score
- Median
- Mode
- Minimum
- Maximum
- Standard Deviation
- Variance
- Histograms
- Score Distributions
- Monthly Trends
- Head-to-Head Comparisons
- Correlation Analysis
- Percentile Analysis
- Night Winner Analysis
- Historical Performance
- Interactive Filtering

All statistics should be generated dynamically from database queries.

---

# Data Management

The application should support:

- Creating Games
- Editing Games
- Deleting Games
- Viewing Historical Games
- Searching Historical Games
- CSV Import
- CSV Export

Appropriate validation should prevent incomplete or inconsistent records.

---

# Administration

Administrators should be able to:

- Manage Users
- Manage Players
- Correct Historical Data
- Import Historical Data
- Export Data
- Access the Django Administration Site

---

# User Interface

The interface should emphasize:

- Simplicity
- Responsiveness
- Accessibility
- Mobile Compatibility
- Readability

Interactive visualizations should be implemented using Plotly.

The application should prioritize fast page loads and minimize unnecessary client-side JavaScript.

---

# Docker Strategy

Development and production environments should closely mirror one another.

Docker Compose manages the complete application stack.

Persistent Docker volumes should be used for PostgreSQL data.

Application configuration should be managed through environment variables.

---

# Development Philosophy

When making architectural decisions, prioritize:

- Maintainability
- Readability
- Testability
- Production Readiness
- Clear Separation of Concerns
- Industry-Standard Practices

Every architectural decision should be justified by long-term maintainability rather than short-term convenience.

Development should proceed incrementally, validating each layer before introducing additional complexity.