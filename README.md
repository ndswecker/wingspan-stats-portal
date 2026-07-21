# Wingspan Stats Portal

A Dockerized Django application for recording, managing, and analyzing statistics from games of Wingspan.

The application consists of:

- Django
- PostgreSQL
- Nginx
- Docker Compose

Development and production environments share the same Docker Compose base configuration with environment-specific override files.

---

## Docker Compose Configuration

The project uses a layered Docker Compose configuration.

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Shared infrastructure used by all environments |
| `docker-compose.dev.yml` | Development-specific overrides |
| `docker-compose.prod.yml` | Production-specific overrides |

---

## Running the Development Environment

Start the development environment with:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.dev.yml \
  up --build
```

Once the containers have started, the application is available at:

- **Application:** http://localhost
- **PostgreSQL:** localhost:5432

During startup, the Django entrypoint automatically:

- Applies any pending database migrations
- Collects static files

The development override starts Gunicorn with automatic code reloading while bind-mounting the project source into the container.

To stop the development environment:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.dev.yml \
  down
```

---

## Running the Production Environment

The production configuration reuses the shared Docker Compose stack while enabling production-specific settings such as:

- Production Django settings
- Gunicorn worker configuration
- Nginx reverse proxy
- TLS certificate support (Let's Encrypt)
- Production environment variables

Start the production environment with:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  up --build -d
```

The production `.env` file is **not committed** to Git and must be copied to the deployment server separately.

---

## Production Deployment

The application is deployed to an Ubuntu server using Docker Compose.

Typical deployment workflow:

1. Commit application changes.
2. Push changes to GitHub.
3. Pull the latest changes on the production server.
4. Copy the production `.env` file to the server.
5. Start or restart the production Docker Compose stack.
6. Verify the application is running correctly.

---

## HTTPS

Production HTTPS is provided by:

- Nginx
- Let's Encrypt
- Certbot

Nginx terminates TLS connections and proxies requests to the Django application container.

TLS certificates are stored in Docker volumes and are **not** committed to source control.

---

## Environment Variables

Application configuration is supplied through a local `.env` file.

Important environment variables include:

| Variable | Purpose |
|----------|---------|
| `DJANGO_SECRET_KEY` | Django cryptographic secret key |
| `DJANGO_ALLOWED_HOSTS` | Allowed hostnames for the application |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Trusted origins for CSRF validation |
| `DATABASE_NAME` | PostgreSQL database name |
| `DATABASE_USER` | PostgreSQL username |
| `DATABASE_PASSWORD` | PostgreSQL password used by Django |
| `DATABASE_HOST` | PostgreSQL hostname |
| `DATABASE_PORT` | PostgreSQL port |
| `POSTGRES_DB` | Database created during PostgreSQL initialization |
| `POSTGRES_USER` | PostgreSQL initialization user |
| `POSTGRES_PASSWORD` | PostgreSQL initialization password |

---

## Initial Data Import

Historical Wingspan data can be imported into a new database using the project's custom Django management command after the production database has been initialized.

> **Note:** Documentation for the import process will be added once the import workflow has been finalized.

---

## Rotating the PostgreSQL Password

The PostgreSQL password stored in `.env` is **only used when initializing a brand-new database**. Updating `.env` alone does **not** change the password stored inside an existing PostgreSQL database.

### 1. Start only the PostgreSQL service

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.dev.yml \
  up -d postgres
```

### 2. Connect to PostgreSQL

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.dev.yml \
  exec postgres \
  psql -U wingspan_user -d wingspan
```

> **Note:** This project initializes PostgreSQL using the `wingspan_user` role. A `postgres` role is not automatically created.

### 3. Change the password

At the PostgreSQL prompt:

```sql
\password wingspan_user
```

Enter the new password twice when prompted.

Exit PostgreSQL:

```sql
\q
```

### 4. Update `.env`

Update both settings so they contain the same password:

```dotenv
DATABASE_PASSWORD=your-new-password
POSTGRES_PASSWORD=your-new-password
```

- `DATABASE_PASSWORD` is used by Django when connecting to PostgreSQL.
- `POSTGRES_PASSWORD` is used only when initializing a brand-new PostgreSQL database, but should be kept synchronized for consistency.

### 5. Restart the application

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.dev.yml \
  down
```

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.dev.yml \
  up --build
```

If the application starts successfully and Django connects to PostgreSQL without authentication errors, the password rotation was successful.

---

## Understanding the Different Credentials

The project uses three independent credentials:

| Credential | Purpose |
|------------|---------|
| `DJANGO_SECRET_KEY` | Cryptographically signs sessions, CSRF tokens, password reset tokens, and other Django-generated values. Changing it logs users out but does **not** affect the database. |
| `DATABASE_PASSWORD` | Used by Django to authenticate with PostgreSQL. |
| Django Admin User Password | Used to sign in to the Django Administration site (`/admin`). Stored inside the database and completely independent of the PostgreSQL password. |

---

## Production Architecture

```
                Browser
                   │
              HTTPS (443)
                   │
                Nginx
                   │
            HTTP (internal)
                   │
          Gunicorn / Django
                   │
              PostgreSQL
```

The application uses Nginx as a reverse proxy, Gunicorn as the WSGI application server, Django for the web application, and PostgreSQL as the system of record. Static assets are served directly by Nginx, while application requests are proxied to Django.