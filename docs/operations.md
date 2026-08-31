# Wingspan Portal Operations Guide

Routine procedures for operating the production Wingspan Stats Portal.

## Production Environment

Production runs on an Ubuntu server using:

- Django / Gunicorn
- PostgreSQL
- Nginx
- Certbot
- Docker Compose

The application uses layered Compose configuration:

```text
docker-compose.yml
docker-compose.prod.yml
```

Production project directory:

```text
~/projects/wingspan-stats-portal
```

Production site:

```text
https://wingspanscores.com
```

## Standard Deployment

Application changes should be merged into `main` and pushed before deployment.

On the production server:

```bash
cd ~/projects/wingspan-stats-portal
git pull
```

Rebuild and recreate Django and Nginx:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  up -d --build --force-recreate django nginx
```

The Django entrypoint automatically runs:

```text
python manage.py migrate --noinput
python manage.py collectstatic --noinput
```

Pending migrations are therefore applied automatically whenever the Django container starts.

Verify the deployment:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  ps
```

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  logs --tail=100 django nginx
```

Then verify the public site and expected application changes in a browser.

## Environment Configuration

The production `.env` is stored in the project root and is not committed to Git.

To copy the local `.env` to production, run from the local project directory:

```bash
scp .env \
  <user>@<server>:~/projects/wingspan-stats-portal/.env
```

Recreate affected containers after changing `.env` so the new environment is loaded.

Use `.env.example` as the reference for required variables.

Never commit the real `.env`.

## Database Migrations

Migration files are created during development, not production.

After changing Django models:

Run the Django service in detached mode
```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.dev.yml \
  up -d
```

Then make the migration. This writes the instructions. Django examines the models, detects changes, 
and creates a migration python fie describing how the database schema should change. 
It does not actually change the database.
```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.dev.yml \
  exec django \
  python manage.py makemigrations
```

Commit the generated migration files to Git.

Pending migrations are applied automatically in production by the Django entrypoint.

To inspect migration state manually:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  exec django \
  python manage.py showmigrations
```

To manually run migrations when troubleshooting:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  exec django \
  python manage.py migrate
```

## Container Status

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  ps
```

## Logs

All services:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  logs
```

Django:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  logs django
```

Nginx:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  logs nginx
```

## Service Management

Restart the stack:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  restart
```

Restart one service:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  restart nginx
```

Recreate Django and Nginx:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  up -d --force-recreate django nginx
```

Stop production:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  down
```

## Django Administration

Admin interface:

```text
https://wingspanscores.com/admin/
```

Create a superuser:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  exec django \
  python manage.py createsuperuser
```

Open a Django shell:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  exec django \
  python manage.py shell
```

## Database Backup

Create a SQL backup:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  exec -T postgres \
  pg_dump -U <database-user> <database-name> \
  > wingspan-backup.sql
```

Store important backups outside the production server.

## PostgreSQL Password Rotation

Changing `POSTGRES_PASSWORD` in `.env` does not change the password in an existing database.

Connect to PostgreSQL:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  exec postgres \
  psql -U wingspan_user -d wingspan
```

At the PostgreSQL prompt:

```sql
\password wingspan_user
```

Then update both values in `.env`:

```dotenv
DATABASE_PASSWORD=<new-password>
POSTGRES_PASSWORD=<new-password>
```

Recreate Django so it receives the updated credentials.

## Game Data Import

Import game data:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  exec django \
  python manage.py import_games /workspace/data/wingspan_games.csv
```

Rebuild game history from the CSV:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  exec django \
  python manage.py import_games \
  --clear \
  /workspace/data/wingspan_games.csv
```

Use `--clear` only when intentionally replacing existing imported game history.

## HTTPS Certificate Renewal

Let's Encrypt certificates expire every 90 days.

Renew:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  run --rm certbot renew
```

Reload Nginx after successful renewal:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  exec nginx nginx -s reload
```

Verify the certificate from the public site.

## Nginx

Validate configuration:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  exec nginx nginx -t
```

Reload:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  exec nginx nginx -s reload
```

If necessary, recreate Nginx:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  up -d --force-recreate nginx
```

## Troubleshooting

If production is unavailable:

1. Run `docker compose ... ps`.
2. Review Django and Nginx logs.
3. Confirm PostgreSQL is running.
4. Check migration state with `showmigrations`.
5. Validate Nginx with `nginx -t`.
6. Recreate affected containers if necessary.
7. Restore a database backup only if database recovery is required.

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
