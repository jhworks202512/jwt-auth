from fastapi import FastAPI, HTTPException, Response, Cookie
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import sqlite3
import bcrypt
import secrets
from datetime import datetime, timedelta

app = FastAPI()

# CORS 설정 - 모든 origin 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_PATH = "users.db"

# 세션 저장소 (메모리)
sessions = {}
SESSION_TIMEOUT = timedelta(hours=24)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# DB 초기화: users 테이블 및 notes 테이블 생성
def init_db():
    print("Initializing database...")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # users 테이블 생성 (없으면)
    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    
    # notes 테이블 생성 (없으면)
    c.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            title TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    # 예시 사용자 추가 (이미 존재하면 무시)
    try:
        # bcrypt로 비밀번호 해싱
        hashed_password = bcrypt.hashpw("password123".encode('utf-8'), bcrypt.gensalt())
        c.execute("INSERT INTO users (email, password) VALUES (?, ?)", ("test@example.com", hashed_password.decode('utf-8')))
        conn.commit()
        print("Test user created with hashed password.")
    except sqlite3.IntegrityError:
        print("Test user already exists.")
    
    conn.close()
    print("Database initialized successfully.")

init_db()

# 세션 생성
def create_session(email: str) -> str:
    session_id = secrets.token_urlsafe(32)
    sessions[session_id] = {
        "email": email,
        "created_at": datetime.now(),
        "expires_at": datetime.now() + SESSION_TIMEOUT
    }
    print(f"Session created for {email}: {session_id}")
    return session_id

# 세션 검증
def validate_session(session_id: Optional[str]) -> Optional[str]:
    if not session_id or session_id not in sessions:
        return None
    
    session = sessions[session_id]
    
    # 세션 만료 확인
    if datetime.now() > session["expires_at"]:
        del sessions[session_id]
        print(f"Session expired and deleted: {session_id}")
        return None
    
    return session["email"]

# 세션 삭제
def delete_session(session_id: str):
    if session_id in sessions:
        del sessions[session_id]
        print(f"Session deleted: {session_id}")

# 회원가입
@app.post("/signup")
async def signup(data: dict):
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password required")
    
    # bcrypt로 비밀번호 해싱
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    conn = get_db()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, hashed_password.decode('utf-8')))
        conn.commit()
        conn.close()
        return {"success": True, "message": "Signup successful"}
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=400, detail="Email already exists")

# 로그인
@app.post("/login")
async def login(data: dict, response: Response):
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        raise HTTPException(status_code=400, detail="Email and password required")
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email=?", (email,))
    user = c.fetchone()
    conn.close()
    
    if user and bcrypt.checkpw(password.encode('utf-8'), user["password"].encode('utf-8')):
        # 세션 생성
        session_id = create_session(email)
        # 쿠키에 세션 ID 저장
        response.set_cookie(
            key="session_id",
            value=session_id,
            httponly=True,
            max_age=86400,  # 24시간
            samesite="lax"
        )
        return {"success": True, "message": "Login successful"}
    else:
        raise HTTPException(status_code=401, detail="Invalid credentials")

# 로그아웃
@app.post("/logout")
async def logout(response: Response, session_id: Optional[str] = Cookie(None)):
    if session_id:
        delete_session(session_id)
    response.delete_cookie(key="session_id")
    return {"success": True, "message": "Logged out"}

# 현재 사용자 정보 조회
@app.get("/me")
async def get_current_user(session_id: Optional[str] = Cookie(None)):
    email = validate_session(session_id)
    if not email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"email": email}

# 노트 추가
@app.post("/notes")
async def add_note(data: dict, session_id: Optional[str] = Cookie(None)):
    email = validate_session(session_id)
    if not email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
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

# 노트 조회
@app.get("/notes")
async def get_notes(session_id: Optional[str] = Cookie(None)):
    email = validate_session(session_id)
    if not email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM notes WHERE user_email=? ORDER BY created_at DESC", (email,))
    notes = c.fetchall()
    conn.close()
    
    notes_list = [{"id": note["id"], "title": note["title"], "content": note["content"], 
                   "created_at": note["created_at"]} for note in notes]
    return {"success": True, "notes": notes_list}

# 노트 수정
@app.put("/notes/{note_id}")
async def update_note(note_id: int, data: dict, session_id: Optional[str] = Cookie(None)):
    email = validate_session(session_id)
    if not email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    title = data.get("title")
    content = data.get("content")
    
    if not title or not content:
        raise HTTPException(status_code=400, detail="Title and content required")
    
    conn = get_db()
    c = conn.cursor()
    
    # 해당 노트가 현재 사용자의 것인지 확인
    c.execute("SELECT * FROM notes WHERE id=? AND user_email=?", (note_id, email))
    note = c.fetchone()
    
    if not note:
        conn.close()
        raise HTTPException(status_code=404, detail="Note not found or not authorized")
    
    c.execute("UPDATE notes SET title=?, content=? WHERE id=?", (title, content, note_id))
    conn.commit()
    conn.close()
    return {"success": True, "message": "Note updated"}

# 노트 삭제
@app.delete("/notes/{note_id}")
async def delete_note(note_id: int, session_id: Optional[str] = Cookie(None)):
    email = validate_session(session_id)
    if not email:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    conn = get_db()
    c = conn.cursor()
    
    # 해당 노트가 현재 사용자의 것인지 확인
    c.execute("SELECT * FROM notes WHERE id=? AND user_email=?", (note_id, email))
    note = c.fetchone()
    
    if not note:
        conn.close()
        raise HTTPException(status_code=404, detail="Note not found or not authorized")
    
    c.execute("DELETE FROM notes WHERE id=?", (note_id,))
    conn.commit()
    conn.close()
    return {"success": True, "message": "Note deleted"}

# 정적 파일 서빙 (index.html 등)
app.mount("/", StaticFiles(directory="static", html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)