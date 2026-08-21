# Wingspan Stats Portal

A Dockerized Django application for recording, managing, and analyzing statistics from games of Wingspan.

## Stack

- Django
- PostgreSQL
- Gunicorn
- Nginx
- Docker Compose
- Bootstrap
- Plotly

## Architecture

```text
Browser
   │
 Nginx
   │
Gunicorn / Django
   │
PostgreSQL
```

The project uses layered Docker Compose configuration:

| File | Purpose |
|---|---|
| `docker-compose.yml` | Shared configuration |
| `docker-compose.dev.yml` | Development overrides |
| `docker-compose.prod.yml` | Production overrides |

## Development

Create a `.env` file using `.env.example` as a reference.

Start the development environment:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.dev.yml \
  up --build
```

The application is available at:

```text
http://localhost
```

Stop the environment:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.dev.yml \
  down
```

## Database Migrations

After changing Django models, generate migrations:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.dev.yml \
  exec django \
  python manage.py makemigrations
```

Migration files should be committed to Git.

The Django container automatically applies pending migrations and collects static files when it starts.

## Production

Production deployment and maintenance procedures are documented in:

```text
docs/operations.md
```
