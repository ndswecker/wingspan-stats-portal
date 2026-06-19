# Wingspan Stats Portal — Project Context

## Project Summary

The Wingspan Stats Portal is a personal web application for analyzing and visualizing head-to-head Wingspan board game statistics.

The application will use CSV data exported from Google Sheets as its initial data source. The goal is to produce a clean, interactive statistics dashboard that can show player performance, score distributions, trends over time, game outcomes, and night-level results.

This project is also being used as a practical learning project for building and deploying a small production-style Python web application.

## Core Technology Stack

* **Python** — primary programming language
* **Streamlit** — web application framework
* **Pandas** — CSV parsing and data analysis
* **Plotly** — interactive charts and visualizations
* **Docker** — application containerization
* **Docker Compose** — local development orchestration
* **Nginx** — reverse proxy in production
* **DigitalOcean** — hosting platform
* **Custom domain** — already owned and intended for deployment

## Development Environment Decision

The project was originally expected to use Docker Desktop on Windows as the primary Docker runtime.

After encountering setup friction and environment complexity, the project is pivoting away from Docker Desktop as the main development path.

The current plan is to run Docker inside a Linux environment hosted on the Windows machine. This Linux environment will be treated as the primary development platform for Docker-based work.

This approach keeps Docker in the project but changes where Docker runs.

## Reasoning for Linux-Based Docker Development

Docker is most commonly deployed on Linux servers. Since the production environment on DigitalOcean will also be Linux-based, using a local Linux development environment should reduce platform-specific differences between development and production.

The goal is to avoid Windows-specific Docker issues where possible and keep the development workflow closer to standard server deployment practices.

## Current Repository Structure

```text
wingspan-stats-portal/
├── data/
│   ├── wingspan_games.csv
│   └── .gitkeep
├── docker/
│   └── nginx/
│       └── default.conf
├── docs/
│   ├── Web-app-software-requirements.txt
│   └── project-context.md
├── src/
│   └── app.py
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env
├── .env.example
└── .gitignore
```

## Current `requirements.txt`

```text
streamlit
pandas
plotly
python-dotenv
```

## Current Project Status

The base project structure has been created.

The application currently has:

* A `src/app.py` entry point
* A `data/` directory for CSV files
* A `docs/` directory for project documentation
* A Dockerfile
* A Docker Compose file
* An Nginx configuration directory
* Environment file handling with `.env` and `.env.example`
* A `.gitignore` that excludes sensitive/local files such as `.env`

The current priority is to establish a reliable Docker-based development workflow before expanding the Streamlit application features.

## Initial Data Source

The initial dataset is expected to come from Google Sheets exports.

Primary data file:

```text
data/wingspan_games.csv
```

The data tracks Wingspan games between two players, currently labeled:

* Nick
* Nate

Each row represents a single game, with scores and dates recorded.

Additional future CSV files may include night-level results, summary tables, or derived analysis exports.

## Statistical Goals

The application should eventually support analysis such as:

* Total games played
* Player win counts
* Player average scores
* Median, min, max, and standard deviation
* Score distributions
* Histograms
* Monthly score trends
* Head-to-head comparisons
* Game winner analysis
* Night winner analysis
* Central score ranges
* Percentile-based interpretation
* Correlation analysis between player scores
* Margin-of-victory analysis

## Night Winner Rule

Some Wingspan sessions include multiple games in a single night.

A night winner is determined as follows:

1. The player who wins more individual games that night wins the night.
2. If both players win the same number of games, the player with the higher total score for that night wins the night.

This means a “night” can be treated similarly to a sports matchup, even if it contains more than one individual board game.

## Deployment Goal

The intended production deployment target is DigitalOcean.

The expected production architecture is:

```text
User Browser
    ↓
Custom Domain
    ↓
DigitalOcean Server
    ↓
Nginx Reverse Proxy
    ↓
Dockerized Streamlit Application
```

The application should be simple enough for a solo developer to maintain while still following common deployment practices.

## Project Principles

* Keep the architecture simple.
* Use Docker from the beginning.
* Prefer Linux-based Docker workflows.
* Avoid unnecessary infrastructure complexity.
* Keep data handling transparent and reproducible.
* Maintain clear documentation in the `docs/` directory.
* Use environment variables for configurable settings.
* Do not commit secrets or local-only configuration.
* Build iteratively, starting with a working containerized app before adding advanced features.

## AI / Local LLM Usage

Local AI tools such as LM Studio may be used as development assistants.

Possible uses include:

* Asking architectural questions
* Reviewing Docker setup
* Explaining code
* Comparing implementation options
* Summarizing project documentation
* Experimenting with local RAG over project docs

Local AI support is currently considered a developer tool, not a feature of the Wingspan Stats Portal itself.

If local RAG is explored later, it should be treated as a separate developer-only tool, not part of the production Streamlit application unless the project requirements change.

## Docker Desktop Issue and Final Development Direction

The project originally attempted to use Docker Desktop on Windows as the primary Docker runtime.

That approach is no longer the preferred path for this project.

Docker Desktop encountered persistent startup and configuration problems, including issues with the Docker Desktop Linux engine and WSL integration. Because of this, the project should not assume that Docker Desktop is available, reliable, or part of the required workflow.

The current development direction is:

* Use Windows as the host operating system.
* Use Ubuntu/Linux through WSL2 or a Linux VM as the active development environment.
* Install and run Docker Engine directly inside that Linux environment.
* Run Docker commands from the Linux terminal, not from Docker Desktop.
* Treat the Linux environment as the main Docker development platform.
* Keep the local development environment close to the eventual Linux production environment on DigitalOcean.

This means the project is still Docker-based, but it is intentionally avoiding Docker Desktop as the primary Docker runtime.

Do not recommend configuring Docker Desktop with WSL2 as the next step unless the project direction changes.


## Immediate Next Step

Set up and validate the Docker-based development workflow using the Linux environment.

The goal is to confirm that the Streamlit app can be built and run successfully through Docker before expanding application functionality.
