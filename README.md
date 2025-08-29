# BandMate 🎸

**BandMate** is a web application that eliminates the chaos before band rehearsals by providing a centralized dashboard for tracking song progress and generating optimized practice setlists.

## 🎯 The Problem It Solves

**"Who knows what?"** - Stop endless WhatsApp messages asking "Have you practiced the new song?" The dashboard shows everyone's progress at a glance.

**"What should we practice today?"** - Instead of wasting 20 minutes deciding, see which songs have the highest "readiness score" and focus on those.

**"What's the next song?"** - Centralized management of new ideas. No more lost YouTube links or forgotten proposals in chat.

## ✨ What BandMate Does

### 🎵 **Multi-Band Management**
BandMate supports musicians who play in multiple bands. Each band has its own workspace where members can track songs, progress, and generate setlists. The invitation system allows band leaders to invite new members with secure codes, while users can seamlessly switch between bands they belong to.

### 📊 **Smart Progress Tracking**
The core of BandMate is its visual progress dashboard. Each song displays a table where every band member can update their learning status:
- **⚪️ To Listen**: Haven't started learning yet
- **🟡 In Practice**: Currently working on parts, chords, or lyrics
- **🟢 Ready for Rehearsal**: Can play the song start-to-finish with the band
- **🔵 Mastered**: Performance-ready, knows it by heart

The system calculates a "readiness score" showing how many members are ready (e.g., "4/5 Ready"), helping bands identify which songs to focus on during rehearsals.

### 🎼 **Intelligent Setlist Generation**
BandMate's setlist generator acts as a virtual musical director. It creates optimized practice schedules by:
- **Balancing Learning vs. Maintenance**: Allocates time between new songs and keeping mastered ones fresh
- **Smart Time Management**: Clusters sessions into 30-minute intervals with configurable breaks
- **Progress-Based Selection**: Prioritizes songs where most members are ready, maximizing rehearsal efficiency
- **Customizable Buffers**: Adjusts time allocation based on whether songs are new (20% buffer) or mastered (10% buffer)

### 🎧 **Spotify Integration**
Adding new songs is seamless with Spotify integration. Search for any track and BandMate automatically fills in:
- Song title and artist
- Album artwork
- Duration and metadata
- Direct links to Spotify

### 🗳️ **Democratic Song Selection**
The wishlist system lets every band member contribute:
- **Propose Songs**: Suggest new tracks with optional notes
- **Vote System**: Members can vote on proposed songs
- **Band Approval**: Leaders can promote popular songs from wishlist to active repertoire

## 🏗️ Technical Stack

- **Backend**: Python 3.11+, Flask
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: Google OAuth via Flask-Dance
- **Frontend**: Jinja2 templates + Alpine.js
- **Styling**: Tailwind CSS
- **External APIs**: Spotify Web API
- **Testing**: pytest with comprehensive test coverage

## 🚀 Quick Start

1. **Setup**: Clone the repository and install dependencies
2. **Configure**: Set up Google OAuth and optional Spotify API credentials
3. **Create Band**: Start your first band or join existing ones
4. **Add Songs**: Use Spotify search or manual entry
5. **Track Progress**: Update your learning status for each song
6. **Generate Setlists**: Create optimized practice schedules

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

**BandMate** - Because great music happens when everyone knows what they're doing. 🎸✨
