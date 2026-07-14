# Wingspan Stats Portal

Dockerized statistics portal for Wingspan game analysis.

## Running the Development Environment

The project uses a layered Docker Compose configuration:

- `docker-compose.yml` contains the shared infrastructure used by all environments.
- `docker-compose.dev.yml` contains development-specific overrides.
- `docker-compose.prod.yml` contains production-specific overrides.

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

- Applies any pending database migrations
- Collects static files

The development Docker Compose configuration then starts Gunicorn with automatic code reloading.

To stop the development environment:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.dev.yml \
  down
```

## Running the Production Environment

The production configuration uses the same shared Docker Compose base configuration while applying production-specific overrides.

Start the production environment with:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  up --build


## Rotating the PostgreSQL Password

The PostgreSQL password stored in `.env` is **only used when initializing a brand-new database**. Updating `.env` alone does **not** change the password stored inside an existing PostgreSQL database.

To rotate the database password on an existing development database:

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

* `DATABASE_PASSWORD` is used by Django when connecting to PostgreSQL.
* `POSTGRES_PASSWORD` is used only when initializing a brand-new PostgreSQL database, but should be kept synchronized for consistency.

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

| Credential                 | Purpose                                                                                                                                                                   |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `DJANGO_SECRET_KEY`        | Cryptographically signs sessions, CSRF tokens, password reset tokens, and other Django-generated values. Changing it logs users out but does **not** affect the database. |
| `DATABASE_PASSWORD`        | Used by Django to authenticate with PostgreSQL.                                                                                                                           |
| Django Admin User Password | Used to sign in to the Django Administration site (`/admin`). Stored inside the database and completely independent of the PostgreSQL password.                           |

