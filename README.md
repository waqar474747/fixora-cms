# Complaint System Project Setup and Run Instructions

This document provides the necessary steps to set up and run the Complaint System project, which has been reorganized to place all application-specific files (apps, templates, static, media) within an `app/` directory.

## Project Structure

The project follows a standard Django structure with a dedicated `app/` directory for all reusable components:

```
complaint_system_project/
├── app/
│   ├── accounts/         # User authentication app
│   ├── complaints/       # Complaint management app
│   ├── dashboard/        # User and admin dashboard app
│   ├── templates/        # Global templates
│   ├── static/           # Global static files
│   ├── media/            # User-uploaded media files
│   └── __init__.py
├── complaint_system/     # Project settings and configuration
│   ├── settings.py
│   ├── urls.py
│   └── ...
├── manage.py             # Django's command-line utility
└── requirements.txt      # Python dependencies
```

## Setup Instructions

Follow these steps to get the project running on your local machine.

### 1. Prerequisites

Ensure you have the following installed:
*   **Python 3.8+**
*   **pip** (Python package installer)

### 2. Virtual Environment

It is highly recommended to use a virtual environment to manage project dependencies.

```bash
# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
# On Linux/macOS:
source venv/bin/activate
# On Windows (Command Prompt):
# venv\Scripts\activate
# On Windows (PowerShell):
# venv\Scripts\Activate.ps1
```

### 3. Install Dependencies

Install all required Python packages using the provided `requirements.txt` file.

```bash
pip install -r requirements.txt
```

### 4. Database Migrations

Apply the database migrations to set up the necessary tables.

```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create Superuser (Admin Account)

Create an administrative user to access the Django admin interface and the admin dashboard.

```bash
python manage.py createsuperuser
```

Follow the prompts to set a username, email, and password.

### 6. Run the Development Server

Start the Django development server.

```bash
python manage.py runserver
```

The application will be accessible at: `http://127.0.0.1:8000/`

### 7. Access Points

*   **Home Page:** `http://127.0.0.1:8000/`
*   **User Registration:** `http://127.0.0.1:8000/accounts/register/`
*   **User Login:** `http://127.0.0.1:8000/accounts/login/`
*   **Admin Interface:** `http://127.0.0.1:8000/admin/` (Use the superuser credentials)
*   **Dashboard:** `http://127.0.0.1:8000/dashboard/` (Requires login)

---

