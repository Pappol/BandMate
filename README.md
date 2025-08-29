# BandMate 🎸

**BandMate** is a web application that eliminates the chaos before band rehearsals by providing a centralized dashboard for tracking song progress and generating optimized practice setlists.

## 🎯 The Problem It Solves

**"Who knows what?"** - Stop endless WhatsApp messages asking "Have you practiced the new song?" The dashboard shows everyone's progress at a glance.

**"What should we practice today?"** - Instead of wasting 20 minutes deciding, see which songs have the highest "readiness score" and focus on those.

**"What's the next song?"** - Centralized management of new ideas. No more lost YouTube links or forgotten proposals in chat.

## ✨ Key Features

### 🎵 **Multi-Band Support**
- Join multiple bands with different roles (Leader/Member)
- Seamlessly switch between bands
- Invitation system with secure codes

### 📊 **Smart Progress Tracking**
- **Dashboard**: Visual progress table showing each member's status for every song
- **Progress States**: 
  - ⚪️ To Listen (not started)
  - 🟡 In Practice (learning parts)
  - 🟢 Ready for Rehearsal (can play with band)
  - 🔵 Mastered (performance ready)
- **Readiness Score**: Shows how many members are ready (e.g., "4/5 Ready")

### 🎼 **Advanced Setlist Generator**
- **Intelligent Planning**: Balances learning new songs vs. maintaining mastered ones
- **Customizable Buffers**: Configurable time buffers for new vs. learned songs
- **Smart Scheduling**: Clusters time into 30-minute intervals
- **Break Management**: Automatic breaks for sessions over 90 minutes
- **Learning Ratio Control**: Adjust focus between new material and maintenance

### 🎧 **Spotify Integration**
- **Auto-complete**: Search songs and auto-fill metadata
- **Rich Content**: Album artwork and track information
- **Seamless Workflow**: Propose songs directly from Spotify search

### 🗳️ **Democratic Song Management**
- **Wishlist System**: Propose new songs with voting
- **Band Approval**: Leaders can promote songs from wishlist to active repertoire

## 🏗️ Technical Stack

- **Backend**: Python 3.11+, Flask
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: Google OAuth via Flask-Dance
- **Frontend**: Jinja2 templates + Alpine.js
- **Styling**: Tailwind CSS
- **External APIs**: Spotify Web API
- **Testing**: pytest with comprehensive test coverage

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Google OAuth credentials
- Spotify API credentials (optional)

### Setup
```bash
# Clone and setup
git clone <your-repo-url>
cd bandmate
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Environment configuration
cp .env.example .env
# Edit .env with your credentials

# Database setup
export FLASK_APP=manage.py
flask db upgrade
python manage.py seed

# Run
flask run
```

## 🔧 Configuration

### Environment Variables
```bash
FLASK_SECRET_KEY=your-secret-key
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
SPOTIFY_CLIENT_ID=your-spotify-client-id
SPOTIFY_CLIENT_SECRET=your-spotify-client-secret
```

### Setlist Generation Settings
- **Buffer Percentages**: Customize time allocation for new vs. learned songs
- **Break Management**: Configure break duration and thresholds
- **Time Clustering**: Adjust session time intervals

## 📱 Usage

1. **Create/Join Band**: Start a new band or join existing ones
2. **Add Songs**: Use Spotify search or manual entry
3. **Track Progress**: Update your status for each song
4. **Generate Setlists**: Create optimized practice schedules
5. **Vote & Propose**: Contribute to the band's song selection

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run multi-band specific tests
python run_multi_band_tests.py
```

## 🚀 Deployment

### Render
- Connect GitHub repository
- Set environment variables
- Build: `pip install -r requirements.txt`
- Start: `gunicorn manage:app`

### Docker
```bash
docker-compose up --build
```

## 📚 Documentation

- **API Reference**: See `/docs` folder
- **Multi-Band Guide**: `MULTI_BAND_README.md`
- **Spotify Integration**: `SPOTIFY_INTEGRATION_README.md`
- **Setlist Algorithm**: Detailed in `DOCUMENTAZIONE.md`

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes and add tests
4. Submit a pull request

## 📄 License

MIT License - see LICENSE file for details.

---

**BandMate** transforms band coordination from chaotic messaging to structured, productive practice sessions. 🎸✨
