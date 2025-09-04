# BandMate Database Integration Tests

This document describes the comprehensive database integration test suite for BandMate, designed to ensure data integrity, performance, and reliability with PostgreSQL.

## Test Structure

### Test Files

1. **`test_database_integration.py`** - Core integration tests
   - User-Band relationships and multi-band support
   - Song management and progress tracking
   - Voting system functionality
   - Invitation system
   - Setlist configuration
   - Data integrity and constraints

2. **`test_database_performance.py`** - Performance and scalability tests
   - Query performance with large datasets
   - Indexing effectiveness
   - Concurrent access simulation
   - Memory usage optimization
   - Database maintenance operations

3. **`test_database_relationships.py`** - Complex relationship tests
   - Multi-band user relationships
   - Cascading operations
   - Data consistency validation
   - Complex query testing

## Test Categories

### 🔗 Integration Tests
- **User-Band Relationships**: Multi-band membership, role management
- **Song Management**: Creation, status changes, progress tracking
- **Voting System**: Vote creation, counting, unique constraints
- **Invitation System**: Creation, validation, expiration
- **Setlist Configuration**: Band-specific settings and calculations
- **Data Integrity**: Foreign key constraints, cascading deletes

### ⚡ Performance Tests
- **Query Performance**: Large dataset queries, complex joins
- **Indexing**: Foreign key lookups, unique constraint checks
- **Concurrent Access**: Multi-threaded read/write operations
- **Memory Usage**: Large result sets, batch processing
- **Database Maintenance**: VACUUM, ANALYZE, REINDEX operations

### 🤝 Relationship Tests
- **Multi-Band Support**: Cross-band user access, permissions
- **Cascading Operations**: Delete cascades, data consistency
- **Complex Queries**: Statistics, aggregation, analysis
- **Data Consistency**: Relationship integrity validation

## Running Tests

### Prerequisites

1. **PostgreSQL Setup**:
   ```bash
   # Install PostgreSQL
   brew install postgresql  # macOS
   sudo apt install postgresql  # Ubuntu
   
   # Start PostgreSQL
   brew services start postgresql  # macOS
   sudo systemctl start postgresql  # Ubuntu
   
   # Create test database
   sudo -u postgres psql
   CREATE DATABASE bandmate_test;
   CREATE USER test_user WITH PASSWORD 'test_pass';
   GRANT ALL PRIVILEGES ON DATABASE bandmate_test TO test_user;
   \q
   ```

2. **Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   pip install psycopg2-binary  # PostgreSQL driver
   ```

### Test Commands

#### Using the Test Runner
```bash
# Run all database tests
python run_database_tests.py all

# Run specific test categories
python run_database_tests.py integration
python run_database_tests.py performance
python run_database_tests.py relationships

# Run quick tests (subset)
python run_database_tests.py quick

# Run with coverage
python run_database_tests.py coverage
```

#### Using Make
```bash
# Run all database tests
make test-db

# Run specific categories
make test-db-integration
make test-db-performance
make test-db-relationships

# Run quick tests
make test-db-quick

# Run in Docker
make test-db-docker
```

#### Using pytest directly
```bash
# Run all database tests
pytest tests/test_database_*.py -v

# Run specific test file
pytest tests/test_database_integration.py -v

# Run specific test class
pytest tests/test_database_integration.py::TestUserBandRelationships -v

# Run with coverage
pytest tests/test_database_*.py --cov=app --cov-report=html
```

### Docker Testing

For consistent testing across environments:

```bash
# Run tests in Docker
docker-compose -f docker-compose.test.yml up --build

# Or using make
make test-db-docker
```

## Test Data

### Fixtures

Tests use comprehensive fixtures that create realistic data:

- **10 Bands**: Different musical styles and configurations
- **100 Users**: Multi-band memberships with various roles
- **500 Songs**: Mix of active and wishlist songs
- **Progress Records**: Realistic progress tracking
- **Votes**: Voting patterns on wishlist songs
- **Invitations**: Sample pending invitations

### Data Relationships

- Users can be members of multiple bands
- Each band has songs in different statuses
- Progress records track individual member progress
- Votes are cast on wishlist songs
- Invitations link users to bands

## Performance Benchmarks

### Query Performance Targets

- **Simple Queries**: < 100ms
- **Complex Joins**: < 500ms
- **Aggregation Queries**: < 1s
- **Large Dataset Queries**: < 2s

### Memory Usage Targets

- **Large Result Sets**: < 100MB increase
- **Batch Processing**: More efficient than bulk loading
- **Concurrent Operations**: Stable memory usage

### Concurrent Access

- **5 Concurrent Readers**: All complete within 3s
- **Mixed Read/Write**: Stable performance under load
- **Transaction Isolation**: No data corruption

## Test Coverage

### Database Models
- ✅ User model and relationships
- ✅ Band model and membership management
- ✅ Song model and status management
- ✅ SongProgress model and tracking
- ✅ Vote model and constraints
- ✅ Invitation model and validation
- ✅ SetlistConfig model and calculations

### Database Operations
- ✅ CRUD operations for all models
- ✅ Relationship management
- ✅ Constraint validation
- ✅ Cascading operations
- ✅ Transaction handling
- ✅ Bulk operations

### Query Patterns
- ✅ Simple lookups and filters
- ✅ Complex joins and aggregations
- ✅ Pagination and sorting
- ✅ Performance optimization
- ✅ Index utilization

## Troubleshooting

### Common Issues

1. **PostgreSQL Connection Failed**:
   ```bash
   # Check if PostgreSQL is running
   brew services list | grep postgresql
   sudo systemctl status postgresql
   
   # Check connection
   psql -h localhost -U test_user -d bandmate_test
   ```

2. **Permission Denied**:
   ```sql
   -- Grant proper permissions
   GRANT ALL PRIVILEGES ON DATABASE bandmate_test TO test_user;
   GRANT ALL ON SCHEMA public TO test_user;
   ```

3. **Test Timeout**:
   ```bash
   # Increase timeout in pytest.ini
   timeout = 600
   
   # Or run specific tests
   pytest tests/test_database_integration.py::TestUserBandRelationships -v
   ```

4. **Memory Issues**:
   ```bash
   # Run tests with smaller datasets
   python run_database_tests.py quick
   
   # Or run specific test categories
   python run_database_tests.py integration
   ```

### Debug Mode

Run tests with verbose output and debugging:

```bash
# Verbose output
pytest tests/test_database_*.py -v -s

# Debug specific test
pytest tests/test_database_integration.py::TestUserBandRelationships::test_user_can_join_multiple_bands -v -s --pdb

# Show SQL queries
pytest tests/test_database_*.py -v -s --log-cli-level=DEBUG
```

## Continuous Integration

### GitHub Actions Example

```yaml
name: Database Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: bandmate_test
          POSTGRES_USER: test_user
          POSTGRES_PASSWORD: test_pass
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.9
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install psycopg2-binary
    
    - name: Run database tests
      run: python run_database_tests.py all
      env:
        DATABASE_URL: postgresql://test_user:test_pass@localhost:5432/bandmate_test
```

## Best Practices

### Writing Tests

1. **Use Fixtures**: Create reusable test data
2. **Test Edge Cases**: Boundary conditions and error states
3. **Verify Data Integrity**: Check relationships and constraints
4. **Performance Testing**: Include timing assertions
5. **Clean Up**: Ensure tests don't leave side effects

### Test Organization

1. **Group Related Tests**: Use test classes for related functionality
2. **Descriptive Names**: Clear test method names
3. **Setup/Teardown**: Proper test isolation
4. **Documentation**: Comment complex test logic

### Database Testing

1. **Transaction Isolation**: Each test in its own transaction
2. **Data Cleanup**: Clean up after each test
3. **Index Testing**: Verify index usage
4. **Constraint Testing**: Test foreign key and unique constraints

## Monitoring and Maintenance

### Test Metrics

- **Test Execution Time**: Track test performance over time
- **Coverage Percentage**: Maintain high test coverage
- **Failure Rate**: Monitor test stability
- **Performance Regression**: Detect performance issues early

### Regular Maintenance

1. **Update Test Data**: Keep test data realistic and current
2. **Review Performance**: Check for performance regressions
3. **Update Dependencies**: Keep test dependencies current
4. **Documentation**: Keep test documentation up to date

This comprehensive test suite ensures that BandMate's database layer is robust, performant, and reliable for production use.
