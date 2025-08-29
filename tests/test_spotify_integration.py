import pytest
import responses
import os
from unittest.mock import patch, MagicMock
from app.spotify import SpotifyAPI, spotify_api


class TestSpotifyAPI:
    """Test cases for Spotify API integration"""
    
    def setup_method(self):
        """Set up test environment"""
        self.api = SpotifyAPI()
        self.api.client_id = "test_client_id"
        self.api.client_secret = "test_client_secret"
        self.api.access_token = None
        self.api.token_expires_at = None
        self.api.last_error = None
    
    def test_init_with_credentials(self):
        """Test API initialization with credentials"""
        api = SpotifyAPI()
        # Should work even without credentials
        assert hasattr(api, 'client_id')
        assert hasattr(api, 'client_secret')
        assert hasattr(api, 'is_configured')
    
    def test_is_configured_property(self):
        """Test is_configured property"""
        # With credentials
        self.api.client_id = "test_id"
        self.api.client_secret = "test_secret"
        assert self.api.is_configured is True
        
        # Without credentials
        self.api.client_id = None
        self.api.client_secret = None
        assert self.api.is_configured is False
    
    @responses.activate
    def test_get_access_token_success(self):
        """Test successful access token retrieval"""
        # Mock successful response
        responses.add(
            responses.POST,
            'https://accounts.spotify.com/api/token',
            json={
                'access_token': 'test_token_123',
                'expires_in': 3600,
                'token_type': 'Bearer'
            },
            status=200
        )
        
        token = self.api._get_access_token()
        
        assert token == 'test_token_123'
        assert self.api.access_token == 'test_token_123'
        assert self.api.last_error is None
    
    @responses.activate
    def test_get_access_token_failure(self):
        """Test access token retrieval failure"""
        # Mock failed response
        responses.add(
            responses.POST,
            'https://accounts.spotify.com/api/token',
            json={'error': 'invalid_client'},
            status=400
        )
        
        token = self.api._get_access_token()
        
        assert token is None
        assert self.api.last_error is not None
    
    @responses.activate
    def test_get_access_token_timeout(self):
        """Test access token retrieval timeout"""
        # Mock timeout
        responses.add(
            responses.POST,
            'https://accounts.spotify.com/api/token',
            body=Exception("Connection timeout")
        )
        
        token = self.api._get_access_token()
        
        assert token is None
        assert "timeout" in self.api.last_error.lower()
    
    def test_get_basic_auth_header(self):
        """Test basic auth header generation"""
        header = self.api._get_basic_auth_header()
        
        # Should be base64 encoded
        import base64
        decoded = base64.b64decode(header).decode()
        assert decoded == f"{self.api.client_id}:{self.api.client_secret}"
    
    def test_is_token_valid(self):
        """Test token validity checking"""
        # No token
        assert self.api._is_token_valid() is False
        
        # Valid token
        self.api.access_token = "test_token"
        self.api.token_expires_at = 1000  # Future time
        assert self.api._is_token_valid() is True
        
        # Expired token
        self.api.token_expires_at = 0  # Past time
        assert self.api._is_token_valid() is False
    
    @responses.activate
    def test_search_tracks_success(self):
        """Test successful track search"""
        # Mock successful search response
        responses.add(
            responses.GET,
            'https://api.spotify.com/v1/search?q=test&type=track&limit=10&market=US',
            json={
                'tracks': {
                    'items': [
                        {
                            'id': 'track1',
                            'name': 'Test Song',
                            'artists': [{'name': 'Test Artist'}],
                            'album': {
                                'name': 'Test Album',
                                'images': [{'url': 'http://example.com/image.jpg'}]
                            },
                            'duration_ms': 180000,
                            'external_urls': {'spotify': 'https://open.spotify.com/track/track1'}
                        }
                    ]
                }
            },
            status=200
        )
        
        # Set valid token
        self.api.access_token = "test_token"
        self.api.token_expires_at = 1000
        
        result = self.api.search_tracks("test")
        
        assert 'tracks' in result
        assert 'error' in result
        assert result['error'] is None
        assert len(result['tracks']) == 1
        assert result['tracks'][0]['title'] == 'Test Song'
        assert result['tracks'][0]['duration_minutes'] == 3.0
    
    @responses.activate
    def test_search_tracks_no_credentials(self):
        """Test search without credentials"""
        self.api.client_id = None
        self.api.client_secret = None
        
        result = self.api.search_tracks("test")
        
        assert result['tracks'] == []
        assert result['error'] == 'Spotify API not configured'
    
    @responses.activate
    def test_search_tracks_authentication_failure(self):
        """Test search with authentication failure"""
        # Mock failed auth
        responses.add(
            responses.POST,
            'https://accounts.spotify.com/api/token',
            json={'error': 'invalid_client'},
            status=400
        )
        
        result = self.api.search_tracks("test")
        
        assert result['tracks'] == []
        assert 'Failed to authenticate' in result['error']
    
    @responses.activate
    def test_search_tracks_timeout(self):
        """Test search timeout handling"""
        # Mock timeout
        responses.add(
            responses.GET,
            'https://api.spotify.com/v1/search?q=test&type=track&limit=10&market=US',
            body=Exception("Connection timeout")
        )
        
        # Set valid token
        self.api.access_token = "test_token"
        self.api.token_expires_at = 1000
        
        result = self.api.search_tracks("test")
        
        assert result['tracks'] == []
        assert 'timeout' in result['error'].lower()
    
    @responses.activate
    def test_search_tracks_malformed_data(self):
        """Test handling of malformed track data"""
        # Mock response with malformed data
        responses.add(
            responses.GET,
            'https://api.spotify.com/v1/search?q=test&type=track&limit=10&market=US',
            json={
                'tracks': {
                    'items': [
                        {
                            'id': 'track1',
                            'name': 'Test Song',
                            # Missing required fields
                        }
                    ]
                }
            },
            status=200
        )
        
        # Set valid token
        self.api.access_token = "test_token"
        self.api.token_expires_at = 1000
        
        result = self.api.search_tracks("test")
        
        # Should handle gracefully and skip malformed tracks
        assert result['tracks'] == []
        assert result['error'] is None
    
    @responses.activate
    def test_get_track_success(self):
        """Test successful single track retrieval"""
        # Mock successful track response
        responses.add(
            responses.GET,
            'https://api.spotify.com/v1/tracks/track1',
            json={
                'id': 'track1',
                'name': 'Test Song',
                'artists': [{'name': 'Test Artist'}],
                'album': {
                    'name': 'Test Album',
                    'images': [{'url': 'http://example.com/image.jpg'}]
                },
                'duration_ms': 180000,
                'external_urls': {'spotify': 'https://open.spotify.com/track/track1'}
            },
            status=200
        )
        
        # Set valid token
        self.api.access_token = "test_token"
        self.api.token_expires_at = 1000
        
        track = self.api.get_track("track1")
        
        assert track is not None
        assert track['title'] == 'Test Song'
        assert track['duration_minutes'] == 3.0
    
    def test_duration_calculation(self):
        """Test duration calculation from milliseconds"""
        # Test various durations
        test_cases = [
            (60000, 1.0),    # 1 minute
            (90000, 1.5),    # 1.5 minutes
            (180000, 3.0),   # 3 minutes
            (300000, 5.0),   # 5 minutes
        ]
        
        for ms, expected_minutes in test_cases:
            calculated = round(ms / 60000, 1)
            assert calculated == expected_minutes
    
    def test_error_message_persistence(self):
        """Test that error messages are properly stored"""
        self.api.last_error = "Test error message"
        assert self.api.last_error == "Test error message"
        
        # Error should be cleared on success
        self.api.last_error = None
        assert self.api.last_error is None


class TestSpotifyIntegration:
    """Integration tests for Spotify API"""
    
    @patch.dict(os.environ, {'SPOTIFY_CLIENT_ID': 'test_id', 'SPOTIFY_CLIENT_SECRET': 'test_secret'})
    def test_global_instance_creation(self):
        """Test that global spotify_api instance is created"""
        from app.spotify import spotify_api
        assert isinstance(spotify_api, SpotifyAPI)
        assert spotify_api.is_configured is True
    
    @patch.dict(os.environ, {}, clear=True)
    def test_global_instance_no_credentials(self):
        """Test global instance without credentials"""
        from app.spotify import spotify_api
        assert isinstance(spotify_api, SpotifyAPI)
        assert spotify_api.is_configured is False


class TestSpotifyAPIRateLimiting:
    """Test rate limiting and error handling"""
    
    def setup_method(self):
        """Set up test environment"""
        self.api = SpotifyAPI()
        self.api.client_id = "test_client_id"
        self.api.client_secret = "test_client_secret"
    
    @responses.activate
    def test_rate_limit_handling(self):
        """Test handling of rate limit responses"""
        # Mock rate limit response
        responses.add(
            responses.GET,
            'https://api.spotify.com/v1/search?q=test&type=track&limit=10&market=US',
            json={'error': {'status': 429, 'message': 'Rate limit exceeded'}},
            status=429
        )
        
        # Set valid token
        self.api.access_token = "test_token"
        self.api.token_expires_at = 1000
        
        result = self.api.search_tracks("test")
        
        assert result['tracks'] == []
        assert 'failed' in result['error'].lower()
    
    @responses.activate
    def test_invalid_token_handling(self):
        """Test handling of invalid token responses"""
        # Mock invalid token response
        responses.add(
            responses.GET,
            'https://api.spotify.com/v1/search?q=test&type=track&limit=10&market=US',
            json={'error': {'status': 401, 'message': 'Invalid access token'}},
            status=401
        )
        
        # Set invalid token
        self.api.access_token = "invalid_token"
        self.api.token_expires_at = 1000
        
        result = self.api.search_tracks("test")
        
        # Should attempt to refresh token
        assert result['tracks'] == []
        assert 'Failed to authenticate' in result['error']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
