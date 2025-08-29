# BandMate 🎸

A web application for bands to manage their song repertoire, track member progress, and generate optimized setlists for rehearsals and performances.

## Google OAuth Setup

To enable Google authentication and fix the `redirect_uri_mismatch` error, follow these steps:

### 1. Create Google Cloud Project
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google+ API and Google OAuth2 API

### 2. Configure OAuth Consent Screen
1. Go to "APIs & Services" > "OAuth consent screen"
2. Choose "External" user type
3. Fill in the required fields:
   - App name: "BandMate"
   - User support email: your email
   - Developer contact information: your email
4. Add scopes: `userinfo.email`, `userinfo.profile`, `openid`
5. Add test users (your email addresses)

### 3. Create OAuth 2.0 Credentials
1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth 2.0 Client IDs"
3. Choose "Web application"
4. Add authorized redirect URIs:
   - For local development: `http://localhost:5001/login/google/authorized`
   - For production: `https://yourdomain.com/login/google/authorized`

### 4. Configure Environment Variables
1. Copy `env.example` to `.env`
2. Update the following variables:
   ```bash
   GOOGLE_CLIENT_ID=your-actual-client-id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=your-actual-client-secret
   ```

**Important:** The redirect URI in your Google Cloud Console MUST exactly match `http://localhost:5001/login/google/authorized` for local development on port 5001.

## Features

- **Song Dashboard**: Track all active songs and member progress
- **Wishlist Management**: Propose new songs and vote on band additions
- **Progress Tracking**: Monitor individual member readiness for each song
- **Smart Setlist Generator**: Create optimized rehearsal setlists based on learning needs
- **Google OAuth**: Secure authentication using Google accounts
- **Responsive Design**: Mobile-first interface built with Tailwind CSS

## Tech Stack

- **Backend**: Python 3.11+, Flask
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: Google OAuth via Flask-Dance
- **Frontend**: Jinja2 templates + Alpine.js for interactivity
- **Styling**: Tailwind CSS
- **Testing**: pytest with factory_boy
- **Code Quality**: black, isort, flake8

## Quick Start

### Prerequisites

- Python 3.11 or higher
- Google OAuth credentials (see [Authentication Setup](#authentication-setup))

### Local Development

1. **Clone and setup**
   ```bash
   git clone <your-repo-url>
   cd bandmate
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Environment Configuration**
   ```bash
   cp .env.example .env
   # Edit .env with your Google OAuth credentials and other settings
   ```

3. **Database Setup**
   ```bash
   export FLASK_APP=manage.py
   export FLASK_ENV=development
   flask db upgrade
   python manage.py seed
   ```

4. **Run the Application**
   ```bash
   flask run
   ```
   
   Open [http://localhost:5000](http://localhost:5000) in your browser.

### Docker (Optional)

```bash
docker-compose up --build
```

## Authentication Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google+ API
4. Go to Credentials → Create Credentials → OAuth 2.0 Client ID
5. Set Application Type to "Web application"
6. Add authorized redirect URIs:
   - `http://localhost:5000/login/google/authorized` (development)
   - `https://yourdomain.com/login/google/authorized` (production)
7. Copy Client ID and Client Secret to your `.env` file

## Environment Variables

Create a `.env` file based on `.env.example`:

```bash
FLASK_SECRET_KEY=your-secret-key-here
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
OAUTH_REDIRECT_URI=http://localhost:5000/login/google/authorized
DATABASE_URL=sqlite:///bandmate.db
FLASK_ENV=development
```

## API Endpoints

### Main Routes
- `GET /` - Home page (redirects to dashboard if authenticated)
- `GET /dashboard` - Main dashboard with songs and progress
- `GET /wishlist` - Song wishlist and voting
- `GET /setlist` - Setlist generator interface

### API Endpoints
- `POST /progress` - Update song progress for current user
- `POST /wishlist/propose` - Add new song proposal
- `POST /wishlist/vote` - Toggle vote on song proposal
- `POST /wishlist/approve` - Approve song proposal (band leader only)
- `POST /generate_setlist` - Generate optimized setlist

### Example API Usage

```bash
# Update song progress
curl -X POST http://localhost:5000/progress \
  -H "Content-Type: application/json" \
  -d '{"song_id": 1, "status": "Ready for Rehearsal"}'

# Generate setlist
curl -X POST http://localhost:5000/generate_setlist \
  -H "Content-Type: application/json" \
  -d '{"duration_minutes_total": 120, "learning_ratio": 0.6}'
```

## Testing

Run the test suite:

```bash
pytest
```

Run with coverage:

```bash
pytest --cov=app
```

## Database Migrations

```bash
# Create new migration
flask db migrate -m "Description of changes"

# Apply migrations
flask db upgrade

# Rollback migration
flask db downgrade
```

## Seed Data

The application comes with demo data including:
- 1 Band: "The Demo Band"
- 3 Users: Alice (leader), Bob, Carla
- 8 Songs with varied progress states
- Sample progress tracking and votes

To reload seed data:

```bash
python manage.py seed
```

## Deployment

### Render

1. Connect your GitHub repository
2. Set environment variables in Render dashboard
3. Set build command: `pip install -r requirements.txt`
4. Set start command: `gunicorn manage:app`

### Fly.io

1. Install flyctl: `curl -L https://fly.io/install.sh | sh`
2. Login: `fly auth login`
3. Deploy: `fly deploy`

### Environment Variables for Production

```bash
FLASK_ENV=production
FLASK_SECRET_KEY=<strong-random-secret>
DATABASE_URL=<your-production-database-url>
```

## Project Structure

```
bandmate/
├── app/                    # Main application package
│   ├── __init__.py        # Flask app factory
│   ├── models.py          # Database models
│   ├── auth.py            # Authentication logic
│   ├── main/              # Main routes and templates
│   └── api/               # API endpoints
├── migrations/             # Database migrations
├── tests/                  # Test suite
├── seed_data/             # Seed data and scripts
├── requirements.txt        # Python dependencies
├── manage.py              # CLI management script
└── README.md              # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests and linting
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
- Create an issue in the GitHub repository
- Check the documentation in the `/docs` folder
- Review the test files for usage examples
