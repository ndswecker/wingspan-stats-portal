# Wingspan Stats Portal

Dockerized statistics portal for Wingspan game analysis.

## Running the Development Environment

The project uses a layered Docker Compose configuration. The base `docker-compose.yml` defines the common infrastructure, while `docker-compose.dev.yml` contains development-specific overrides such as bind mounts, development settings, and automatic code reloading.

Start the development environment with:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.dev.yml \
  up --build
```

Once the containers have started, the application is available at:

* **Application:** http://localhost
* **PostgreSQL:** localhost:5432

During startup, the Django entrypoint automatically:

* Applies any pending database migrations
* Collects static files
* Starts Gunicorn in development mode with automatic code reloading

To stop the development environment:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.dev.yml \
  down
```
