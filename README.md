# CampusConnect

Student networking platform developed using Git, GitHub and DevOps practices.

CampusConnect is a Flask-based REST API that lets students register, create profiles and showcase their skills. It was built as a team project to practice real-world software development workflows: feature branches, issue tracking, pull requests with peer review, and continuous integration.

## Features

- **Home route:** confirms the API is running
- **Register:** user registration with input validation (name and email required)
- **Profiles:** create and view student profiles (name, skills, specialization, bio)
- **Automated tests:** written with pytest
- **CI pipeline:** GitHub Actions runs all tests on every push and pull request

## Tech Stack

- Python 3.11
- Flask
- pytest
- Git and GitHub
- GitHub Actions

## Project Structure

```
campus-connect-f/
├── .github/workflows/ci.yml   # CI workflow
├── routes/
│   ├── auth.py                # register route
│   └── profile.py             # profile routes
├── tests/                     # pytest test files
├── app.py                     # Flask app entry point
├── conftest.py
└── requirements.txt
```

## Getting Started

1. Clone the repository:
```bash
   git clone https://github.com/Vanditamehta/campus-connect-f.git
   cd campus-connect-f
```
2. Install dependencies:
```bash
   pip install -r requirements.txt
```
3. Run the app:
```bash
   python app.py
```
4. Run the tests:
```bash
   pytest
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Check that the API is running |
| POST | `/register` | Register a new user (`name`, `email`) |
| POST | `/profile` | Create a profile (`name`, `skills`, optional `specialization`, `bio`) |
| GET | `/profile/<id>` | View a profile by ID |

## Team and Responsibilities

| Member | Responsibility | Branch |
|--------|----------------|--------|
| Vandita Mehta | Project setup, CI pipeline, register feature | `feature/auth` |
| Bhavini | Profile feature | `feature/profile` |
| Dhruvi | Testing and blog feature | `feature/blog` |

## Git Workflow Followed

1. Repository created on GitHub, and teammates added as collaborators
2. Tasks divided and tracked using **GitHub Issues**
3. Each feature built on its own **branch**, with small commits and clear messages
4. Changes merged into `main` through **pull requests**, reviewed by a teammate
5. **GitHub Actions** ran the tests automatically on every push and pull request

## Known Limitations

Data is stored in in-memory lists, so it resets when the server restarts. Moving to a SQLite database is the planned next step.
