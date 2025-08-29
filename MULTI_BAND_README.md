# 🎸 BandMate Multi-Band Functionality

## Overview

The BandMate application has been enhanced with comprehensive multi-band support, allowing users to be members of multiple bands simultaneously and seamlessly switch between them.

## ✨ Key Features

### Multi-Band Membership
- **Many-to-Many Relationship**: Users can belong to multiple bands at the same time
- **Role-Based Access**: Each band membership has a specific role (Leader/Member)
- **Band Switching**: Quick switching between bands via navigation dropdown
- **Data Isolation**: All data (songs, progress, setlists) is scoped to the current band

### User Experience
- **Band Switcher**: Dropdown in navigation showing all user's bands
- **Band Selection Page**: Dedicated page for users with multiple bands
- **Create New Band**: Easy band creation with automatic leadership role
- **Join Existing Band**: Join bands using invitation codes

## 🏗️ Architecture Changes

### Database Schema
- **New Table**: `band_membership` association table
- **Fields**: `user_id`, `band_id`, `role`, `joined_at`
- **Relationships**: Many-to-many between User and Band models

### Model Updates
- **User Model**: Added `bands` relationship and role management methods
- **Band Model**: Added member management methods and role queries
- **Backward Compatibility**: Legacy `band_id` field maintained during transition

### Session Management
- **Current Band**: Stored in `session['current_band_id']`
- **Context Processor**: Makes `current_band` available globally in templates
- **Automatic Selection**: Single band users automatically set current band

## 🚀 Getting Started

### 1. Database Migration
Run the migration script to update your database:

```bash
python migrate_multi_band.py
```

### 2. Test the Functionality
Run the comprehensive test suite:

```bash
# Run all multi-band tests
python run_multi_band_tests.py

# Or run specific tests
python -m pytest tests/test_multi_band.py -v
```

### 3. Use the New Features
- **Band Switching**: Use the dropdown in the navigation
- **Create Bands**: Navigate to "Manage Bands" → "Create New Band"
- **Join Bands**: Use invitation codes from band leaders

## 📱 User Interface

### Navigation Band Switcher
- **Dropdown Menu**: Shows all user's bands with current band highlighted
- **Quick Switch**: Click any band to switch context immediately
- **Role Indicators**: Shows leader/member status for each band
- **Manage Bands**: Link to band management page

### Band Selection Page
- **Band Cards**: Visual representation of all user's bands
- **Role Badges**: Clear indication of leadership status
- **Action Buttons**: Quick access to create/join new bands

### Create Band Form
- **Simple Input**: Just enter the band name
- **Automatic Leadership**: Creator becomes band leader
- **Immediate Access**: New band becomes current band

### Join Band Form
- **Invitation Code**: 8-character alphanumeric code input
- **Validation**: Real-time code format checking
- **Security**: Expired/invalid code handling

## 🔧 Technical Implementation

### New Routes
```python
@main.route('/band/switch/<int:band_id>')      # Switch active band
@main.route('/band/select')                    # Band selection page
@main.route('/band/create', methods=['GET', 'POST'])  # Create new band
@main.route('/band/join', methods=['GET', 'POST'])    # Join existing band
```

### Context Processor
```python
@app.context_processor
def inject_current_band():
    """Make current band available in all templates"""
    current_band = None
    if 'current_band_id' in session:
        current_band = Band.query.get(session['current_band_id'])
    return dict(current_band=current_band)
```

### Model Methods
```python
# User methods
user.is_leader_of(band_id)      # Check leadership in specific band
user.is_member_of(band_id)      # Check membership in specific band
user.get_band_role(band_id)     # Get role in specific band

# Band methods
band.add_member(user, role)     # Add user with specific role
band.remove_member(user_id)     # Remove user from band
band.get_member_role(user_id)   # Get user's role in band
```

## 🧪 Testing

### Test Coverage
- **25 Test Cases**: Comprehensive coverage of all multi-band features
- **Model Testing**: Database relationships and role management
- **Route Testing**: All new endpoints and functionality
- **UI Testing**: Template rendering and user interactions
- **Integration Testing**: End-to-end multi-band workflows

### Test Categories
1. **BandMembershipModel**: Association table and relationships
2. **MultiBandRoutes**: New route functionality
3. **DashboardMultiBand**: Dashboard with multi-band support
4. **ContextProcessor**: Template context injection
5. **DataScoping**: Band-specific data filtering
6. **InvitationSystem**: Invitation handling with multi-band

### Running Tests
```bash
# Full test suite
python run_multi_band_tests.py

# Individual test categories
python -m pytest tests/test_multi_band.py::TestBandMembershipModel -v
python -m pytest tests/test_multi_band.py::TestMultiBandRoutes -v
python -m pytest tests/test_multi_band.py::TestDashboardMultiBand -v
```

## 🔄 Migration Process

### Step 1: Create New Table
- Creates `band_membership` association table
- Adds indexes for performance
- Sets up foreign key constraints

### Step 2: Migrate Existing Data
- Moves existing user-band relationships to new table
- Preserves role information (band leaders)
- Maintains data integrity

### Step 3: Update Models
- Adds new relationships to User and Band models
- Maintains backward compatibility
- Provides migration path for existing code

### Step 4: Verify Migration
- Checks table creation and data migration
- Validates relationship integrity
- Reports migration success/failure

## 🚨 Important Notes

### Backward Compatibility
- **Legacy Fields**: `band_id` and `is_band_leader` remain for compatibility
- **Gradual Migration**: Existing code continues to work during transition
- **Fallback Support**: Models provide fallback to legacy relationships

### Data Scoping
- **Session-Based**: Current band stored in Flask session
- **Template Access**: `current_band` available globally via context processor
- **Query Filtering**: All data queries must filter by current band

### Security Considerations
- **Role Validation**: All band operations validate user membership
- **Permission Checks**: Leader-only operations verify leadership status
- **Session Security**: Band switching validates user permissions

## 🐛 Troubleshooting

### Common Issues

#### "No current band set" Error
- **Cause**: User hasn't selected a band or session expired
- **Solution**: Redirect to band selection page

#### Band Switching Fails
- **Cause**: User not member of target band
- **Solution**: Verify band membership and permissions

#### Template Errors
- **Cause**: `current_band` not available in template
- **Solution**: Check context processor and session state

### Debug Commands
```bash
# Check database state
python manage.py status

# Verify band memberships
python -c "
from app import create_app, db
from app.models import User, Band
app = create_app()
with app.app_context():
    users = User.query.all()
    for user in users:
        print(f'{user.name}: {len(user.bands)} bands')
"
```

## 📚 API Reference

### Band Membership Endpoints

#### Switch Band
```http
GET /band/switch/{band_id}
```
Switches the current active band for the authenticated user.

**Parameters:**
- `band_id` (integer): ID of the band to switch to

**Response:**
- Redirects to previous page or dashboard
- Sets `session['current_band_id']`

#### Select Band
```http
GET /band/select
```
Shows band selection page for users with multiple bands.

**Response:**
- HTML page with band selection options
- Redirects to dashboard if only one band

#### Create Band
```http
POST /band/create
```
Creates a new band and adds the user as leader.

**Form Data:**
- `band_name` (string): Name of the new band

**Response:**
- Redirects to dashboard with new band as current

#### Join Band
```http
POST /band/join
```
Joins an existing band using an invitation code.

**Form Data:**
- `invitation_code` (string): 8-character invitation code

**Response:**
- Redirects to dashboard with joined band as current

## 🔮 Future Enhancements

### Planned Features
- **Band Templates**: Pre-configured band setups
- **Band Analytics**: Cross-band performance metrics
- **Advanced Permissions**: Granular role-based access control
- **Band Collaboration**: Inter-band song sharing

### Performance Optimizations
- **Caching**: Band membership caching for frequent queries
- **Lazy Loading**: On-demand band data loading
- **Database Indexing**: Optimized queries for large band memberships

## 📞 Support

For questions or issues with the multi-band functionality:

1. **Check the Tests**: Run `python run_multi_band_tests.py`
2. **Review Documentation**: Check this README and main documentation
3. **Database Issues**: Verify migration with `python migrate_multi_band.py`
4. **Code Problems**: Check the test suite for expected behavior

---

*Multi-Band functionality implemented in BandMate v0.3.0-alpha*
