# Session Auth

A minimal authentication and note-taking application built for educational purposes. This project demonstrates **session-based authentication** with server-side session storage.

## 🔐 Authentication Evolution

This is the third version in the authentication learning series:
1. **plain-auth**: Plain text passwords (no security)
2. **bcrypt-auth**: Bcrypt password hashing (secure storage)
3. **session-auth**: Session-based authentication (secure transmission) ← **You are here**

## 🎯 What's New in Session Auth

### Key Improvements:
- ✅ **Session-based authentication** - No more sending passwords with every request
- ✅ **HTTP-only cookies** - Session ID stored securely in cookies
- ✅ **Server-side session storage** - Sessions stored in memory (dictionary)
- ✅ **Session expiration** - Automatic timeout after 24 hours
- ✅ **Bcrypt password hashing** - Passwords remain securely hashed

### What This Solves:
- ❌ **Before**: Client sent email/password with EVERY request (insecure)
- ✅ **Now**: Client logs in once, then uses session ID (secure)

## ⚠️ Warning

**This project is still for educational purposes only!** While it implements proper session management, it still lacks:
- Persistent session storage (sessions lost on server restart)
- CSRF protection
- Rate limiting
- HTTPS enforcement in production
- Comprehensive input validation

**DO NOT use this in production without additional security measures!**

## How Session Authentication Works

### 1. Login Flow
```
Client                          Server                      Memory Storage
  |                               |                               |
  |--POST /login--------------->  |                               |
  |  {email, password}            |                               |
  |                               |--Verify bcrypt password-----> |
  |                               |                               |
  |                               |--Generate session_id--------> |
  |                               |  session_id: abc123           |
  |                               |  email: user@example.com      |
  |                               |  expires_at: 2024-01-02       |
  |                               |                               |
  |<--Set-Cookie: session_id-----|                               |
  |   (HttpOnly, SameSite)        |                               |
```

### 2. Authenticated Request Flow
```
Client                          Server                      Memory Storage
  |                               |                               |
  |--GET /notes---------------->  |                               |
  |  Cookie: session_id=abc123    |                               |
  |                               |                               |
  |                               |--Lookup session_id----------> |
  |                               |<--Return user email---------- |
  |                               |  (if valid & not expired)     |
  |                               |                               |
  |                               |--Query DB with email-------->|
  |<--Return user's notes--------|                               |
```

### 3. Logout Flow
```
Client                          Server                      Memory Storage
  |                               |                               |
  |--POST /logout-------------->  |                               |
  |  Cookie: session_id=abc123    |                               |
  |                               |                               |
  |                               |--Delete session_id----------> |
  |<--Clear Cookie----------------|                               |
```

## Session Storage Structure

### In-Memory Dictionary (Python):
```python
sessions = {
    "abc123xyz": {
        "email": "user@example.com",
        "created_at": datetime(2024, 1, 1, 10, 0, 0),
        "expires_at": datetime(2024, 1, 2, 10, 0, 0)
    },
    "def456uvw": {
        "email": "another@example.com",
        "created_at": datetime(2024, 1, 1, 11, 0, 0),
        "expires_at": datetime(2024, 1, 2, 11, 0, 0)
    }
}
```

### Key Points:
- **Session ID**: Generated using `secrets.token_urlsafe(32)` (cryptographically secure)
- **Storage**: In-memory dictionary (fast, but lost on restart)
- **Expiration**: 24 hours from creation
- **Validation**: Checked on every request
- **Cleanup**: Expired sessions automatically deleted on access

## Features

- 📝 User registration and login
- 📄 Create, read, update, and delete notes
- 💾 SQLite database for data persistence
- 🔐 Session-based authentication with bcrypt password hashing
- 🍪 HTTP-only cookies for session management
- 🎨 Simple, clean UI

## Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: SQLite
- **Password Hashing**: bcrypt
- **Session Storage**: In-memory dictionary
- **Session ID Generation**: secrets module
- **Frontend**: Vanilla HTML/CSS/JavaScript
- **Package Manager**: uv

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd session-auth
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
session-auth/
├── main.py              # FastAPI backend with session management
├── static/
│   └── index.html       # Frontend UI (no localStorage for credentials)
├── users.db             # SQLite database (auto-generated)
├── pyproject.toml       # Project dependencies
└── README.md            # This file
```

## API Endpoints

- `POST /signup` - Register a new user
- `POST /login` - Login and create session (sets cookie)
- `POST /logout` - Logout and destroy session
- `GET /me` - Get current user info from session
- `GET /notes` - Get all notes (session authentication)
- `POST /notes` - Create a new note (session authentication)
- `PUT /notes/{id}` - Update a note (session authentication)
- `DELETE /notes/{id}` - Delete a note (session authentication)

## Code Examples

### Backend: Session Creation
```python
def create_session(email: str) -> str:
    session_id = secrets.token_urlsafe(32)
    sessions[session_id] = {
        "email": email,
        "created_at": datetime.now(),
        "expires_at": datetime.now() + timedelta(hours=24)
    }
    return session_id
```

### Backend: Session Validation
```python
def validate_session(session_id: Optional[str]) -> Optional[str]:
    if not session_id or session_id not in sessions:
        return None
    
    session = sessions[session_id]
    
    # Check expiration
    if datetime.now() > session["expires_at"]:
        del sessions[session_id]
        return None
    
    return session["email"]
```

### Backend: Protected Endpoint
```python
@app.get("/notes")
async def get_notes(session_id: Optional[str] = Cookie(None)):
    email = validate_session(session_id)
    if not email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Fetch notes for authenticated user
    notes = db.query("SELECT * FROM notes WHERE user_email=?", (email,))
    return {"notes": notes}
```

### Frontend: Login Request
```javascript
const res = await fetch('/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password }),
    credentials: 'include'  // Important: sends cookies
});
```

### Frontend: Authenticated Request
```javascript
const res = await fetch('/notes', {
    credentials: 'include'  // Sends session cookie automatically
});
```

## Comparison with Previous Versions

| Feature | plain-auth | bcrypt-auth | session-auth |
|---------|------------|-------------|--------------|
| Password Storage | Plain text | Bcrypt hashed | Bcrypt hashed |
| Authentication Method | Email/password every request | Email/password every request | Session ID (cookie) |
| Credentials in localStorage | Yes (plain text) | Yes (plain text) | No |
| Server Session Storage | No | No | Yes (in-memory) |
| Session Expiration | N/A | N/A | 24 hours |
| Network Security | Very low | Low | Medium |
| Scalability | N/A | N/A | Limited (memory only) |

## Security Improvements Over bcrypt-auth

1. **No More Password in Every Request**
   - Before: `GET /notes?email=user@test.com&password=secret`
   - Now: `GET /notes` (with session cookie)

2. **HTTP-Only Cookies**
   - JavaScript cannot access session ID
   - Protected from XSS attacks

3. **Session Expiration**
   - Automatic logout after 24 hours
   - Old sessions are invalidated

4. **Centralized Session Management**
   - Server can revoke sessions anytime
   - Logout actually destroys the session

## Limitations of In-Memory Sessions

### Pros:
- ✅ Very fast (no database queries)
- ✅ Simple implementation
- ✅ Great for learning and development

### Cons:
- ❌ Lost on server restart
- ❌ Cannot scale horizontally (multiple servers)
- ❌ Memory consumption grows with users
- ❌ No persistence

### Production Alternative:
Use **Redis** or **database tables** for session storage:
```python
# Redis example (not implemented)
import redis
redis_client = redis.Redis(host='localhost', port=6379)
redis_client.setex(session_id, 86400, user_email)
```

## Learning Objectives

This project helps understand:
- How session-based authentication works
- Why sessions are more secure than sending passwords repeatedly
- The role of cookies in web authentication
- Session lifecycle (create, validate, expire, destroy)
- The difference between stateful (sessions) and stateless (JWT) authentication
- Why HTTP-only cookies prevent XSS attacks
- Session storage trade-offs (memory vs database)

## Next Steps

To further improve security, consider:
- **JWT authentication** (stateless, scalable)
- Persistent session storage (Redis/Database)
- CSRF protection
- Rate limiting for login attempts
- HTTPS/TLS encryption
- Session refresh/renewal
- Remember me functionality
- Multi-device session management

## License

MIT

## Previous Versions

- **plain-auth**: Basic authentication without password hashing
- **bcrypt-auth**: Added bcrypt password hashing
- **session-auth**: Added session-based authentication ← **Current**

## Next Version

- **jwt-auth**: JWT token-based authentication (coming soon)