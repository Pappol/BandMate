import requests
import os
from flask import current_app
import logging

logger = logging.getLogger(__name__)

class SpotifyAPI:
    """Spotify API client for searching tracks and getting metadata"""
    
    def __init__(self):
        self.client_id = os.getenv('SPOTIFY_CLIENT_ID')
        self.client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        self.base_url = 'https://api.spotify.com/v1'
        self.access_token = None
        self.token_expires_at = None
        self.last_error = None
        self.is_configured = bool(self.client_id and self.client_secret)
    
    def _get_access_token(self):
        """Get a new access token using client credentials flow"""
        if not self.is_configured:
            self.last_error = "Spotify credentials not configured"
            logger.error("Spotify credentials not configured")
            return None
        
        try:
            auth_url = 'https://accounts.spotify.com/api/token'
            auth_data = {
                'grant_type': 'client_credentials'
            }
            auth_headers = {
                'Authorization': f'Basic {self._get_basic_auth_header()}'
            }
            
            response = requests.post(auth_url, data=auth_data, headers=auth_headers, timeout=10)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data['access_token']
            # Token expires in 1 hour, set expiry 5 minutes earlier for safety
            self.token_expires_at = token_data['expires_in'] - 300
            self.last_error = None
            
            logger.info("Successfully obtained Spotify access token")
            return self.access_token
            
        except requests.exceptions.Timeout:
            self.last_error = "Spotify authentication timeout"
            logger.error("Spotify authentication timeout")
            return None
        except requests.exceptions.RequestException as e:
            self.last_error = f"Spotify authentication request failed: {e}"
            logger.error(f"Failed to get Spotify access token: {e}")
            return None
        except KeyError as e:
            self.last_error = f"Invalid Spotify authentication response: {e}"
            logger.error(f"Invalid response from Spotify auth: {e}")
            return None
        except Exception as e:
            self.last_error = f"Unexpected authentication error: {e}"
            logger.error(f"Unexpected error in Spotify authentication: {e}")
            return None
    
    def _get_basic_auth_header(self):
        """Create basic auth header from client credentials"""
        import base64
        credentials = f"{self.client_id}:{self.client_secret}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return encoded
    
    def _is_token_valid(self):
        """Check if current access token is still valid"""
        return self.access_token and self.token_expires_at and self.token_expires_at > 0
    
    def search_tracks(self, query, limit=10):
        """
        Search for tracks using Spotify API
        
        Args:
            query (str): Search query (e.g., "Everlong Foo Fighters")
            limit (int): Maximum number of results to return
            
        Returns:
            dict: Dictionary with 'tracks' list and 'error' if any
        """
        if not self.is_configured:
            return {'tracks': [], 'error': 'Spotify API not configured'}
        
        if not self._is_token_valid():
            if not self._get_access_token():
                return {'tracks': [], 'error': self.last_error or 'Failed to authenticate with Spotify'}
        
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}'
            }
            
            params = {
                'q': query,
                'type': 'track',
                'limit': limit,
                'market': 'US'  # You can make this configurable
            }
            
            response = requests.get(
                f"{self.base_url}/search",
                headers=headers,
                params=params,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            tracks = data.get('tracks', {}).get('items', [])
            
            # Format the response for our app
            formatted_tracks = []
            for track in tracks:
                try:
                    # Get the first image (usually the largest)
                    album_art = track['album']['images'][0]['url'] if track['album']['images'] else None
                    
                    formatted_track = {
                        'id': track['id'],
                        'title': track['name'],
                        'artist': track['artists'][0]['name'] if track['artists'] else 'Unknown Artist',
                        'album': track['album']['name'],
                        'duration_ms': track['duration_ms'],
                        'duration_seconds': int(track['duration_ms'] / 1000),
                        'album_art_url': album_art,
                        'spotify_url': track['external_urls']['spotify'],
                        'preview_url': track.get('preview_url')
                    }
                    formatted_tracks.append(formatted_track)
                except (KeyError, IndexError) as e:
                    logger.warning(f"Skipping malformed track data: {e}")
                    continue
            
            self.last_error = None
            logger.info(f"Successfully searched Spotify for '{query}', found {len(formatted_tracks)} tracks")
            return {'tracks': formatted_tracks, 'error': None}
            
        except requests.exceptions.Timeout:
            self.last_error = "Spotify search timeout"
            logger.error("Spotify search timeout")
            return {'tracks': [], 'error': 'Search timeout - please try again'}
        except requests.exceptions.RequestException as e:
            self.last_error = f"Spotify search request failed: {e}"
            logger.error(f"Spotify API request failed: {e}")
            return {'tracks': [], 'error': 'Search request failed - please try again'}
        except KeyError as e:
            self.last_error = f"Invalid Spotify search response: {e}"
            logger.error(f"Unexpected response format from Spotify: {e}")
            return {'tracks': [], 'error': 'Invalid response from Spotify'}
        except Exception as e:
            self.last_error = f"Unexpected search error: {e}"
            logger.error(f"Unexpected error in Spotify search: {e}")
            return {'tracks': [], 'error': 'Unexpected error occurred'}
    
    def get_track(self, track_id):
        """
        Get detailed information about a specific track
        
        Args:
            track_id (str): Spotify track ID
            
        Returns:
            dict: Track information or None if not found
        """
        if not self._is_token_valid():
            if not self._get_access_token():
                return None
        
        try:
            headers = {
                'Authorization': f'Bearer {self.access_token}'
            }
            
            response = requests.get(
                f"{self.base_url}/tracks/{track_id}",
                headers=headers
            )
            response.raise_for_status()
            
            track = response.json()
            
            # Format the response
            album_art = track['album']['images'][0]['url'] if track['album']['images'] else None
            
            formatted_track = {
                'id': track['id'],
                'title': track['name'],
                'artist': track['artists'][0]['name'] if track['artists'] else 'Unknown Artist',
                'album': track['album']['name'],
                'duration_ms': track['duration_ms'],
                'duration_seconds': int(track['duration_ms'] / 1000),
                'album_art_url': album_art,
                'spotify_url': track['external_urls']['spotify'],
                'preview_url': track.get('preview_url')
            }
            
            return formatted_track
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get track {track_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error getting track {track_id}: {e}")
            return None

# Global instance
spotify_api = SpotifyAPI()
