# BandMate Deployment Guide

This guide covers deploying the BandMate application to various platforms.

## Prerequisites

Before deploying, ensure you have:

1. ✅ All tests passing locally (`make test`)
2. ✅ Code quality checks passing (`make lint`)
3. ✅ Environment variables configured
4. ✅ Database migrations ready
5. ✅ Google OAuth credentials set up

## Environment Variables for Production

Create a `.env` file with these production settings:

```bash
FLASK_ENV=production
FLASK_SECRET_KEY=<strong-random-secret-key>
DATABASE_URL=<your-production-database-url>
GOOGLE_CLIENT_ID=<your-google-client-id>
GOOGLE_CLIENT_SECRET=<your-google-client-secret>
OAUTH_REDIRECT_URI=https://yourdomain.com/login/google/authorized
```

## Deployment Options

### 1. Render (Recommended for MVP)

Render is a great platform for Flask applications with a generous free tier.

#### Setup Steps:

1. **Connect Repository**
   - Sign up at [render.com](https://render.com)
   - Connect your GitHub repository

2. **Create New Web Service**
   - Choose "Web Service"
   - Select your BandMate repository
   - Set branch to `main`

3. **Configure Service**
   ```
   Name: bandmate
   Environment: Python 3
   Build Command: pip install -r requirements.txt
   Start Command: gunicorn manage:app
   ```

4. **Set Environment Variables**
   - Add all variables from your `.env` file
   - Ensure `FLASK_ENV=production`

5. **Deploy**
   - Click "Create Web Service"
   - Wait for build and deployment

#### Render-specific Notes:
- Free tier includes 750 hours/month
- Automatic HTTPS
- Custom domains supported
- Built-in logging and monitoring

### 2. Fly.io

Fly.io offers global deployment with edge locations.

#### Setup Steps:

1. **Install flyctl**
   ```bash
   curl -L https://fly.io/install.sh | sh
   ```

2. **Login and Create App**
   ```bash
   fly auth login
   fly apps create bandmate
   ```

3. **Deploy**
   ```bash
   fly deploy
   ```

4. **Set Secrets**
   ```bash
   fly secrets set FLASK_SECRET_KEY="your-secret"
   fly secrets set GOOGLE_CLIENT_ID="your-client-id"
   # ... set other secrets
   ```

#### Fly.io-specific Notes:
- Global edge deployment
- Free tier includes 3 shared-cpu VMs
- Automatic HTTPS with Let's Encrypt
- Built-in PostgreSQL (optional)

### 3. Railway

Railway provides simple deployment with automatic scaling.

#### Setup Steps:

1. **Connect Repository**
   - Sign up at [railway.app](https://railway.app)
   - Connect your GitHub repository

2. **Configure Service**
   - Set build command: `pip install -r requirements.txt`
   - Set start command: `gunicorn manage:app`

3. **Set Environment Variables**
   - Add all required environment variables

4. **Deploy**
   - Railway will automatically deploy on push

### 4. Heroku (Legacy)

While Heroku no longer offers a free tier, it's still a solid option for paid deployments.

#### Setup Steps:

1. **Install Heroku CLI**
   ```bash
   # macOS
   brew tap heroku/brew && brew install heroku
   
   # Linux
   curl https://cli-assets.heroku.com/install.sh | sh
   ```

2. **Create App**
   ```bash
   heroku create your-bandmate-app
   ```

3. **Set Environment Variables**
   ```bash
   heroku config:set FLASK_ENV=production
   heroku config:set FLASK_SECRET_KEY="your-secret"
   # ... set other variables
   ```

4. **Deploy**
   ```bash
   git push heroku main
   ```

## Database Options

### SQLite (Development/Testing)
- Good for development and small deployments
- File-based, no external dependencies
- Limited concurrent access

### PostgreSQL (Production)
- Recommended for production use
- Better performance and concurrency
- Built-in support in most platforms

#### Setting up PostgreSQL:

**Render:**
- Create a new PostgreSQL service
- Use the provided connection string

**Fly.io:**
```bash
fly postgres create
fly postgres attach <your-postgres-app>
```

**Railway:**
- Add PostgreSQL plugin
- Use the provided connection string

## SSL/HTTPS Configuration

### Automatic (Recommended)
Most platforms provide automatic HTTPS:
- Render: ✅ Automatic
- Fly.io: ✅ Automatic with Let's Encrypt
- Railway: ✅ Automatic
- Heroku: ✅ Automatic

### Manual Configuration
If you need to configure SSL manually:

1. **Obtain SSL Certificate**
   - Use Let's Encrypt (free)
   - Or purchase from a certificate authority

2. **Configure Web Server**
   - Nginx/Apache configuration
   - SSL certificate paths
   - Redirect HTTP to HTTPS

## Monitoring and Logging

### Built-in Logging
The app includes basic logging:
```python
import logging
logging.basicConfig(level=logging.INFO)
```

### External Monitoring
Consider adding:
- **Sentry**: Error tracking
- **Uptime Robot**: Uptime monitoring
- **Google Analytics**: User analytics

## Performance Optimization

### Production Settings
```bash
FLASK_ENV=production
FLASK_DEBUG=false
```

### Gunicorn Configuration
```bash
gunicorn --workers 4 --bind 0.0.0.0:5000 --timeout 120 manage:app
```

### Database Optimization
- Enable connection pooling
- Use database indexes
- Regular maintenance tasks

## Security Checklist

- [ ] `FLASK_SECRET_KEY` is strong and unique
- [ ] `FLASK_ENV=production`
- [ ] HTTPS enabled
- [ ] Google OAuth redirect URI matches production domain
- [ ] Database credentials are secure
- [ ] No sensitive data in logs
- [ ] Rate limiting enabled (optional)
- [ ] CORS configured properly (if needed)

## Troubleshooting

### Common Issues

1. **Build Failures**
   - Check Python version compatibility
   - Verify all dependencies in `requirements.txt`
   - Check build logs for specific errors

2. **Runtime Errors**
   - Verify environment variables
   - Check database connectivity
   - Review application logs

3. **OAuth Issues**
   - Ensure redirect URI matches exactly
   - Check Google OAuth credentials
   - Verify domain verification

### Getting Help

1. Check the application logs
2. Review platform-specific documentation
3. Check the [BandMate GitHub issues](https://github.com/your-repo/issues)
4. Review Flask and platform documentation

## Post-Deployment

After successful deployment:

1. **Test All Features**
   - User registration/login
   - Song management
   - Setlist generation
   - API endpoints

2. **Monitor Performance**
   - Response times
   - Error rates
   - Resource usage

3. **Set Up Backups**
   - Database backups
   - Configuration backups
   - Regular backup testing

4. **Documentation**
   - Update deployment notes
   - Document any custom configurations
   - Share with team members

## Cost Estimation

### Free Tiers
- **Render**: $0/month (750 hours)
- **Fly.io**: $0/month (3 shared VMs)
- **Railway**: $0/month (limited usage)

### Paid Plans
- **Render**: $7/month (unlimited)
- **Fly.io**: $1.94/month per VM
- **Railway**: $5/month (unlimited)
- **Heroku**: $7/month (basic dyno)

Choose based on your expected traffic and budget requirements.
