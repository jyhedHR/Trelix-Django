# Trelix Django Project

This project uses Django with PostgreSQL as the database.

## Initial Setup

### 1. Set up Python Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment (Windows)
venv\Scripts\activate
```

You should now see `(venv)` at the start of your terminal prompt.

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Create .env File

Create a `.env` file in the root of your project:

```ini
DB_NAME=trelix_db
DB_USER=trelix_user
DB_PASSWORD=trelix
DB_HOST=127.0.0.1
DB_PORT=5432
```

### 4. Set up PostgreSQL Database

Open PostgreSQL terminal:

```bash
psql -U postgres
```

Create the database user with full privileges:

```sql
CREATE USER trelix_user WITH PASSWORD 'trelix' CREATEDB CREATEROLE LOGIN;
```

Create the database:

```sql
CREATE DATABASE trelix_db OWNER trelix_user;
GRANT ALL PRIVILEGES ON DATABASE trelix_db TO trelix_user;
```

Connect to the database and grant privileges on schemas and objects:

```sql
\c trelix_db
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO trelix_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO trelix_user;
GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO trelix_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON TABLES TO trelix_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON SEQUENCES TO trelix_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL PRIVILEGES ON FUNCTIONS TO trelix_user;
\q
```

### 5. Run Migrations

```bash
python manage.py migrate
```

### 6. Run Development Server

```bash
python manage.py runserver
```

Visit http://127.0.0.1:8000/ to see the project running.

---

## Development Workflow

### Adding New Dependencies

When you need to install a new library:

```bash
pip install <library_name>
```

Update requirements.txt:

```bash
pip freeze > requirements.txt
```

### Creating New Models

When you add new models to your Django app:

```bash
# Create migration files
python manage.py makemigrations Trelix

# Apply migrations to database
python manage.py migrate
```

---

## Quick Reference

| Task | Command |
|------|---------|
| Activate virtual environment | `venv\Scripts\activate` |
| Install packages | `pip install <package>` |
| Update requirements | `pip freeze > requirements.txt` |
| Connect to PostgreSQL | `psql -U postgres` |
| Make migrations | `python manage.py makemigrations Trelix` |
| Apply migrations | `python manage.py migrate` |
| Run server | `python manage.py runserver` |

## Notes

- Ensure PostgreSQL is installed and running
- Make sure the `.env` file matches your database credentials
- Always activate the virtual environment before running Django commands
- The user `trelix_user` has full control over `trelix_db`
