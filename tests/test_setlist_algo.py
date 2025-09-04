import pytest
from datetime import datetime, date, timedelta

from app import db
from app.models import Song, SongProgress, Vote, SongStatus, ProgressStatus


class TestSetlistAlgorithm:
    """Test setlist generation algorithm functionality."""

    def test_basic_setlist_generation(self, app, test_band, test_user, test_song):
        """Test basic setlist generation with one song."""
        with app.app_context():
            # Create progress record
            progress = SongProgress(
                user_id=test_user.id,
                song_id=test_song.id,
                status=ProgressStatus.READY_FOR_REHEARSAL
            )
            db.session.add(progress)
            db.session.commit()

            # Test setlist generation via API
            # This would need to be tested via the actual route

            # For now, test the logic components
            assert test_song.readiness_score > 0
            assert test_song.status == SongStatus.ACTIVE

    def test_song_readiness_score_calculation(self, app, test_band, test_user):
        """Test song readiness score calculation."""
        with app.app_context():
            # Create multiple songs with different progress levels
            songs = []
            for i in range(3):
                song = Song(
                    title=f"Test Song {i}",
                    artist=f"Test Artist {i}",
                    status=SongStatus.ACTIVE,
                    duration_minutes=5,
                    band_id=test_band.id
                )
                songs.append(song)
                db.session.add(song)

            db.session.flush()

            # Create progress records with different statuses
            progress_statuses = [
                ProgressStatus.TO_LISTEN,
                ProgressStatus.IN_PRACTICE,
                ProgressStatus.READY_FOR_REHEARSAL,
                ProgressStatus.MASTERED
            ]

            for i, song in enumerate(songs):
                progress = SongProgress(
                    user_id=test_user.id,
                    song_id=song.id,
                    status=progress_statuses[i % len(progress_statuses)]
                )
                db.session.add(progress)

            db.session.commit()

            # Test readiness scores
            for i, song in enumerate(songs):
                expected_score = (i % len(progress_statuses)) + 1  # 1-4
                assert song.readiness_score == expected_score

    def test_song_status_enum(self, app):
        """Test song status enum values."""
        assert SongStatus.WISHLIST.value == 'wishlist'
        assert SongStatus.ACTIVE.value == 'active'

    def test_progress_status_enum(self, app):
        """Test progress status enum values."""
        assert ProgressStatus.TO_LISTEN.value == 'To Listen'
        assert ProgressStatus.IN_PRACTICE.value == 'In Practice'
        assert ProgressStatus.READY_FOR_REHEARSAL.value == 'Ready for Rehearsal'
        assert ProgressStatus.MASTERED.value == 'Mastered'

    def test_song_duration_validation(self, app, test_band):
        """Test song duration validation."""
        with app.app_context():
            # Test valid duration
            valid_song = Song(
                title="Valid Song",
                artist="Valid Artist",
                status=SongStatus.ACTIVE,
                duration_minutes=5,
                band_id=test_band.id
            )
            db.session.add(valid_song)
            db.session.commit()

            assert valid_song.duration_minutes == 5

            # Test None duration (optional field)
            optional_duration_song = Song(
                title="Optional Duration Song",
                artist="Optional Artist",
                status=SongStatus.WISHLIST,
                band_id=test_band.id
            )
            db.session.add(optional_duration_song)
            db.session.commit()

            assert optional_duration_song.duration_minutes is None

    def test_song_band_relationship(self, app, test_band):
        """Test song-band relationship."""
        with app.app_context():
            song = Song(
                title="Relationship Test Song",
                artist="Relationship Test Artist",
                status=SongStatus.ACTIVE,
                band_id=test_band.id
            )
            db.session.add(song)
            db.session.commit()

            assert song.band == test_band
            assert song in test_band.songs

    def test_song_progress_relationship(self, app, test_user, test_song):
        """Test song-progress relationship."""
        with app.app_context():
            progress = SongProgress(
                user_id=test_user.id,
                song_id=test_song.id,
                status=ProgressStatus.IN_PRACTICE
            )
            db.session.add(progress)
            db.session.commit()

            assert progress.song == test_song
            assert progress.user == test_user
            assert progress in test_song.progress
            assert progress in test_user.progress

    def test_song_vote_relationship(self, app, test_user, test_song):
        """Test song-vote relationship."""
        with app.app_context():
            vote = Vote(
                user_id=test_user.id,
                song_id=test_song.id
            )
            db.session.add(vote)
            db.session.commit()

            assert vote.song == test_song
            assert vote.user == test_user
            assert vote in test_song.votes
            assert vote in test_user.votes

    def test_song_creation_timestamp(self, app, test_band):
        """Test song creation timestamp."""
        with app.app_context():
            before_creation = datetime.utcnow()
            song = Song(
                title="Timestamp Test Song",
                artist="Timestamp Test Artist",
                status=SongStatus.WISHLIST,
                band_id=test_band.id
            )
            db.session.add(song)
            db.session.commit()
            after_creation = datetime.utcnow()

            assert before_creation <= song.created_at <= after_creation

    def test_song_last_rehearsed_date(self, app, test_band):
        """Test song last rehearsed date."""
        with app.app_context():
            rehearsal_date = date.today() - timedelta(days=7)
            song = Song(
                title="Rehearsal Date Test Song",
                artist="Rehearsal Date Test Artist",
                status=SongStatus.ACTIVE,
                duration_minutes=5,
                last_rehearsed_on=rehearsal_date,
                band_id=test_band.id
            )
            db.session.add(song)
            db.session.commit()

            assert song.last_rehearsed_on == rehearsal_date

    def test_song_status_transitions(self, app, test_band):
        """Test song status transitions."""
        with app.app_context():
            song = Song(
                title="Status Transition Song",
                artist="Status Transition Artist",
                status=SongStatus.WISHLIST,
                band_id=test_band.id
            )
            db.session.add(song)
            db.session.commit()

            # Test transition from wishlist to active
            assert song.status == SongStatus.WISHLIST
            song.status = SongStatus.ACTIVE
            db.session.commit()
            assert song.status == SongStatus.ACTIVE

    def test_song_progress_updates(self, app, test_user, test_song):
        """Test song progress updates."""
        with app.app_context():
            progress = SongProgress(
                user_id=test_user.id,
                song_id=test_song.id,
                status=ProgressStatus.TO_LISTEN
            )
            db.session.add(progress)
            db.session.commit()

            # Test progress status update
            assert progress.status == ProgressStatus.TO_LISTEN
            progress.status = ProgressStatus.IN_PRACTICE
            db.session.commit()
            assert progress.status == ProgressStatus.IN_PRACTICE

            # Test that updated_at is automatically updated
            original_updated = progress.updated_at
            progress.status = ProgressStatus.READY_FOR_REHEARSAL
            db.session.commit()
            assert progress.updated_at > original_updated
