# Wingspan Portal Operations Guide

Routine procedures for operating the Wingspan Stats Portal.

## Production Environment

Production runs on Ubuntu with:

- Django / Gunicorn
- PostgreSQL
- Nginx
- Certbot
- Docker Compose

Production uses:

```text
docker-compose.yml
docker-compose.prod.yml
```

Project directory:

```text
~/projects/wingspan-stats-portal
```

## Standard Production Deployment

Application changes should be merged into `main` and pushed before deployment.

On the production server:

```bash
cd ~/projects/wingspan-stats-portal
git pull
```

Rebuild and recreate Django and Nginx:

```bash
docker compose   -f docker-compose.yml   -f docker-compose.prod.yml   up -d --build --force-recreate django nginx
```

The Django entrypoint automatically runs:

```text
python manage.py migrate --noinput
python manage.py collectstatic --noinput
```

Verify:

```bash
docker compose   -f docker-compose.yml   -f docker-compose.prod.yml   ps
```

```bash
docker compose   -f docker-compose.yml   -f docker-compose.prod.yml   logs --tail=100 django nginx
```

Then verify the public site in a browser.

## Development Environment

Start development:

```bash
docker compose   -f docker-compose.yml   -f docker-compose.dev.yml   up --build
```

Check status:

```bash
docker compose   -f docker-compose.yml   -f docker-compose.dev.yml   ps
```

## Environment Configuration

The real `.env` is not committed to Git.

Use `.env.example` as the reference for required variables.

To copy the local `.env` to production:

```bash
scp .env   <user>@<server>:~/projects/wingspan-stats-portal/.env
```

Recreate affected containers after changing `.env`.

## Database Migrations

Create migration files during development only.

```bash
docker compose   -f docker-compose.yml   -f docker-compose.dev.yml   exec django   python manage.py makemigrations
```

Commit generated migration files to Git.

Production applies pending migrations automatically when Django starts.

Inspect production migration state:

```bash
docker compose   -f docker-compose.yml   -f docker-compose.prod.yml   exec django   python manage.py showmigrations
```

## Production Database Backup

Backups are created manually.

Backup files are stored under:

```text
backups/
```

This directory is ignored by Git except for its placeholder file.

Create a PostgreSQL custom-format backup from the production project root:

```bash
docker compose   -f docker-compose.yml   -f docker-compose.prod.yml   exec -T postgres   pg_dump   -U wingspan_user   -d wingspan   -Fc   > backups/wingspan-prod-YYYY-MM-DD.dump
```

Verify the file exists:

```bash
ls -lh backups/
```

Validate the archive:

```bash
docker compose   -f docker-compose.yml   -f docker-compose.prod.yml   exec -T postgres   pg_restore --list   < backups/wingspan-prod-YYYY-MM-DD.dump
```

Important backups should also be stored outside the production server.

## Refresh Development from Production

This process completely replaces the local `wingspan` database with a production snapshot.

### 1. Transfer the Backup

From the local project root:

```bash
scp <user>@<server>:~/projects/wingspan-stats-portal/backups/wingspan-prod-YYYY-MM-DD.dump   backups/wingspan-prod-YYYY-MM-DD.dump
```

Verify:

```bash
ls -lh backups/
```

### 2. Start Local PostgreSQL

If the development stack is not running:

```bash
docker compose   -f docker-compose.yml   -f docker-compose.dev.yml   up -d
```

### 3. Stop Django and Nginx

Leave PostgreSQL running:

```bash
docker compose   -f docker-compose.yml   -f docker-compose.dev.yml   stop django nginx
```

Verify that only PostgreSQL remains running:

```bash
docker compose   -f docker-compose.yml   -f docker-compose.dev.yml   ps
```

### 4. Drop the Local Database

This destroys the current local `wingspan` database.

```bash
docker compose   -f docker-compose.yml   -f docker-compose.dev.yml   exec postgres   psql   -U wingspan_user   -d postgres   -c "DROP DATABASE wingspan WITH (FORCE);"
```

### 5. Recreate an Empty Database

```bash
docker compose   -f docker-compose.yml   -f docker-compose.dev.yml   exec postgres   psql   -U wingspan_user   -d postgres   -c "CREATE DATABASE wingspan OWNER wingspan_user;"
```

### 6. Restore the Production Backup

```bash
docker compose   -f docker-compose.yml   -f docker-compose.dev.yml   exec -T postgres   pg_restore   -U wingspan_user   -d wingspan   --exit-on-error   --verbose   < backups/wingspan-prod-YYYY-MM-DD.dump
```

### 7. Verify the Restore

List tables:

```bash
docker compose   -f docker-compose.yml   -f docker-compose.dev.yml   exec postgres   psql   -U wingspan_user   -d wingspan   -c '\dt'
```

Check representative row counts:

```bash
docker compose   -f docker-compose.yml   -f docker-compose.dev.yml   exec postgres   psql   -U wingspan_user   -d wingspan   -c "SELECT COUNT(*) FROM portal_game;"
```

```bash
docker compose   -f docker-compose.yml   -f docker-compose.dev.yml   exec postgres   psql   -U wingspan_user   -d wingspan   -c "SELECT COUNT(*) FROM portal_player;"
```

### 8. Start Development Normally

```bash
docker compose   -f docker-compose.yml   -f docker-compose.dev.yml   up --build
```

Then verify the local site and confirm that expected production data is present.

## Service Management

Production status:

```bash
docker compose   -f docker-compose.yml   -f docker-compose.prod.yml   ps
```

Restart production:

```bash
docker compose   -f docker-compose.yml   -f docker-compose.prod.yml   restart
```

Production logs:

```bash
docker compose   -f docker-compose.yml   -f docker-compose.prod.yml   logs
```

Django logs:

```bash
docker compose   -f docker-compose.yml   -f docker-compose.prod.yml   logs django
```

Nginx logs:

```bash
docker compose   -f docker-compose.yml   -f docker-compose.prod.yml   logs nginx
```

## Django Administration

Admin interface:

```text
https://wingspanscores.com/admin/
```

Create a superuser:

```bash
docker compose   -f docker-compose.yml   -f docker-compose.prod.yml   exec django   python manage.py createsuperuser
```

Open a Django shell:

```bash
docker compose   -f docker-compose.yml   -f docker-compose.prod.yml   exec django   python manage.py shell
```

## HTTPS Certificate Renewal

Renew:

```bash
docker compose   -f docker-compose.yml   -f docker-compose.prod.yml   run --rm certbot renew
```

Reload Nginx:

```bash
docker compose   -f docker-compose.yml   -f docker-compose.prod.yml   exec nginx nginx -s reload
```

## Nginx Validation

Validate configuration:

```bash
docker compose   -f docker-compose.yml   -f docker-compose.prod.yml   exec nginx nginx -t
```

Reload:

```bash
docker compose   -f docker-compose.yml   -f docker-compose.prod.yml   exec nginx nginx -s reload
```

## Troubleshooting

If production is unavailable:

1. Check container status with `docker compose ... ps`.
2. Review Django and Nginx logs.
3. Confirm PostgreSQL is running.
4. Check migration state with `showmigrations`.
5. Validate Nginx with `nginx -t`.
6. Recreate affected containers if necessary.
7. Restore a database backup only when database recovery is required.

## Deployment Checklist

After deployment verify:

- Containers are running.
- Home page loads.
- Games and statistics pages load.
- Login and Django Admin work.
- Expected changes are present.
- Static assets load.
- HTTPS works.
- No unexpected errors appear in Django or Nginx logs.
