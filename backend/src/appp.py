from fastapi import FastAPI, HTTPException, status, Request, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from typing import Optional
import os
import logging
import re
import sqlite3
import bcrypt
import uuid
from dotenv import load_dotenv
from groq import Groq
from slowapi import Limiter
from slowapi.util import get_remote_address
from src.ragi import get_context_for_query
from src.context_manager import get_history, add_message, clear_history

# --- Load environment variables ---
load_dotenv(override=True)

# --- FastAPI app ---
app = FastAPI(
    title="Asha AI Chatbot",
    description="Career assistant for women's professional growth",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None
)

# --- Rate limiting ---
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

# --- CORS middleware ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "https://asha-ai-bot-63eo.onrender.com").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("AshaAI")

# --- Environment variable checks ---
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()

# --- Database setup ---
DB_PATH = os.getenv("DB_PATH", "users.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                rating TEXT NOT NULL,
                comments TEXT
            )
        ''')
        conn.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
        conn.commit()

init_db()

# --- Groq client ---
try:
    groq_client = Groq(api_key=GROQ_API_KEY, timeout=10.0)
except Exception as e:
    logger.critical("Groq client initialization failed: %s", str(e))
    raise RuntimeError("AI service initialization failed") from e

# --- Models ---
class ChatRequest(BaseModel):
    session_id: str
    message: str
    location: Optional[str] = ""

class FeedbackRequest(BaseModel):
    session_id: str
    rating: str
    comments: Optional[str] = None

class SignupRequest(BaseModel):
    name: str
    email: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

# --- Security ---
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

# --- Bias & Ambiguity Detection ---
AMBIGUOUS_TERMS = {
    "bank": ["financial institution", "river bank"],
    "python": ["programming language", "snake"],
    "java": ["programming language", "island"],
    "coach": ["mentor", "vehicle"],
    "tablet": ["medicine", "electronic device"]
}

def detect_ambiguity(query: str) -> str:
    query_lower = query.lower()
    for term, meanings in AMBIGUOUS_TERMS.items():
        if term in query_lower:
            return f"I noticed you mentioned '{term}'. Did you mean: {', '.join(meanings)}?"
    return ""

def analyze_bias(query: str) -> Optional[str]:
    lower = query.lower()
    if "men only" in lower or "male only" in lower:
        return "Asha AI is inclusive and does not filter jobs by gender. Please specify your skills or interests."
    if "age" in lower or "young people" in lower or "old people" in lower:
        return "Asha AI does not filter jobs by age. Please specify your skills or interests."
    return None

@app.get("/")
async def index():
    return "Asha's backend working."

@app.middleware("http")
async def add_correlation_id(request: Request, call_next):
    correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
    request.state.correlation_id = correlation_id
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response

# --- Chat endpoint ---
@app.post("/chat")
@limiter.limit("10/minute")
async def handle_chat(request: Request, chat_request: ChatRequest):
    try:
        logger.info(f"Chat request - Session: {chat_request.session_id}")
        
        clarification = detect_ambiguity(chat_request.message)
        if clarification:
            add_message(chat_request.session_id, "bot", clarification)
            return {
                "reply": clarification,
                "history": get_history(chat_request.session_id),
                "requires_clarification": True
            }

        bias_msg = analyze_bias(chat_request.message)
        if bias_msg:
            add_message(chat_request.session_id, "bot", bias_msg)
            return {
                "reply": bias_msg,
                "history": get_history(chat_request.session_id),
                "bias_detected": True
            }

        context = await run_in_threadpool(get_context_for_query, chat_request.message, chat_request.location)

        response = await run_in_threadpool(
            groq_client.chat.completions.create,
            messages=[ 
                {"role": "system", "content": f"""You are Asha AI, a career assistant. Use this context:\n{context}\n\nResponse rules:\n1. Use markdown for lists/links\n2. Keep responses under 150 words\n3. Ask follow-up questions"""}, 
                {"role": "user", "content": chat_request.message}
            ],
            model="llama3-8b-8192",
            temperature=0.7,
            max_tokens=500
        )
        
        reply = response.choices[0].message.content
        add_message(chat_request.session_id, "bot", reply)
        
        return {
            "reply": reply,
            "history": get_history(chat_request.session_id)
        }
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}", exc_info=True)
        return {"reply": "I'm having technical difficulties. Please try again later."}

# --- Signup endpoint ---
@app.post("/signup")
@limiter.limit("5/minute")
async def handle_signup(request: Request, signup_request: SignupRequest):
    try:
        if not re.match(r"[^@]+@[^@]+\.[^@]+", signup_request.email):
            raise HTTPException(status_code=400, detail="Invalid email format")

        def signup_user():
            with get_db_connection() as conn:
                existing = conn.execute("SELECT * FROM users WHERE email = ?", (signup_request.email,)).fetchone()
                if existing:
                    raise HTTPException(status_code=400, detail="Email already registered")
                conn.execute(
                    "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
                    (signup_request.name, signup_request.email, hash_password(signup_request.password))
                )
                conn.commit()

        await run_in_threadpool(signup_user)
        return {"success": True, "message": "Signup successful"}
        
    except sqlite3.Error as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error")

# --- Login endpoint ---
@app.post("/login")
@limiter.limit("10/minute")
async def handle_login(request: Request, login_request: LoginRequest):
    try:
        def login_user():
            with get_db_connection() as conn:
                user = conn.execute("SELECT * FROM users WHERE email = ?", (login_request.email,)).fetchone()
                return user

        user = await run_in_threadpool(login_user)
        
        if not user or not verify_password(login_request.password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Invalid credentials")
            
        return {"success": True, "message": "Login successful"}
        
    except sqlite3.Error as e:
        logger.error(f"Database error: {str(e)}")
        raise HTTPException(status_code=500, detail="Database error")

# --- Feedback endpoint ---
@app.post("/feedback")
async def handle_feedback(feedback_request: FeedbackRequest):
    try:
        with get_db_connection() as conn:
            conn.execute(
                "INSERT INTO feedback (session_id, rating, comments) VALUES (?, ?, ?)",
                (feedback_request.session_id, feedback_request.rating, feedback_request.comments)
            )
            conn.commit()
        return {"success": True, "message": "Thank you for your feedback!"}
    except sqlite3.Error as e:
        logger.error(f"Feedback DB error: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not submit feedback")
