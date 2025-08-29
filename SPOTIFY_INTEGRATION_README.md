# 🎵 Spotify API Integration - BandMate

This document explains how to set up and use the Spotify API integration in your BandMate application.

## 🚀 Overview

The Spotify API integration enhances your BandMate app by providing:
- **Automatic song search** instead of manual entry
- **Rich metadata** including album art and duration
- **Professional appearance** with visual elements
- **Accurate data** from Spotify's official catalog

## ⚙️ Setup Instructions

### 1. Create Spotify Developer Account

1. Go to [Spotify for Developers](https://developer.spotify.com/)
2. Log in with your Spotify account
3. Click "Create App"
4. Fill in the app details:
   - **App name**: `BandMate` (or your preferred name)
   - **App description**: `Music band management application`
   - **Website**: `http://localhost:5000` (for development)
   - **Redirect URI**: Leave empty (we use Client Credentials flow)
   - **Category**: Choose "Other"

### 2. Get Your Credentials

After creating the app, you'll see:
- **Client ID**: A long string of letters and numbers
- **Client Secret**: Click "Show Client Secret" to reveal it

### 3. Configure Environment Variables

Add these to your `.env` file:

```bash
# Spotify API Credentials
SPOTIFY_CLIENT_ID=your-client-id-here
SPOTIFY_CLIENT_SECRET=your-client-secret-here
```

### 4. Run Database Migration

The new Spotify fields need to be added to your database:

```bash
python migrate_spotify.py
```

### 5. Restart Your Application

```bash
make dev
# or
python manage.py run
```

## 🎯 How It Works

### Authentication Flow
- **Client Credentials Flow**: Your backend authenticates with Spotify using your app credentials
- **No User Login Required**: Users don't need Spotify accounts
- **Automatic Token Management**: Tokens are refreshed automatically

### Search Process
1. User types in the search box (e.g., "Everlong Foo Fighters")
2. App sends request to Spotify API via your backend
3. Spotify returns matching tracks with metadata
4. User selects a track from the results
5. Form is automatically filled with song details
6. Song is saved with Spotify metadata

### Data Stored
- `spotify_track_id`: Unique identifier for the track
- `album_art_url`: URL to the album cover image
- `duration_minutes`: Accurate song duration in minutes
- `title` and `artist`: Official names from Spotify

## 🎨 User Interface

### Propose Song Page
- **Spotify Search Section**: Green box at the top with search functionality
- **Real-time Search**: Results appear as you type (with debouncing)
- **Visual Results**: Album art, song title, artist, album, and duration
- **Auto-fill**: Click a result to populate the form

### Wishlist & Dashboard
- **Album Art Display**: Shows actual album covers when available
- **Fallback Icons**: Musical note icons for songs without Spotify data
- **Enhanced Layout**: Better visual hierarchy with images

## 🔧 Technical Details

### API Endpoints
- `GET /api/spotify/search?q=<query>`: Search for tracks
- **Rate Limits**: Spotify allows 25 requests per second

### Error Handling
- **Graceful Degradation**: App works without Spotify credentials
- **Fallback UI**: Default icons when album art is unavailable
- **User Feedback**: Clear error messages for search failures

### Security
- **No User Tokens**: Only your app credentials are stored
- **Server-side Requests**: All API calls go through your backend
- **No Sensitive Data**: Only public track information is accessed

## 🐛 Troubleshooting

### Common Issues

#### "Spotify credentials not configured"
- Check your `.env` file has the correct variable names
- Ensure `SPOTIFY_CLIENT_ID` and `SPOTIFY_CLIENT_SECRET` are set
- Restart your application after adding credentials

#### "Failed to search Spotify"
- Verify your Spotify app is active in the developer dashboard
- Check that your credentials are correct
- Ensure your app hasn't exceeded rate limits

#### Album art not displaying
- Some tracks may not have album art available
- Check browser console for image loading errors
- Fallback icons should appear automatically

#### Search not working
- Ensure you have an active internet connection
- Check that your Flask app can make outbound HTTP requests
- Verify the `/api/spotify/search` endpoint is accessible

### Debug Mode

Enable debug logging in your Flask app to see detailed Spotify API interactions:

```python
# In your Flask app
app.logger.setLevel(logging.DEBUG)
```

## 📱 Testing the Integration

### 1. Basic Search
1. Go to "Propose Song" page
2. Type "Bohemian Rhapsody" in the Spotify search box
3. Verify results appear with album art
4. Click a result and check form auto-fill

### 2. Album Art Display
1. Add a song via Spotify search
2. Go to Wishlist or Dashboard
3. Verify album art is displayed
4. Check fallback icons for songs without Spotify data

### 3. Duration Accuracy
1. Add a song via Spotify search
2. Check that duration is automatically filled
3. Verify the duration appears in setlist generation

## 🚀 Production Considerations

### Environment Variables
- Use production Spotify app credentials
- Store credentials securely (not in version control)
- Consider using a secrets management service

### Rate Limiting
- Monitor API usage in Spotify developer dashboard
- Implement caching for frequently searched terms
- Consider implementing request queuing for high traffic

### Error Monitoring
- Log Spotify API errors for monitoring
- Set up alerts for authentication failures
- Monitor response times and success rates

## 📚 API Reference

### Spotify Search Response Format
```json
{
  "tracks": [
    {
      "id": "spotify-track-id",
      "title": "Song Title",
      "artist": "Artist Name",
      "album": "Album Name",
      "duration_ms": 180000,
      "duration_minutes": 3.0,
      "album_art_url": "https://...",
      "spotify_url": "https://open.spotify.com/track/...",
      "preview_url": "https://..."
    }
  ]
}
```

### Database Schema Changes
```sql
ALTER TABLE songs ADD COLUMN spotify_track_id TEXT;
ALTER TABLE songs ADD COLUMN album_art_url TEXT;
CREATE INDEX ix_songs_spotify_track_id ON songs(spotify_track_id);
```

## 🤝 Support

If you encounter issues with the Spotify integration:

1. Check this documentation first
2. Verify your credentials and configuration
3. Check the Flask application logs
4. Ensure your Spotify app is active and not rate-limited

## 📄 License

This integration uses the Spotify Web API under their [Developer Terms of Service](https://developer.spotify.com/documentation/web-api/).

---

*Last updated: August 2025*
*BandMate version: 0.1.0*
