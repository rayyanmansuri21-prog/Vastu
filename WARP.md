# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

## Project Overview

**Cosmo-Vastu** is a Django-based web application for Vastu Shastra blueprint analysis. The application allows users to upload architectural blueprints, analyze them according to Vastu principles by dividing them into directional zones (8, 16, or 32 divisions), and generate detailed reports with area calculations and directional analysis.

## Commands

### Environment Setup
```powershell
# Activate virtual environment (Windows PowerShell)
.\.vastuenv\Scripts\Activate.ps1

# Install dependencies (if requirements.txt exists)
pip install django pillow matplotlib reportlab python-docx ezdxf fpdf mysqlclient

# Navigate to Django project directory
cd vastu_app
```

### Database
```powershell
# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Make migrations after model changes
python manage.py makemigrations
```

### Development Server
```powershell
# Start development server
python manage.py runserver

# Access application at http://127.0.0.1:8000/
```

### Testing
```powershell
# Run tests
python manage.py test main

# Run specific test
python manage.py test main.tests.TestClassName
```

## Architecture

### Application Structure

This is a standard Django project with the following layout:
- **`vastu_app/`** - Django project root
  - **`main/`** - Primary Django app containing all business logic
  - **`vastu_app/`** - Django project configuration (settings, root URLs, WSGI)
  - **`templates/`** - HTML templates
  - **`static/`** - CSS, JavaScript, images
  - **`media/`** - User-uploaded files (blueprints, generated images, DXF files)

### Core Data Models

**Project Model** (`main/models.py`):
- Represents a Vastu analysis project
- Stores blueprint image and generated analysis images (centroid, compass, divided images for 8/16/32 parts)
- Stores DXF files for each division (divided_8_dxf, divided_16_dxf, divided_32_dxf)
- Links to Django User via ForeignKey
- Tracks status (Planned/In Progress) and category (Residential/Commercial)

**UserProfile Model** (`main/models.py`):
- OneToOne relationship with Django User
- `project_limit` field controls how many projects a user can create (default: 3)
- Automatically created via signals when a new user registers

### Authentication Flow

1. **OTP-based Login** (`login_view`): User enters username and email → system generates 4-digit OTP → sent via email
2. **OTP Verification** (`verify_otp`): User enters OTP → system validates → creates/retrieves User → logs in via Django sessions
3. **No password authentication** - uses `set_unusable_password()` for OTP-only auth
4. **Admin Panel**: Separate static credentials (username: `admin`, password: `admin11`) with custom admin dashboard

### Blueprint Analysis Workflow

1. **Project Creation**: User uploads blueprint image → creates Project record
2. **Blueprint Workspace**: Interactive canvas where users:
   - Calculate centroid of the blueprint polygon
   - Set compass direction and rotation
   - Draw grid over blueprint
   - System divides into 8, 16, or 32 directional zones
3. **Zone Analysis**: 
   - Frontend sends zone measurements (width/height in inches) to backend
   - `calculate_zonal_areas()` in `utils.py` computes area for each zone in sq ft
   - `calculate_directional_areas()` maps grid points to compass directions
4. **DXF Generation**: System creates CAD files (`.dxf`) with radial lines and area labels using `ezdxf` library
5. **Report Generation**:
   - Graph generation: Bar charts showing area distribution per direction
   - Word document: Complete report with all images, tables, and graphs using `python-docx`
   - PDF support via ReportLab

### Session Management

The application heavily uses Django sessions to store temporary data:
- `grid_points`: Array of grid coordinates drawn by user
- `compass_center`: [x, y] coordinates of compass center
- `compass_rotation`: Rotation angle of compass in degrees
- `divisions`: Current division setting (8, 16, or 32)
- `zone_measurements`: List of zone dimensions and measurements
- `otp`, `email`, `username`: Temporary auth data during login

### Key Utilities (`main/utils.py`)

- **`get_angle(cx, cy, px, py)`**: Calculate bearing angle from center to point
- **`get_direction(angle, divisions, compass_rotation)`**: Map angle to directional label (N, NE, E, etc.)
- **`calculate_zonal_areas(zone_measurements)`**: Core area calculation logic - converts zone dimensions to square feet
- **`process_dxf_with_ezdxf(doc, compass_center, divisions, compass_rotation)`**: Parse DXF files and count entities per direction

### Important View Functions

- **`dashboard_view`**: Displays user's projects, respects project_limit
- **`create_project`**: Enforces project limit before creating new project
- **`blueprint_workspace`**: Main interactive workspace for blueprint analysis
- **`analyze_grid`**: AJAX endpoint that receives zone measurements and returns area calculations
- **`plot_graph_and_area`**: Generates DXF with zonal divisions and area labels
- **`save_project_image`**: Saves canvas snapshots and converts to DXF
- **`download_blueprint`**: Generates directional bar chart as DXF download
- **`download_word_blueprint`**: Creates comprehensive Word document report with custom styling
- **`generate_graph_data_view`**: Reads stored DXF and generates direction-wise area data
- **`increase_project_limit`**: Admin function to increase user's project limit (sends notification email)

### Database Configuration

- Uses **MySQL** database (`vastu_db`)
- Connection configured in `settings.py`:
  - Host: localhost
  - Port: 3306
  - User: root
  - Password: sql@12345 (should be in environment variable for production)

### Email Configuration

- Uses Gmail SMTP for sending OTP and notifications
- Configured in `settings.py`:
  - EMAIL_HOST: smtp.gmail.com
  - EMAIL_PORT: 587
  - Uses App Password (not regular Gmail password)
  - Current sender: gohelhetvi18@gmail.com

## Development Practices

### When Modifying Models
1. Always run `makemigrations` after model changes
2. Review generated migration files before applying
3. Run `migrate` to apply changes
4. UserProfile is auto-created via signals - don't create manually

### Working with Sessions
- Session data persists across requests during blueprint analysis
- Clear sessions appropriately after analysis completion
- Session-stored data is critical for multi-step workflows (grid → compass → analysis → report)

### Image and File Handling
- Blueprint uploads go to `media/blueprints/`
- Generated analysis images go to `media/project_images/`
- DXF files stored in `media/divided_8_dxf/`, `divided_16_dxf/`, `divided_32_dxf/`
- All use Django's FileField/ImageField with automatic storage management

### DXF File Processing
- DXF files are created using `ezdxf` library
- They contain actual CAD entities (lines, polylines, text), not just images
- Process: Image → Grid → DXF entities → Directional analysis → Graph/Report
- DXF parsing in `views.py` processes LINE, LWPOLYLINE, POLYLINE, INSERT, CIRCLE entities

### Admin Features
- Custom admin dashboard separate from Django admin
- Can view all users and their project counts
- Can increase individual user project limits
- Can delete users
- Email notifications sent when limits are increased

### Frontend-Backend Communication
- Heavy use of AJAX for interactive blueprint workspace
- Canvas drawings sent as base64-encoded images
- JSON payloads for grid data and measurements
- Response includes generated images/files as base64 or file downloads

## Project-Specific Notes

### Compass Direction Labels
The application uses specific label schemes for different divisions:
- **8 divisions**: N, NE, E, SE, S, SW, W, NW
- **16 divisions**: N, NNE, NE, ENE, E, ESE, SE, SSE, S, SSW, SW, WSW, W, WNW, NW, NNW  
- **32 divisions**: N1-N8, E1-E8, S1-S8, W1-W8

These are hardcoded in `utils.py` and `views.py` - maintain consistency when modifying directional logic.

### Area Calculation Logic
- Zones measured in inches (width × height)
- Converted to square feet (divide by 144)
- Total area is sum of all zones
- Located in `utils.py::calculate_zonal_areas()` - this is the single source of truth

### Color Coding for Graphs
Different directions have specific colors in generated charts:
- **Blue**: North regions
- **Green**: East regions  
- **Red**: South regions
- **Yellow**: Southwest regions
- **Grey**: West/Northwest regions

Color maps defined in `download_word_blueprint()` and graph generation functions.

### File Paths in Code
- Use `os.path.join(BASE_DIR, ...)` for constructing paths
- MEDIA_ROOT and STATIC_ROOT configured in settings
- Templates directory explicitly set in TEMPLATES config

### Security Considerations
- DEBUG=True in current settings - **must be False in production**
- SECRET_KEY is hardcoded - **move to environment variable**
- Database password visible - **use environment variables**
- Email credentials in settings - **move to environment variables**
- ALLOWED_HOSTS is empty - **configure for production**
- Admin credentials are static in code - **implement proper admin authentication**
