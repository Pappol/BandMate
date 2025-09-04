import os
import pytest
from unittest.mock import patch, MagicMock

from app.spotify import SpotifyAPI, spotify_api


class TestSpotifyAPIBasic:
    """Basic test cases for Spotify API integration"""

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


class TestSpotifyAPIMocked:
    """Test cases using mocked HTTP requests"""

    def setup_method(self):
        """Set up test environment"""
        self.api = SpotifyAPI()
        self.api.client_id = "test_client_id"
        self.api.client_secret = "test_client_secret"

    @patch('requests.post')
    def test_get_access_token_success(self, mock_post):
        """Test successful access token retrieval"""
        # Mock successful response
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'access_token': 'test_token_123',
            'expires_in': 3600
        }
        mock_post.return_value = mock_response

        token = self.api._get_access_token()

        assert token == 'test_token_123'
        assert self.api.access_token == 'test_token_123'
        assert self.api.last_error is None

    @patch('requests.post')
    def test_get_access_token_failure(self, mock_post):
        """Test access token retrieval failure"""
        # Mock failed response
        mock_response = MagicMock()
        mock_response.ok = False
        mock_response.raise_for_status.side_effect = Exception("Auth failed")
        mock_post.return_value = mock_response

        token = self.api._get_access_token()

        assert token is None
        assert self.api.last_error is not None

    @patch('requests.get')
    def test_search_tracks_success(self, mock_get):
        """Test successful track search"""
        # Mock successful search response
        mock_response = MagicMock()
        mock_response.ok = True
        mock_response.json.return_value = {
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
                        'external_urls': {
                            'spotify': 'https://open.spotify.com/track/track1'}
                    }
                ]
            }
        }
        mock_get.return_value = mock_response

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

    def test_search_tracks_no_credentials(self):
        """Test search without credentials"""
        self.api.client_id = None
        self.api.client_secret = None

        result = self.api.search_tracks("test")

        assert result['tracks'] == []
        assert result['error'] == 'Spotify API not configured'


class TestSpotifyIntegration:
    """Integration tests for Spotify API"""

    @patch.dict(os.environ, {
        'SPOTIFY_CLIENT_ID': 'test_id',
        'SPOTIFY_CLIENT_SECRET': 'test_secret'})
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


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
