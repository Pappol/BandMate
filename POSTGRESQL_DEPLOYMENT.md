# BandMate PostgreSQL Deployment Guide

This guide covers deploying BandMate with PostgreSQL as the production database.

## Prerequisites

- Docker and Docker Compose installed
- PostgreSQL client tools (optional, for direct database access)
- Domain name configured (for production)

## Quick Start

### 1. Environment Setup

```bash
# Copy production environment template
cp env.production .env

# Edit .env with your actual values
nano .env
```

### 2. Database Initialization

```bash
# Start PostgreSQL container
docker-compose -f docker-compose.prod.yml up db -d

# Wait for database to be ready
docker-compose -f docker-compose.prod.yml logs db

# Initialize database with comprehensive seed data
python manage.py init-db
```

### 3. Start Application

```bash
# Start all services
docker-compose -f docker-compose.prod.yml up -d

# Check logs
docker-compose -f docker-compose.prod.yml logs -f web
```

## Manual Setup (Without Docker)

### 1. Install PostgreSQL

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

**macOS (with Homebrew):**
```bash
brew install postgresql
brew services start postgresql
```

**Windows:**
Download from [postgresql.org](https://www.postgresql.org/download/windows/)

### 2. Create Database and User

```sql
-- Connect to PostgreSQL as superuser
sudo -u postgres psql

-- Create database
CREATE DATABASE bandmate_prod;

-- Create user
CREATE USER bandmate_user WITH PASSWORD 'your-secure-password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE bandmate_prod TO bandmate_user;
GRANT ALL ON SCHEMA public TO bandmate_user;

-- Exit
\q
```

### 3. Install Python Dependencies

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export FLASK_ENV=production
export DATABASE_URL=postgresql://bandmate_user:your-password@localhost:5432/bandmate_prod
export FLASK_SECRET_KEY=your-secret-key
# ... other environment variables

# Initialize database
python manage.py init-db
```

### 4. Run Application

```bash
# Using Gunicorn (recommended for production)
gunicorn --bind 0.0.0.0:5000 --workers 4 --timeout 120 manage:app

# Or using Flask development server (not recommended for production)
python manage.py run
```

## Cloud Deployment

### Render.com

1. **Create PostgreSQL Database:**
   - Go to Render Dashboard
   - Create new PostgreSQL service
   - Note the connection string

2. **Deploy Web Service:**
   - Connect your GitHub repository
   - Set build command: `pip install -r requirements.txt`
   - Set start command: `gunicorn manage:app`
   - Add environment variables from your `.env` file

3. **Initialize Database:**
   ```bash
   # Connect to your Render service
   render run python manage.py init-db
   ```

### Railway

1. **Add PostgreSQL:**
   - Add PostgreSQL service to your project
   - Note the connection string

2. **Deploy:**
   - Connect GitHub repository
   - Set environment variables
   - Deploy automatically

3. **Initialize:**
   ```bash
   railway run python manage.py init-db
   ```

### Fly.io

1. **Create PostgreSQL:**
   ```bash
   fly postgres create
   fly postgres attach <your-postgres-app>
   ```

2. **Deploy:**
   ```bash
   fly deploy
   ```

3. **Initialize:**
   ```bash
   fly ssh console
   python manage.py init-db
   ```

## Database Management

### Seed Data Commands

```bash
# Load comprehensive production data
python manage.py seed-comprehensive

# Load basic demo data
python manage.py seed

# Reset database (WARNING: deletes all data)
python manage.py reset

# Check database status
python manage.py status
```

### Database Backup

```bash
# Backup database
pg_dump -h localhost -U bandmate_user bandmate_prod > backup.sql

# Restore database
psql -h localhost -U bandmate_user bandmate_prod < backup.sql
```

### Database Maintenance

```bash
# Connect to database
psql -h localhost -U bandmate_user bandmate_prod

# Check database size
SELECT pg_size_pretty(pg_database_size('bandmate_prod'));

# Check table sizes
SELECT schemaname,tablename,pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables WHERE schemaname = 'public' ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

# Vacuum database
VACUUM ANALYZE;
```

## Performance Optimization

### Database Configuration

Edit `postgresql.conf` for production:

```conf
# Memory settings
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB

# Connection settings
max_connections = 100

# Logging
log_statement = 'mod'
log_min_duration_statement = 1000

# Checkpoint settings
checkpoint_completion_target = 0.9
```

### Application Configuration

Update your `.env` file:

```bash
# Database connection pooling
SQLALCHEMY_ENGINE_OPTIONS={"pool_size": 10, "pool_recycle": 120, "pool_pre_ping": true, "max_overflow": 20}

# Enable query logging for debugging
SQLALCHEMY_ECHO=false
```

## Monitoring

### Database Monitoring

```sql
-- Check active connections
SELECT count(*) FROM pg_stat_activity;

-- Check slow queries
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- Check table statistics
SELECT schemaname, tablename, n_tup_ins, n_tup_upd, n_tup_del 
FROM pg_stat_user_tables;
```

### Application Monitoring

Add to your application:

```python
# In your app/__init__.py
import logging
logging.basicConfig(level=logging.INFO)

# Monitor database connections
@app.before_request
def log_db_connections():
    if hasattr(db.engine.pool, 'size'):
        logging.info(f"DB Pool: {db.engine.pool.size()} connections")
```

## Security Checklist

- [ ] Strong database password
- [ ] Database user has minimal required privileges
- [ ] SSL/TLS enabled for database connections
- [ ] Firewall rules configured
- [ ] Regular security updates
- [ ] Database backups encrypted
- [ ] No sensitive data in logs
- [ ] Environment variables secured

## Troubleshooting

### Common Issues

1. **Connection Refused:**
   ```bash
   # Check if PostgreSQL is running
   sudo systemctl status postgresql
   
   # Check connection
   psql -h localhost -U bandmate_user -d bandmate_prod
   ```

2. **Permission Denied:**
   ```sql
   -- Grant proper permissions
   GRANT ALL PRIVILEGES ON DATABASE bandmate_prod TO bandmate_user;
   GRANT ALL ON SCHEMA public TO bandmate_user;
   ```

3. **Out of Memory:**
   ```bash
   # Check memory usage
   free -h
   
   # Adjust PostgreSQL settings
   # Edit postgresql.conf: shared_buffers, work_mem
   ```

4. **Slow Queries:**
   ```sql
   -- Enable query logging
   ALTER SYSTEM SET log_statement = 'all';
   SELECT pg_reload_conf();
   ```

### Getting Help

1. Check application logs: `docker-compose logs web`
2. Check database logs: `docker-compose logs db`
3. Check PostgreSQL logs: `/var/log/postgresql/`
4. Monitor database performance: `pg_stat_statements`

## Next Steps

After successful deployment:

1. **Test All Features:**
   - User registration/login
   - Band management
   - Song management
   - Setlist generation
   - API endpoints

2. **Set Up Monitoring:**
   - Database performance monitoring
   - Application error tracking
   - Uptime monitoring

3. **Configure Backups:**
   - Automated daily backups
   - Test restore procedures
   - Off-site backup storage

4. **Security Hardening:**
   - SSL certificates
   - Firewall configuration
   - Regular security updates
