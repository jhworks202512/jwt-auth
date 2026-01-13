# Bcrypt Auth

A minimal authentication and note-taking application built for educational purposes. This project demonstrates email/password authentication with **bcrypt password hashing**.

## 🔐 Security Improvements

This version improves upon the plain-auth version by implementing:
- ✅ **Bcrypt password hashing** - Passwords are hashed before storage
- ✅ **Salt generation** - Each password gets a unique salt
- ✅ **Secure password verification** - Uses bcrypt.checkpw() for comparison

## ⚠️ Warning

**This project is still for educational purposes only!** While it implements password hashing, it still lacks:
- Session management or JWT tokens
- CSRF protection
- Rate limiting
- Comprehensive input validation/sanitization
- HTTPS enforcement

**DO NOT use this in production without additional security measures!**

## Features

- 📝 User registration and login
- 📄 Create, read, update, and delete notes
- 💾 SQLite database for data persistence
- 🔐 Email/password authentication with bcrypt hashing
- 🎨 Simple, clean UI

## Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: SQLite
- **Password Hashing**: bcrypt
- **Frontend**: Vanilla HTML/CSS/JavaScript
- **Package Manager**: uv

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd bcrypt-auth
```

2. Install dependencies using uv:
```bash
uv pip install fastapi uvicorn bcrypt
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
bcrypt-auth/
├── main.py              # FastAPI backend with bcrypt hashing
├── static/
│   └── index.html       # Frontend UI
├── users.db             # SQLite database (auto-generated)
├── pyproject.toml       # Project dependencies
└── README.md            # This file
```

## API Endpoints

- `POST /signup` - Register a new user (password is hashed with bcrypt)
- `POST /login` - Verify login credentials (compares hashed passwords)
- `GET /notes` - Get all notes for authenticated user
- `POST /notes` - Create a new note
- `PUT /notes/{id}` - Update an existing note
- `DELETE /notes/{id}` - Delete a note

## Authentication Flow

1. **Signup**: User enters email and password → Password is hashed with bcrypt → Stored in database
2. **Login**: User enters credentials → Server retrieves hashed password → bcrypt.checkpw() verifies match
3. **Requests**: Client sends email/password with each request → Server verifies against hashed password
4. **Logout**: On 401 error, credentials are cleared from localStorage

## Bcrypt Implementation

### Password Hashing (Signup)
```python
hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
# Stored as: $2b$12$... (60 characters)
```

### Password Verification (Login)
```python
bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8'))
# Returns True if password matches
```

## Comparison with plain-auth

| Feature | plain-auth | bcrypt-auth |
|---------|------------|-------------|
| Password Storage | Plain text | Bcrypt hashed |
| Database Compromise | All passwords exposed | Passwords protected |
| Rainbow Table Attack | Vulnerable | Protected by salt |
| Brute Force Difficulty | Easy | Significantly harder |

## Learning Objectives

This project helps understand:
- How bcrypt protects passwords with hashing and salting
- Why storing plain text passwords is dangerous
- Basic implementation of password hashing in Python
- The difference between encryption and hashing
- How to verify passwords without storing them in plain text

## Next Steps

To further improve security, consider:
- Implementing JWT or session-based authentication
- Adding rate limiting for login attempts
- Implementing password strength requirements
- Adding HTTPS/TLS encryption
- Implementing CSRF protection
- Adding email verification

## License

MIT

## Previous Version

- **plain-auth**: Basic authentication without password hashing