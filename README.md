CampusConnect – Student Networking Platform

CampusConnect is a student networking web application that enables college students to create profiles, share posts, discover other students, and build connections within their campus community.

Live Application: https://campus-connect-f.onrender.com
GitHub Repository: https://github.com/Vanditamehta/campus-connect-f

1. Project Objectives
Provide a centralised platform for student networking.
Enable students to create and manage profiles.
Support sharing posts and updates.
Help students discover and connect with peers.
Apply software development and DevOps practices.
2. Key Features
User registration and login.
Student profile creation and editing.
Posts and activity feed.
Student discovery.
Connection management.
Responsive web interface.
3. Technology Stack
Component	Technology
Frontend	HTML, CSS, 
Template Engine	Jinja2
Backend	Python 3.11, Flask
Database	PostgreSQL, SQLite (local development)
SQLAlchemy
Image Storage	Cloudinary
Testing	pytest
Version Control	Git
Repository Hosting	GitHub
Continuous Integration	GitHub Actions
Application Hosting	Render
4. Project Structure
campus-connect-f/
│
├── app.py
├── config.py
├── extensions.py
├── models.py
├── requirements.txt
│
├── routes/
│   ├── __init__.py
│   ├── auth.py
│   ├── profile.py
│   ├── posts.py
│   ├── connections.py
│   └── main.py
│
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── feed.html
│   ├── profile.html
│   ├── edit_profile.html
│   ├── people.html
│   └── connections.html
│
├── static/
│   └── css/
│       └── style.css
│
├── tests/
│   ├── conftest.py
│   ├── test_basic.py
│   ├── test_auth.py
│   ├── test_profile.py
│   ├── test_posts.py
│   └── test_connections.py
│
└── .github/
    └── workflows/
        └── ci.yml

Directory Overview
File / Directory	Description
app.py	Main Flask application entry point.
config.py	Application and environment configuration.
extensions.py	Initialisation of Flask extensions.
models.py	Database models.
requirements.txt	Project dependencies.
routes/	Backend routes organised by functionality.
templates/	HTML and Jinja templates.
static/	Static assets and stylesheets.
tests/	Automated test cases.
.github/workflows/ci.yml	GitHub Actions CI configuration.
5. Installation and Setup
Python 3.11
Git
Visual Studio Code
Clone the Repository
bash
git clone https://github.com/Vanditamehta/campus-connect-f.git
cd campus-connect-f

Create and Activate Virtual Environment
bash
python3 -m venv .venv
source .venv/bin/activate


For Windows:

bash
.venv\Scripts\activate

Install Dependencies
bash
pip install -r requirements.txt

Configure Environment Variables

Configure the required environment variables for the application, including database credentials, Flask secret key, and Cloudinary credentials.

Sensitive credentials should not be committed to the repository.

Run the Application
bash
python app.py


6. Testing

The project uses pytest for automated testing.

Test files are organised by application functionality:

test_basic.py – Basic application tests.
test_auth.py – Authentication tests.
test_profile.py – Profile tests.
test_posts.py – Post-related tests.
test_connections.py – Connection-related tests.

Run all tests:

bash
pytest -v


Run a specific test file:

bash
pytest tests/test_auth.py

7. DevOps and SCM

The project incorporates DevOps practices to improve code management, testing, and application delivery.

Source Code Management: Git and GitHub are used for version control, commits, branching, and collaboration.
Continuous Integration: GitHub Actions automates the configured checks and test execution on repository events.
Automated Testing: pytest validates application functionality and helps identify errors early.
Deployment: Render is used to host and deploy the web application.

The CI workflow is maintained in:

text
.github/workflows/ci.yml

8. Security and Configuration
Environment variables are used to manage sensitive configuration.
Flask secret key supports secure session management.
CSRF protection is used for supported form submissions.
PostgreSQL is configured for production data storage.
Cloudinary provides external image storage.
9. Future Enhancements
Advanced student discovery and filtering.
Improved networking and collaboration features.
Additional notification options.
Expanded automated test coverage.
Performance monitoring and accessibility improvements.
10. Conclusion

CampusConnect demonstrates the development of a student networking platform using Flask and modern web technologies. The project also applies Software Configuration Management, automated testing, Continuous Integration, and cloud hosting practices to support a structured software development workflow.