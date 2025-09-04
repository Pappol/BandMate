import pytest

from app import db
from app.models import SongProgress, ProgressStatus, SetlistConfig


class TestAdvancedSetlistFeatures:
    """Test advanced setlist features including buffer percentages and time
    clustering."""

    def test_setlist_config_creation(self, app, test_band):
        """Test that SetlistConfig is automatically created for bands."""
        with app.app_context():
            # Get the band's config
            config = test_band.get_setlist_config()

            assert config is not None
            assert config.band_id == test_band.id
            assert config.new_songs_buffer_percent == 20.0
            assert config.learned_songs_buffer_percent == 10.0
            assert config.break_time_minutes == 10
            assert config.break_threshold_minutes == 90
            assert config.min_session_minutes == 30
            assert config.max_session_minutes == 240
            assert config.time_cluster_minutes == 30

    def test_time_clustering(self, app, test_band):
        """Test time clustering to nearest 30-minute interval."""
        with app.app_context():
            config = test_band.get_setlist_config()

            # Test clustering
            # Rounds to nearest 30-min interval
            assert config.get_clustered_duration(45) == 60
            assert config.get_clustered_duration(60) == 60  # Exact interval
            assert config.get_clustered_duration(75) == 60  # Rounds down
            assert config.get_clustered_duration(90) == 90  # Exact interval
            assert config.get_clustered_duration(105) == 120  # Rounds up
            assert config.get_clustered_duration(300) == 240  # Above maximum

    def test_buffer_calculation(self, app, test_band):
        """Test buffer percentage calculations for songs."""
        with app.app_context():
            config = test_band.get_setlist_config()

            # Test new songs buffer (20%)
            # 3 minutes
            new_song_duration = config.calculate_song_duration_with_buffer(
                180, is_learned=False)
            assert abs(new_song_duration - 3.6) < 0.001  # 3 * 1.2 = 3.6

            # Test learned songs buffer (10%)
            # 3 minutes
            learned_song_duration = config.calculate_song_duration_with_buffer(
                180, is_learned=True)
            assert abs(learned_song_duration - 3.3) < 0.001  # 3 * 1.1 = 3.3

    def test_break_configuration(self, app, test_band):
        """Test break threshold logic."""
        with app.app_context():
            config = test_band.get_setlist_config()

            # Test break needed
            assert config.is_break_needed(90) is True
            assert config.is_break_needed(120) is True

            # Test break not needed
            assert config.is_break_needed(60) is False
            assert config.is_break_needed(45) is False

    def test_setlist_config_update(self, app, test_band):
        """Test updating setlist configuration."""
        with app.app_context():
            # Create config first
            config = test_band.get_setlist_config()
            assert config is not None

            # Update configuration
            config.new_songs_buffer_percent = 25.0
            config.learned_songs_buffer_percent = 15.0
            config.break_time_minutes = 15
            config.break_threshold_minutes = 120

            db.session.commit()

            # Verify changes
            updated_config = SetlistConfig.query.filter_by(
                band_id=test_band.id).first()
            assert updated_config.new_songs_buffer_percent == 25.0
            assert updated_config.learned_songs_buffer_percent == 15.0
            assert updated_config.break_time_minutes == 15
            assert updated_config.break_threshold_minutes == 120

    def test_buffer_in_setlist_generation(self, app, test_band, test_user, test_song):
        """Test that buffer percentages are applied during setlist generation."""
        with app.app_context():
            # Create progress record for the song
            progress = SongProgress(
                user_id=test_user.id,
                song_id=test_song.id,
                status=ProgressStatus.IN_PRACTICE  # This makes it a learning song
            )
            db.session.add(progress)
            db.session.commit()

            # Get the band's config
            config = test_band.get_setlist_config()

            # Calculate duration with buffer
            original_duration = test_song.duration_seconds / 60  # in minutes
            buffered_duration = config.calculate_song_duration_with_buffer(
                test_song.duration_seconds, is_learned=False
            )

            # Verify buffer is applied
            assert buffered_duration > original_duration
            assert (buffered_duration ==
                   original_duration * (1 + config.new_songs_buffer_percent / 100))
