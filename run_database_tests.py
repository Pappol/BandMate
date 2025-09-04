#!/usr/bin/env python3
"""
Database Test Runner for BandMate
Runs comprehensive database integration tests with PostgreSQL
"""

import os
import sys
import subprocess
import time
from pathlib import Path

def setup_test_environment():
    """Set up test environment variables"""
    os.environ['FLASK_ENV'] = 'testing'
    os.environ['DATABASE_URL'] = 'postgresql://test_user:test_pass@localhost:5432/bandmate_test'
    os.environ['FLASK_SECRET_KEY'] = 'test-secret-key'
    os.environ['GOOGLE_CLIENT_ID'] = 'test-client-id'
    os.environ['GOOGLE_CLIENT_SECRET'] = 'test-client-secret'

def check_postgresql_connection():
    """Check if PostgreSQL is available and accessible"""
    try:
        import psycopg2
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='bandmate_test',
            user='test_user',
            password='test_pass'
        )
        conn.close()
        print("✅ PostgreSQL connection successful")
        return True
    except Exception as e:
        print(f"❌ PostgreSQL connection failed: {e}")
        print("\nTo set up PostgreSQL for testing:")
        print("1. Install PostgreSQL: brew install postgresql (macOS) or apt install postgresql (Ubuntu)")
        print("2. Start PostgreSQL: brew services start postgresql (macOS) or systemctl start postgresql (Ubuntu)")
        print("3. Create test database:")
        print("   sudo -u postgres psql")
        print("   CREATE DATABASE bandmate_test;")
        print("   CREATE USER test_user WITH PASSWORD 'test_pass';")
        print("   GRANT ALL PRIVILEGES ON DATABASE bandmate_test TO test_user;")
        print("   \\q")
        return False

def run_tests(test_files=None, verbose=True, coverage=False):
    """Run database tests"""
    if test_files is None:
        test_files = [
            'tests/test_database_integration.py',
            'tests/test_database_performance.py',
            'tests/test_database_relationships.py'
        ]
    
    # Build pytest command
    cmd = ['python', '-m', 'pytest']
    
    if verbose:
        cmd.append('-v')
    
    if coverage:
        cmd.extend(['--cov=app', '--cov-report=html', '--cov-report=term'])
    
    # Add test files
    cmd.extend(test_files)
    
    # Add additional options
    cmd.extend([
        '--tb=short',  # Short traceback format
        '--strict-markers',  # Strict marker checking
        '--disable-warnings',  # Disable warnings for cleaner output
        '--color=yes'  # Colored output
    ])
    
    print(f"🚀 Running database tests: {' '.join(cmd)}")
    print("=" * 60)
    
    start_time = time.time()
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        end_time = time.time()
        
        print("=" * 60)
        print(f"✅ All tests passed! (took {end_time - start_time:.2f} seconds)")
        return True
        
    except subprocess.CalledProcessError as e:
        end_time = time.time()
        print("=" * 60)
        print(f"❌ Tests failed! (took {end_time - start_time:.2f} seconds)")
        print(f"Exit code: {e.returncode}")
        return False
    except KeyboardInterrupt:
        print("\n⏹️  Tests interrupted by user")
        return False

def run_specific_test_class(test_file, test_class):
    """Run a specific test class"""
    cmd = [
        'python', '-m', 'pytest',
        f'{test_file}::{test_class}',
        '-v',
        '--tb=short',
        '--color=yes'
    ]
    
    print(f"🎯 Running specific test class: {test_class}")
    print("=" * 60)
    
    try:
        subprocess.run(cmd, check=True)
        print("✅ Test class passed!")
        return True
    except subprocess.CalledProcessError:
        print("❌ Test class failed!")
        return False

def run_performance_tests():
    """Run only performance tests"""
    print("⚡ Running performance tests...")
    return run_tests(['tests/test_database_performance.py'])

def run_integration_tests():
    """Run only integration tests"""
    print("🔗 Running integration tests...")
    return run_tests(['tests/test_database_integration.py'])

def run_relationship_tests():
    """Run only relationship tests"""
    print("🤝 Running relationship tests...")
    return run_tests(['tests/test_database_relationships.py'])

def main():
    """Main test runner"""
    print("🧪 BandMate Database Test Runner")
    print("=" * 60)
    
    # Set up environment
    setup_test_environment()
    
    # Check PostgreSQL connection
    if not check_postgresql_connection():
        return 1
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == 'integration':
            success = run_integration_tests()
        elif command == 'performance':
            success = run_performance_tests()
        elif command == 'relationships':
            success = run_relationship_tests()
        elif command == 'all':
            success = run_tests(coverage=True)
        elif command == 'coverage':
            success = run_tests(coverage=True)
        elif command == 'quick':
            # Run a subset of tests for quick feedback
            success = run_tests(['tests/test_database_integration.py::TestUserBandRelationships'])
        else:
            print(f"❌ Unknown command: {command}")
            print("\nAvailable commands:")
            print("  integration  - Run integration tests")
            print("  performance  - Run performance tests")
            print("  relationships - Run relationship tests")
            print("  all         - Run all tests with coverage")
            print("  coverage    - Run all tests with coverage report")
            print("  quick       - Run quick subset of tests")
            return 1
    else:
        # Default: run all tests
        success = run_tests(coverage=True)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
