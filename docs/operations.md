# Wingspan Portal Operations Guide

This document describes the routine operational procedures for maintaining the production Wingspan Portal deployment.

---

# Production Architecture

Production consists of the following services:

- Django
- Gunicorn
- PostgreSQL
- Nginx
- Certbot

The production environment is managed using layered Docker Compose files:

```text
docker-compose.yml
docker-compose.prod.yml
```

---

# Deployment

Deploy the latest version of the application.

## Update the application

Pull the latest changes and rebuild the application containers.

```bash
git pull

docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  up -d --build --force-recreate django nginx
```

This rebuilds the Django image and recreates both the Django and Nginx containers to ensure Nginx reconnects to the current Gunicorn instance.

## Verify the deployment

Confirm the containers are running.

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  ps
```

Review the application logs.

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  logs --tail=100 django nginx
```

Finally, verify the deployment by:

- Opening the public website.
- Confirming the home page loads successfully.
- Logging into the Django admin.
- Checking that the expected application changes are present.

---

# Database Migrations

## Local
Ensure the local django service is running:
```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.dev.yml \
  up -d
```

Generate the migration file
Then 
```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.dev.yml \
  exec django \
  python manage.py makemigrations
```

Then apply the migration
```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.dev.yml \
  exec django \
  python manage.py migrate
```



## Production

If a deployment contains new Django migrations, apply them.

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  exec django \
  python manage.py migrate
```

---

# Import Updated Game Data

Copy the latest CSV to the server.

Run the import command.

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  exec django \
  python manage.py import_games /workspace/data/wingspan_games.csv
```

To completely rebuild game history from the CSV:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  exec django \
  python manage.py import_games \
  --clear \
  /workspace/data/wingspan_games.csv
```

---

# Django Administration

Create a production superuser.

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  exec django \
  python manage.py createsuperuser
```

The Django administration interface is available at:

```
https://wingspanscores.com/admin/
```

---

# HTTPS Certificate Renewal

Let's Encrypt certificates expire every 90 days.

Renew approximately 30 days before expiration.

Run:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  run --rm certbot renew
```

If renewal succeeds, reload Nginx.

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  exec nginx nginx -s reload
```

Verify the certificate expiration using a web browser or another preferred certificate inspection tool.

---

# Nginx Configuration Changes

Validate the configuration.

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  exec nginx nginx -t
```

Reload Nginx.

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  exec nginx nginx -s reload
```

If a reload does not behave as expected, recreate the Nginx container.

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  up -d --force-recreate nginx
```

---

# Database Backup

Create a SQL backup.

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  exec -T postgres \
  pg_dump -U <database-user> <database-name> \
  > wingspan-backup.sql
```

Store backups outside of the production server whenever possible.

---

# Container Status

View running containers.

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  ps
```

---

# View Logs

View logs for all services.

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  logs
```

View logs for a single service.

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  logs django
```

Example:

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  logs nginx
```

---

# Restart Services

Restart the complete application.

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  restart
```

Restart a single service.

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  restart nginx
```

---

# Shut Down Production

Stop all running services.

```bash
docker compose \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  down
```

---

# Disaster Recovery Checklist

If a deployment fails:

1. Inspect container status.
2. Review container logs.
3. Verify PostgreSQL is running.
4. Verify Nginx configuration.
5. Verify migrations completed successfully.
6. Restore the latest database backup if required.

---

# Production Checklist

After each deployment verify:

- Home page loads.
- Games page loads.
- Django Admin loads.
- Static CSS and JavaScript load correctly.
- HTTPS certificate is valid.
- HTTP redirects to HTTPS.
- Database contains expected data.
- No unexpected errors appear in the logs.