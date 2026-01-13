# Simple Auth Notes

A minimal authentication and note-taking application built for educational purposes. This project demonstrates basic email/password authentication without using sessions or JWT tokens.

## ⚠️ Warning

**This project is for educational purposes only!** It deliberately does not implement security best practices:
- Passwords are stored in plain text
- Authentication credentials are sent with every request
- No CSRF protection
- No rate limiting
- No input validation/sanitization

**DO NOT use this in production!**

## Features

- 📝 User registration and login
- 📄 Create, read, update, and delete notes
- 💾 SQLite database for data persistence
- 🔐 Basic email/password authentication (no sessions/JWT)
- 🎨 Simple, clean UI

## Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: SQLite
- **Frontend**: Vanilla HTML/CSS/JavaScript
- **Package Manager**: uv

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd test2
```

2. Install dependencies using uv:
```bash
uv pip install fastapi uvicorn
```

## Usage

1. Run the server:
```bash
uv run main.py
```

2. Open your browser and navigate to:
```
http://localhost:8000
```

3. Register a new account or use the test account:
   - Email: `test@example.com`
   - Password: `password123`

## Project Structure

```
test2/
├── main.py              # FastAPI backend application
├── static/
│   └── index.html       # Frontend UI
├── users.db             # SQLite database (auto-generated)
├── pyproject.toml       # Project dependencies
└── README.md            # This file
```

## API Endpoints

- `POST /signup` - Register a new user
- `POST /login` - Verify login credentials
- `GET /notes` - Get all notes for authenticated user
- `POST /notes` - Create a new note
- `PUT /notes/{id}` - Update an existing note
- `DELETE /notes/{id}` - Delete a note

## Authentication Flow

1. User enters email and password
2. Credentials are stored in `localStorage`
3. Every API request includes email and password
4. Server validates credentials for each request
5. On 401 error, user is automatically logged out

## License

MIT

## Learning Objectives

This project helps understand:
- Basic REST API design
- FastAPI framework basics
- SQLite database operations
- Client-side state management
- Why proper authentication (sessions/JWT) is important