#!/usr/bin/env python3
"""
Database Performance Tests for BandMate
Tests query performance, indexing, and scalability
"""

import pytest
import time
import os
from datetime import datetime, timedelta
from sqlalchemy import text, func

from app import create_app, db
from app.models import (
    User, Band, Song, SongProgress, Vote, Invitation, SetlistConfig,
    SongStatus, ProgressStatus, InvitationStatus, UserRole
)


@pytest.fixture
def app():
    """Create test application with PostgreSQL database"""
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['DATABASE_URL'] = 'postgresql://test_user:test_pass@localhost:5432/bandmate_test'
    
    app = create_app('testing')
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def large_dataset(app):
    """Create a large dataset for performance testing"""
    with app.app_context():
        # Create 10 bands
        bands = []
        for i in range(10):
            band = Band(
                name=f"Band {i}",
                emoji=f"🎵{i}",
                color=f"#{i:06x}",
                letter=chr(65 + i),  # A, B, C, etc.
                allow_member_invites=True
            )
            db.session.add(band)
            bands.append(band)
        
        db.session.commit()
        
        # Create 100 users
        users = []
        for i in range(100):
            user = User(
                id=f"perf_user_{i}",
                name=f"User {i}",
                email=f"user{i}@test.com"
            )
            db.session.add(user)
            users.append(user)
        
        db.session.commit()
        
        # Create band memberships (each user in 2-3 bands)
        for i, user in enumerate(users):
            # Add user to 2-3 random bands
            import random
            band_count = random.randint(2, 3)
            selected_bands = random.sample(bands, band_count)
            
            for j, band in enumerate(selected_bands):
                role = UserRole.LEADER if j == 0 else UserRole.MEMBER
                band.add_member(user, role)
        
        # Create 500 songs across all bands
        songs = []
        for i in range(500):
            band = bands[i % len(bands)]
            song = Song(
                title=f"Song {i}",
                artist=f"Artist {i}",
                status=SongStatus.ACTIVE if i % 3 == 0 else SongStatus.WISHLIST,
                duration_seconds=240 + (i % 300),
                band_id=band.id
            )
            db.session.add(song)
            songs.append(song)
        
        db.session.commit()
        
        # Create progress records for active songs
        active_songs = [song for song in songs if song.status == SongStatus.ACTIVE]
        for song in active_songs:
            # Each active song gets progress from 3-5 random users
            import random
            user_count = random.randint(3, 5)
            selected_users = random.sample(users, user_count)
            
            for user in selected_users:
                if user.is_member_of(song.band_id):
                    status = random.choice(list(ProgressStatus))
                    progress = SongProgress(
                        user_id=user.id,
                        song_id=song.id,
                        status=status
                    )
                    db.session.add(progress)
        
        # Create votes for wishlist songs
        wishlist_songs = [song for song in songs if song.status == SongStatus.WISHLIST]
        for song in wishlist_songs:
            # Each wishlist song gets votes from 2-4 random users
            import random
            user_count = random.randint(2, 4)
            selected_users = random.sample(users, user_count)
            
            for user in selected_users:
                if user.is_member_of(song.band_id):
                    vote = Vote(
                        user_id=user.id,
                        song_id=song.id
                    )
                    db.session.add(vote)
        
        db.session.commit()
        
        return {
            'bands': bands,
            'users': users,
            'songs': songs,
            'active_songs': active_songs,
            'wishlist_songs': wishlist_songs
        }


class TestQueryPerformance:
    """Test query performance with large datasets"""
    
    def test_band_member_query_performance(self, app, large_dataset):
        """Test performance of band member queries"""
        with app.app_context():
            bands = large_dataset['bands']
            
            start_time = time.time()
            
            # Query all bands with their member counts
            band_member_counts = []
            for band in bands:
                member_count = len([user for user in large_dataset['users'] if user.is_member_of(band.id)])
                band_member_counts.append((band.name, member_count))
            
            end_time = time.time()
            query_time = end_time - start_time
            
            # Should complete in reasonable time (less than 1 second)
            assert query_time < 1.0
            assert len(band_member_counts) == 10
    
    def test_song_progress_aggregation_performance(self, app, large_dataset):
        """Test performance of song progress aggregation queries"""
        with app.app_context():
            active_songs = large_dataset['active_songs']
            
            start_time = time.time()
            
            # Aggregate progress by status for all active songs
            progress_stats = {}
            for song in active_songs:
                progress_records = SongProgress.query.filter_by(song_id=song.id).all()
                for progress in progress_records:
                    status = progress.status.value
                    progress_stats[status] = progress_stats.get(status, 0) + 1
            
            end_time = time.time()
            query_time = end_time - start_time
            
            # Should complete in reasonable time
            assert query_time < 2.0
            assert len(progress_stats) > 0
    
    def test_vote_counting_performance(self, app, large_dataset):
        """Test performance of vote counting queries"""
        with app.app_context():
            wishlist_songs = large_dataset['wishlist_songs']
            
            start_time = time.time()
            
            # Count votes for all wishlist songs
            vote_counts = []
            for song in wishlist_songs:
                vote_count = Vote.query.filter_by(song_id=song.id).count()
                vote_counts.append((song.title, vote_count))
            
            end_time = time.time()
            query_time = end_time - start_time
            
            # Should complete in reasonable time
            assert query_time < 1.0
            assert len(vote_counts) > 0
    
    def test_complex_join_performance(self, app, large_dataset):
        """Test performance of complex joins"""
        with app.app_context():
            start_time = time.time()
            
            # Complex query: bands with member count, active song count, and average vote count
            result = db.session.query(
                Band.name,
                func.count(func.distinct(db.text('band_membership.user_id'))).label('member_count'),
                func.count(func.distinct(Song.id)).label('active_song_count'),
                func.avg(func.coalesce(Vote.id, 0)).label('avg_votes')
            ).outerjoin(db.text('band_membership'), Band.id == db.text('band_membership.band_id')) \
             .outerjoin(Song, (Band.id == Song.band_id) & (Song.status == SongStatus.ACTIVE)) \
             .outerjoin(Vote, Song.id == Vote.song_id) \
             .group_by(Band.id, Band.name) \
             .all()
            
            end_time = time.time()
            query_time = end_time - start_time
            
            # Should complete in reasonable time
            assert query_time < 2.0
            assert len(result) == 10
    
    def test_pagination_performance(self, app, large_dataset):
        """Test performance of paginated queries"""
        with app.app_context():
            songs = large_dataset['songs']
            
            start_time = time.time()
            
            # Test pagination with different page sizes
            page_size = 20
            total_pages = (len(songs) + page_size - 1) // page_size
            
            for page in range(min(5, total_pages)):  # Test first 5 pages
                offset = page * page_size
                page_songs = Song.query.offset(offset).limit(page_size).all()
                assert len(page_songs) <= page_size
            
            end_time = time.time()
            query_time = end_time - start_time
            
            # Should complete in reasonable time
            assert query_time < 1.0


class TestIndexingPerformance:
    """Test database indexing performance"""
    
    def test_foreign_key_index_performance(self, app, large_dataset):
        """Test performance of foreign key lookups"""
        with app.app_context():
            songs = large_dataset['songs']
            bands = large_dataset['bands']
            
            start_time = time.time()
            
            # Query songs by band (tests foreign key index)
            for band in bands:
                band_songs = Song.query.filter_by(band_id=band.id).all()
                assert len(band_songs) > 0
            
            end_time = time.time()
            query_time = end_time - start_time
            
            # Should complete quickly with proper indexing
            assert query_time < 1.0
    
    def test_unique_constraint_performance(self, app, large_dataset):
        """Test performance of unique constraint checks"""
        with app.app_context():
            users = large_dataset['users']
            songs = large_dataset['songs']
            
            start_time = time.time()
            
            # Test unique constraint on user_id + song_id for votes
            for i in range(100):  # Test 100 unique constraint checks
                user = users[i % len(users)]
                song = songs[i % len(songs)]
                
                # This should be fast due to unique index
                existing_vote = Vote.query.filter_by(
                    user_id=user.id,
                    song_id=song.id
                ).first()
            
            end_time = time.time()
            query_time = end_time - start_time
            
            # Should complete quickly
            assert query_time < 1.0


class TestConcurrentAccess:
    """Test database performance under concurrent access simulation"""
    
    def test_concurrent_reads(self, app, large_dataset):
        """Test performance with simulated concurrent reads"""
        with app.app_context():
            import threading
            import queue
            
            results = queue.Queue()
            
            def read_worker(worker_id):
                """Worker function that performs read operations"""
                start_time = time.time()
                
                # Perform various read operations
                bands = Band.query.all()
                users = User.query.all()
                songs = Song.query.all()
                
                # Complex query
                band_stats = db.session.query(
                    Band.name,
                    func.count(func.distinct(db.text('band_membership.user_id'))).label('member_count')
                ).outerjoin(db.text('band_membership'), Band.id == db.text('band_membership.band_id')) \
                 .group_by(Band.id, Band.name) \
                 .all()
                
                end_time = time.time()
                results.put((worker_id, end_time - start_time))
            
            # Start multiple threads
            threads = []
            for i in range(5):  # 5 concurrent workers
                thread = threading.Thread(target=read_worker, args=(i,))
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            # Collect results
            worker_times = []
            while not results.empty():
                worker_id, worker_time = results.get()
                worker_times.append(worker_time)
            
            # All workers should complete in reasonable time
            assert len(worker_times) == 5
            for worker_time in worker_times:
                assert worker_time < 3.0  # Each worker should complete within 3 seconds
    
    def test_mixed_read_write_performance(self, app, large_dataset):
        """Test performance with mixed read and write operations"""
        with app.app_context():
            users = large_dataset['users']
            bands = large_dataset['bands']
            
            start_time = time.time()
            
            # Mix of read and write operations
            for i in range(50):
                # Read operation
                band = bands[i % len(bands)]
                members = [user for user in users if user.is_member_of(band.id)]
                
                # Write operation (if not already a member)
                if i < len(users) and not users[i].is_member_of(band.id):
                    band.add_member(users[i], UserRole.MEMBER)
                
                # Another read operation
                songs = Song.query.filter_by(band_id=band.id).all()
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Should complete in reasonable time
            assert total_time < 5.0


class TestMemoryUsage:
    """Test memory usage with large datasets"""
    
    def test_large_result_set_memory(self, app, large_dataset):
        """Test memory usage with large result sets"""
        with app.app_context():
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss
            
            # Load large result set
            all_songs = Song.query.all()
            all_users = User.query.all()
            all_progress = SongProgress.query.all()
            all_votes = Vote.query.all()
            
            peak_memory = process.memory_info().rss
            memory_increase = peak_memory - initial_memory
            
            # Memory increase should be reasonable (less than 100MB)
            assert memory_increase < 100 * 1024 * 1024  # 100MB in bytes
            
            # Verify data integrity
            assert len(all_songs) > 0
            assert len(all_users) > 0
            assert len(all_progress) > 0
            assert len(all_votes) > 0
    
    def test_query_memory_efficiency(self, app, large_dataset):
        """Test memory efficiency of different query patterns"""
        with app.app_context():
            import psutil
            import os
            
            process = psutil.Process(os.getpid())
            
            # Test 1: Load all data at once
            initial_memory = process.memory_info().rss
            all_data = db.session.query(Song, User, Band).all()
            peak_memory_1 = process.memory_info().rss
            
            # Clear memory
            del all_data
            db.session.expunge_all()
            
            # Test 2: Load data in batches
            initial_memory_2 = process.memory_info().rss
            batch_size = 100
            total_loaded = 0
            
            for offset in range(0, 1000, batch_size):
                batch = Song.query.offset(offset).limit(batch_size).all()
                total_loaded += len(batch)
            
            peak_memory_2 = process.memory_info().rss
            
            # Batch loading should use less memory
            memory_increase_1 = peak_memory_1 - initial_memory
            memory_increase_2 = peak_memory_2 - initial_memory_2
            
            # Batch loading should be more memory efficient
            assert memory_increase_2 < memory_increase_1


class TestDatabaseMaintenance:
    """Test database maintenance operations"""
    
    def test_vacuum_analyze_performance(self, app, large_dataset):
        """Test performance of database maintenance operations"""
        with app.app_context():
            start_time = time.time()
            
            # Perform VACUUM ANALYZE
            db.session.execute(text("VACUUM ANALYZE"))
            
            end_time = time.time()
            maintenance_time = end_time - start_time
            
            # Maintenance should complete in reasonable time
            assert maintenance_time < 10.0  # Should complete within 10 seconds
    
    def test_index_rebuild_performance(self, app, large_dataset):
        """Test performance of index rebuild operations"""
        with app.app_context():
            start_time = time.time()
            
            # Rebuild indexes
            db.session.execute(text("REINDEX DATABASE bandmate_test"))
            
            end_time = time.time()
            rebuild_time = end_time - start_time
            
            # Index rebuild should complete in reasonable time
            assert rebuild_time < 15.0  # Should complete within 15 seconds
    
    def test_statistics_update_performance(self, app, large_dataset):
        """Test performance of statistics update operations"""
        with app.app_context():
            start_time = time.time()
            
            # Update table statistics
            db.session.execute(text("ANALYZE"))
            
            end_time = time.time()
            stats_time = end_time - start_time
            
            # Statistics update should complete quickly
            assert stats_time < 5.0  # Should complete within 5 seconds


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
