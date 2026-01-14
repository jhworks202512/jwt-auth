from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import sqlite3
import bcrypt
import secrets
from datetime import datetime, timedelta
import jwt
from jwt import PyJWTError

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "users.db"

# JWT 설정
SECRET_KEY = secrets.token_urlsafe(32)  # 프로덕션에서는 환경변수로 관리
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 15  # 액세스 토큰: 15분
REFRESH_TOKEN_EXPIRE_DAYS = 7     # 리프레시 토큰: 7일

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# DB 초기화
def init_db():
    print("Initializing database...")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # users 테이블 생성 (refresh_token 컬럼 추가)
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            refresh_token TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # notes 테이블 생성
    c.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 예시 사용자 추가
    try:
        hashed_password = bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt())
        c.execute("INSERT INTO users (email, password) VALUES (?, ?)", 
                  ("test@example.com", hashed_password.decode('utf-8')))
        conn.commit()
        print("Test user created.")
    except sqlite3.IntegrityError:
        print("Test user already exists.")
    
    conn.close()
    print("Database initialized successfully.")

init_db()

# JWT 유틸리티 함수
def create_access_token(email: str) -> str:
    """액세스 토큰 생성 (15분)"""
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "email": email,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

def create_refresh_token(email: str) -> str:
    """리프레시 토큰 생성 (7일)"""
    expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "email": email,
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    }
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

def verify_token(token: str, token_type: str = "access") -> Optional[str]:
    """JWT 토큰 검증"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        if payload.get("type") != token_type:
            return None
        
        email: str = payload.get("email")
        if email is None:
            return None
        
        return email
    
    except jwt.ExpiredSignatureError:
        print("Token expired")
        return None
    
    except PyJWTError as e:
        print(f"Token verification failed: {e}")
        return None

def get_current_user_email(authorization: Optional[str] = Header(None)) -> str:
    """Authorization 헤더에서 토큰 추출 및 검증"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")
    
    parts = authorization.split()
    
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
    
    token = parts[1]
    email = verify_token(token, token_type="access")
    
    if not email:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    return email

# ===================================
# 인증 관련 API
# ===================================

@app.post("/signup")
async def signup(data: dict):
    """회원가입"""
    email = data.get("email")
    password = data.get("password")
    
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password required")
    
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (email, password) VALUES (?, ?)", 
                  (email, hashed_password.decode('utf-8')))
        conn.commit()
        conn.close()
        return {"success": True, "message": "Signup successful"}
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Email already exists")

@app.post("/login")
async def login(data: dict):
    """로그인 - JWT 토큰 발급"""
    email = data.get("email")
    password = data.get("password")
    
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password required")
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email=?", (email,))
    user = c.fetchone()
    
    if not user or not bcrypt.checkpw(password.encode('utf-8'), user["password"].encode('utf-8')):
        conn.close()
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    # JWT 토큰 생성
    access_token = create_access_token(email)
    refresh_token = create_refresh_token(email)
    
    # 리프레시 토큰을 DB에 저장
    c.execute("UPDATE users SET refresh_token=? WHERE email=?", (refresh_token, email))
    conn.commit()
    conn.close()
    
    print(f"Login successful for {email}")
    
    return {
        "success": True,
        "message": "Login successful",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

@app.post("/refresh")
async def refresh_access_token(data: dict):
    """액세스 토큰 재발급"""
    refresh_token = data.get("refresh_token")
    
    if not refresh_token:
        raise HTTPException(status_code=400, detail="Refresh token required")
    
    # 리프레시 토큰 검증
    email = verify_token(refresh_token, token_type="refresh")
    if not email:
        raise HTTPException(status_code=401, detail="Invalid or expired refresh token")
    
    # DB에 저장된 리프레시 토큰과 비교
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT refresh_token FROM users WHERE email=?", (email,))
    user = c.fetchone()
    conn.close()
    
    if not user or user["refresh_token"] != refresh_token:
        raise HTTPException(status_code=401, detail="Refresh token not found or revoked")
    
    # 새로운 액세스 토큰 발급
    new_access_token = create_access_token(email)
    
    print(f"Access token refreshed for {email}")
    
    return {
        "success": True,
        "access_token": new_access_token,
        "token_type": "bearer"
    }

@app.post("/logout")
async def logout(email: str = Depends(get_current_user_email)):
    """로그아웃 - DB에서 리프레시 토큰 삭제"""
    conn = get_db()
    c = conn.cursor()
    c.execute("UPDATE users SET refresh_token=NULL WHERE email=?", (email,))
    conn.commit()
    conn.close()
    
    print(f"Logout successful for {email}")
    
    return {"success": True, "message": "Logged out"}

@app.get("/me")
async def get_current_user(email: str = Depends(get_current_user_email)):
    """현재 인증된 사용자 정보 조회"""
    return {"email": email}

# ===================================
# 노트 관련 API
# ===================================

@app.post("/notes")
async def add_note(data: dict, email: str = Depends(get_current_user_email)):
    """노트 추가"""
    title = data.get("title")
    content = data.get("content")
    
    if not title or not content:
        raise HTTPException(status_code=400, detail="Title and content required")
    
    conn = get_db()
    c = conn.cursor()
    c.execute("INSERT INTO notes (user_email, title, content) VALUES (?, ?, ?)", 
              (email, title, content))
    conn.commit()
    note_id = c.lastrowid
    conn.close()
    
    return {"success": True, "message": "Note added", "note_id": note_id}

@app.get("/notes")
async def get_notes(email: str = Depends(get_current_user_email)):
    """노트 조회"""
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM notes WHERE user_email=? ORDER BY created_at DESC", (email,))
    notes = c.fetchall()
    conn.close()
    
    notes_list = [
        {
            "id": note["id"],
            "title": note["title"],
            "content": note["content"],
            "created_at": note["created_at"]
        }
        for note in notes
    ]
    
    return {"success": True, "notes": notes_list}

@app.put("/notes/{note_id}")
async def update_note(note_id: int, data: dict, email: str = Depends(get_current_user_email)):
    """노트 수정"""
    title = data.get("title")
    content = data.get("content")
    
    if not title or not content:
        raise HTTPException(status_code=400, detail="Title and content required")
    
    conn = get_db()
    c = conn.cursor()
    
    c.execute("SELECT * FROM notes WHERE id=? AND user_email=?", (note_id, email))
    note = c.fetchone()
    
    if not note:
        conn.close()
        raise HTTPException(status_code=404, detail="Note not found or not authorized")
    
    c.execute("UPDATE notes SET title=?, content=? WHERE id=?", (title, content, note_id))
    conn.commit()
    conn.close()
    
    return {"success": True, "message": "Note updated"}

@app.delete("/notes/{note_id}")
async def delete_note(note_id: int, email: str = Depends(get_current_user_email)):
    """노트 삭제"""
    conn = get_db()
    c = conn.cursor()
    
    c.execute("SELECT * FROM notes WHERE id=? AND user_email=?", (note_id, email))
    note = c.fetchone()
    
    if not note:
        conn.close()
        raise HTTPException(status_code=404, detail="Note not found or not authorized")
    
    c.execute("DELETE FROM notes WHERE id=?", (note_id,))
    conn.commit()
    conn.close()
    
    return {"success": True, "message": "Note deleted"}

# 정적 파일 서빙
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)