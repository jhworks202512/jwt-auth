# JWT Auth

A minimal authentication and note-taking application built for educational purposes. This project demonstrates **JWT (JSON Web Token) authentication** with stateless token-based authorization.

## 🔐 Authentication Evolution

This is the fourth version in the authentication learning series:
1. **plain-auth**: Plain text passwords (no security)
2. **bcrypt-auth**: Bcrypt password hashing (secure storage)
3. **session-auth**: Session-based authentication (server-side sessions)
4. **jwt-auth**: JWT token authentication (stateless) ← **You are here**

## 🎯 What's New in JWT Auth

### Key Improvements:
- ✅ **Stateless authentication** - No server-side session storage needed
- ✅ **Access + Refresh tokens** - Short-lived access (15min) + long-lived refresh (7 days)
- ✅ **Self-contained tokens** - User info embedded in the token itself
- ✅ **Horizontal scalability** - Multiple servers can verify tokens independently
- ✅ **localStorage + Bearer header** - Modern token management
- ✅ **Automatic token refresh** - Seamless user experience on token expiration

### What This Solves:
- ❌ **Session Auth**: Sessions lost on server restart, hard to scale
- ✅ **JWT Auth**: No server memory needed, infinitely scalable

## ⚠️ Warning

**This project is still for educational purposes only!** While it implements proper JWT authentication, it still lacks:
- HTTPS enforcement in production
- Secure token storage (vulnerable to XSS if stored in localStorage)
- Token revocation list for immediate logout
- Rate limiting
- Comprehensive input validation

**DO NOT use this in production without additional security measures!**

## How JWT Authentication Works

### JWT Token Structure
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJlbWFpbCI6InRlc3RAZXhhbXBsZS5jb20iLCJleHAiOjE3MDYxMjM0NTZ9.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
│                                      │                                                                │
└────────── Header ────────────────────┴──────────────── Payload ─────────────────────────────────────┴──────── Signature ──────┘

Header:   {"alg": "HS256", "typ": "JWT"}
Payload:  {"email": "test@example.com", "exp": 1706123456, "type": "access"}
Signature: HMACSHA256(base64(header) + "." + base64(payload), SECRET_KEY)
```

### 1. Login Flow
```
Client                          Server                      Database
  |                               |                               |
  |--POST /login--------------->  |                               |
  |  {email, password}            |                               |
  |                               |--Verify bcrypt password-----> |
  |                               |                               |
  |                               |--Generate access_token--------|
  |                               |  (15 min expiration)          |
  |                               |                               |
  |                               |--Generate refresh_token-------|
  |                               |  (7 day expiration)           |
  |                               |                               |
  |                               |--Store refresh_token--------> |
  |                               |  (for logout management)      |
  |                               |                               |
  |<--Return tokens---------------|                               |
  |  {access_token, refresh_token}|                               |
  |                               |                               |
  |--Store in localStorage--------|                               |
```

### 2. Authenticated Request Flow
```
Client                          Server                      Memory
  |                               |                               |
  |--GET /notes---------------->  |                               |
  |  Authorization: Bearer eyJ... |                               |
  |                               |                               |
  |                               |--Verify token signature-----> |
  |                               |  (NO database lookup!)        |
  |                               |                               |
  |                               |--Check expiration-----------> |
  |                               |                               |
  |                               |--Extract email from payload-->|
  |                               |                               |
  |                               |--Query DB with email-------->|
  |<--Return user's notes--------|                               |
```

### 3. Token Refresh Flow
```
Client                          Server                      Database
  |                               |                               |
  |--GET /notes (401)----------> |                               |
  |  (access token expired)       |                               |
  |                               |                               |
  |--POST /refresh------------->  |                               |
  |  {refresh_token}              |                               |
  |                               |                               |
  |                               |--Verify refresh token-------> |
  |                               |                               |
  |                               |--Check DB for token---------> |
  |                               |  (validate not revoked)       |
  |                               |                               |
  |                               |--Generate new access_token----|
  |<--Return new access_token----|                               |
  |                               |                               |
  |--Retry GET /notes----------> |                               |
  |  (with new token)             |                               |
```

### 4. Logout Flow
```
Client                          Server                      Database
  |                               |                               |
  |--POST /logout-------------->  |                               |
  |  Authorization: Bearer eyJ... |                               |
  |                               |                               |
  |                               |--Extract email from token---> |
  |                               |                               |
  |                               |--Delete refresh_token-------> |
  |                               |  (prevent new access tokens)  |
  |                               |                               |
  |<--Success--------------------|                               |
  |                               |                               |
  |--Clear localStorage-----------|                               |
  |  (remove both tokens)         |                               |
```

## JWT vs Session Comparison

| Feature | Session Auth | JWT Auth |
|---------|--------------|----------|
| **Storage** | Server memory/DB | Client localStorage |
| **Scalability** | Difficult (shared storage) | Easy (stateless) |
| **DB Lookup** | Every request | Only on refresh |
| **Server Restart** | Sessions lost | No impact |
| **Immediate Logout** | Yes | No (until token expires) |
| **Token Size** | Small (session ID) | Large (full JWT) |
| **XSS Protection** | Good (HttpOnly cookie) | Vulnerable (localStorage) |
| **Best For** | Traditional web apps | APIs, microservices, mobile |

## Token Storage Structure

### Client Side (localStorage):
```javascript
localStorage = {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",  // 15 min
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." // 7 days
}
```

### Server Side (Database):
```sql
users table:
┌─────────────────────┬──────────────────────────────────┬──────────────┐
│ email               │ password (bcrypt)                │ refresh_token│
├─────────────────────┼──────────────────────────────────┼──────────────┤
│ test@example.com    │ $2b$12$...                      │ eyJhbGci...  │
└─────────────────────┴──────────────────────────────────┴──────────────┘
```

**Important**: Only refresh tokens are stored in the database for logout management. Access tokens are never stored server-side!

## Features

- 📝 User registration and login
- 📄 Create, read, update, and delete notes
- 💾 SQLite database for data persistence
- 🔐 JWT-based authentication with bcrypt password hashing
- 🔄 Automatic token refresh on expiration
- 🎨 Simple, clean UI
- 🚀 Stateless and horizontally scalable

## Tech Stack

- **Backend**: FastAPI (Python)
- **Database**: SQLite
- **Password Hashing**: bcrypt
- **JWT Library**: PyJWT
- **Token Storage**: localStorage (client)
- **Authorization**: Bearer token in headers
- **Frontend**: Vanilla HTML/CSS/JavaScript
- **Package Manager**: uv

## Installation

1. Clone the repository:
```bash
git clone https://github.com/jhworks202512/jwt-auth.git
cd jwt-auth
```

2. Install dependencies using uv:
```bash
uv add fastapi uvicorn bcrypt PyJWT
```

## Usage

1. Run the server:
```bash
uv run python main.py
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
jwt-auth/
├── main.py              # FastAPI backend with JWT authentication
├── static/
│   └── index.html       # Frontend UI with JWT token management
├── users.db             # SQLite database (auto-generated)
├── pyproject.toml       # Project dependencies
└── README.md            # This file
```

## API Endpoints

### Authentication
- `POST /signup` - Register a new user
- `POST /login` - Login and receive JWT tokens
- `POST /refresh` - Refresh access token using refresh token
- `POST /logout` - Logout and invalidate refresh token
- `GET /me` - Get current user info from JWT

### Notes (Protected)
- `GET /notes` - Get all notes (JWT required)
- `POST /notes` - Create a new note (JWT required)
- `PUT /notes/{id}` - Update a note (JWT required)
- `DELETE /notes/{id}` - Delete a note (JWT required)

## Code Examples

### Backend: JWT Token Creation
```python
def create_access_token(email: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=15)
    payload = {
        "email": email,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")
```

### Backend: JWT Token Verification
```python
def verify_token(token: str, token_type: str = "access") -> Optional[str]:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
        
        if payload.get("type") != token_type:
            return None
        
        return payload.get("email")
    
    except jwt.ExpiredSignatureError:
        return None
    except PyJWTError:
        return None
```

### Backend: Protected Endpoint
```python
def get_current_user_email(authorization: Optional[str] = Header(None)) -> str:
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    token = authorization.split()[1]  # Extract from "Bearer {token}"
    email = verify_token(token, token_type="access")
    
    if not email:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return email

@app.get("/notes")
async def get_notes(email: str = Depends(get_current_user_email)):
    # Email is automatically extracted from JWT token!
    notes = db.query("SELECT * FROM notes WHERE user_email=?", (email,))
    return {"notes": notes}
```

### Frontend: Login and Token Storage
```javascript
const res = await fetch('/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password })
});

const data = await res.json();

// Store tokens in localStorage
localStorage.setItem('access_token', data.access_token);
localStorage.setItem('refresh_token', data.refresh_token);
```

### Frontend: Authenticated Request
```javascript
const accessToken = localStorage.getItem('access_token');

const res = await fetch('/notes', {
    headers: {
        'Authorization': `Bearer ${accessToken}`
    }
});

if (res.status === 401) {
    // Token expired, refresh it
    await refreshAccessToken();
}
```

### Frontend: Automatic Token Refresh
```javascript
async function refreshAccessToken() {
    const refreshToken = localStorage.getItem('refresh_token');
    
    const res = await fetch('/refresh', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: refreshToken })
    });
    
    if (res.ok) {
        const data = await res.json();
        localStorage.setItem('access_token', data.access_token);
        return true;
    }
    
    // Refresh token expired, redirect to login
    return false;
}
```

## Security Considerations

### ✅ What's Secure:
1. **Bcrypt password hashing** - Passwords never stored in plain text
2. **Short-lived access tokens** - 15 minutes limits damage if stolen
3. **Signed tokens** - Cannot be tampered with without SECRET_KEY
4. **Refresh token in DB** - Can be revoked on logout

### ⚠️ Potential Vulnerabilities:
1. **XSS attacks** - localStorage accessible by JavaScript
2. **Token theft** - If access token is stolen, valid for 15 minutes
3. **No token blacklist** - Logout doesn't invalidate existing access tokens
4. **SECRET_KEY in code** - Should be in environment variables

### 🔒 Production Recommendations:
1. Use **HttpOnly cookies** for tokens (if same-domain)
2. Implement **token blacklist** (Redis) for immediate revocation
3. Store **SECRET_KEY in environment variables**
4. Use **HTTPS only** in production
5. Add **CSRF protection** if using cookies
6. Implement **rate limiting** on auth endpoints
7. Consider **IP-based validation** for additional security

## Why Two Tokens?

### Access Token (15 minutes):
- Short-lived for security
- Used for every API request
- If stolen, expires quickly
- NOT stored in database

### Refresh Token (7 days):
- Long-lived for convenience
- Used only to get new access tokens
- Stored in database (can be revoked)
- Only sent to `/refresh` endpoint

This pattern balances **security** (short access tokens) with **user experience** (no frequent logins).

## Advantages Over Session Auth

1. **Stateless**: No server memory needed
2. **Scalable**: Multiple servers work independently
3. **Cross-domain**: Easy to use with different domains
4. **Mobile-friendly**: No cookie management issues
5. **Microservices**: Each service can verify tokens
6. **Performance**: No database lookup on every request

## Disadvantages Compared to Session Auth

1. **Logout delay**: Access tokens valid until expiration
2. **Token size**: Larger than session IDs
3. **XSS vulnerability**: localStorage accessible to scripts
4. **Cannot modify**: Can't change token data until refresh
5. **Bandwidth**: Full token sent with every request

## Learning Objectives

This project helps understand:
- How JWT tokens work (structure, signing, verification)
- The difference between access and refresh tokens
- Stateless vs stateful authentication
- Token-based authorization headers
- Automatic token refresh patterns
- Trade-offs between sessions and JWTs
- Why JWTs are popular in modern APIs

## Comparison with Previous Versions

| Feature | plain-auth | bcrypt-auth | session-auth | jwt-auth |
|---------|------------|-------------|--------------|----------|
| Password Storage | Plain text | Bcrypt | Bcrypt | Bcrypt |
| Auth Method | Every request | Every request | Session cookie | JWT token |
| Server Storage | No | No | Yes (memory) | No |
| Scalability | N/A | N/A | Limited | Excellent |
| Logout | N/A | N/A | Immediate | Delayed (15min) |
| Mobile Support | Poor | Poor | Fair | Excellent |
| API-friendly | No | No | Fair | Excellent |

## Next Steps

To further improve this implementation:
- Move SECRET_KEY to environment variables
- Implement token blacklist (Redis)
- Add refresh token rotation
- Consider HttpOnly cookies for web apps
- Add rate limiting
- Implement IP validation
- Add comprehensive logging
- Create admin dashboard for token management

## License

MIT

## Previous Versions

- **plain-auth**: Basic authentication without password hashing
- **bcrypt-auth**: Added bcrypt password hashing
- **session-auth**: Added session-based authentication
- **jwt-auth**: JWT token-based authentication ← **Current**

## Repository

https://github.com/jhworks202512/jwt-auth