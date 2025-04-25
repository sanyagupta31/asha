# src/appp.py (Final Production-Ready Version)
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os
import logging
import re
from dotenv import load_dotenv

load_dotenv(override=True)  # Always reload .env

# Check for all API keys
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID", "").strip()
ADZUNA_APP_KEY = os.getenv("ADZUNA_APP_KEY", "").strip()
TICKETMASTER_API_KEY = os.getenv("TICKETMASTER_API_KEY", "").strip()

print(f"Loaded GROQ_API_KEY: {repr(GROQ_API_KEY)}")
print(f"Loaded ADZUNA_APP_ID: {repr(ADZUNA_APP_ID)}")

if not GROQ_API_KEY or not GROQ_API_KEY.startswith("gsk_"):
    raise ValueError("Invalid/Missing Groq API key in .env file")

# Import modules AFTER env validation
from src.context_manager import get_history, add_message, clear_history
from src.ragi import get_context_for_query
from src.ethical import analyze_ethical_concerns
from src.feedback import record_feedback
from src.security import encrypt_data
from src.analytics import log_analytics
from groq import Groq

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("AshaAI")

# Initialize Groq client
try:
    client = Groq(
        api_key=GROQ_API_KEY,
        timeout=10.0
    )
except Exception as e:
    logger.critical("Groq client initialization failed: %s", str(e))
    raise RuntimeError("AI service initialization failed") from e

# FastAPI app
app = FastAPI(
    title="Asha AI Chatbot",
    description="Career assistant for women's professional growth",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None
)

# Data models
class ChatRequest(BaseModel):
    session_id: str
    message: str
    location: Optional[str] = ""

class FeedbackRequest(BaseModel):
    session_id: str
    rating: str
    comments: Optional[str] = None

# Ambiguity detection patterns
AMBIGUOUS_TERMS = {
    "bank": ["financial institution", "river bank"],
    "python": ["programming language", "snake"],
    "java": ["programming language", "island"],
    "coach": ["mentor", "vehicle"],
    "tablet": ["medicine", "electronic device"]
}

def detect_ambiguity(query: str) -> str:
    """Identify ambiguous terms in queries"""
    query_lower = query.lower()
    for term, meanings in AMBIGUOUS_TERMS.items():
        if term in query_lower:
            return f"I noticed you mentioned '{term}'. Did you mean: {', '.join(meanings)}?"
    return ""

def extract_location(message: str) -> str:
    """Extract location from query"""
    patterns = [
        r"in\s+([A-Za-z\s]+)(?:,|\.|$)",
        r"at\s+([A-Za-z\s]+)(?:,|\.|$)",
        r"near\s+([A-Za-z\s]+)(?:,|\.|$)",
        r"around\s+([A-Za-z\s]+)(?:,|\.|$)"
    ]
    for pattern in patterns:
        match = re.search(pattern, message)
        if match:
            return match.group(1).strip()
    return ""

@app.post("/chat", response_model=Dict[str, Any])
async def handle_chat(request: ChatRequest):
    """Main chat endpoint"""
    try:
        session_id = request.session_id
        user_message = request.message.strip()
        location = request.location or extract_location(user_message)
        logger.info(f"Processing query: '{user_message}' in {location or 'any location'}")

        if not user_message:
            return error_response(session_id, "Empty message received")

        add_message(session_id, "user", user_message)

        # Ambiguity check
        clarification = detect_ambiguity(user_message)
        if clarification:
            log_analytics(
                event_type="ambiguity_detected",
                session_id=session_id,
                details={"query": user_message}
            )
            return {
                "reply": clarification,
                "history": get_history(session_id),
                "requires_clarification": True
            }

        # Ethical check
        ethical_check = analyze_ethical_concerns(user_message)
        if ethical_check["is_biased"]:
            log_analytics(
                event_type="bias_detected",
                session_id=session_id,
                details={
                    "query": user_message,
                    "bias_type": ethical_check.get("bias_type", "unknown")
                }
            )
            return handle_ethical_response(session_id, ethical_check)

        # Context retrieval
        context = get_context_for_query(user_message, location)
        if not context_valid(context):
            log_analytics(
                event_type="no_results",
                session_id=session_id,
                details={"query": user_message, "location": location}
            )
            return handle_no_results(session_id)

        # Response generation
        response = generate_ai_response(session_id, context)
        add_message(session_id, "bot", response)

        log_analytics(
            event_type="query",
            session_id=session_id,
            details={
                "query": user_message,
                "response_length": len(response),
                "bias_detected": False
            }
        )

        return success_response(session_id, response, context)

    except Exception as e:
        logger.error("Chat error: %s", str(e), exc_info=True)
        log_analytics(
            event_type="error",
            session_id=session_id if 'session_id' in locals() else "unknown",
            details={"error": str(e), "query": user_message if 'user_message' in locals() else ""}
        )
        return error_response(session_id, str(e))

def handle_ethical_response(session_id: str, analysis: Dict) -> Dict:
    """Handle biased queries"""
    response = analysis["ethical_response"]
    add_message(session_id, "bot", response)
    return {
        "reply": response,
        "history": get_history(session_id),
        "bias_detected": True
    }

def context_valid(context: str) -> bool:
    """Validate RAG context"""
    return bool(context and context.strip())

def handle_no_results(session_id: str) -> Dict:
    """Handle empty results"""
    response = "I couldn't find relevant opportunities. Would you like to try different search terms?"
    add_message(session_id, "bot", response)
    return {
        "reply": response,
        "history": get_history(session_id)
    }

def generate_ai_response(session_id: str, context: str) -> str:
    """Generate response using Groq API"""
    messages = [
        {
            "role": "system",
            "content": f"""You are Asha AI, a career assistant. Use this context:
            {context}
            
            Response rules:
            1. Use markdown formatting for lists and links
            2. Separate different sections with headers
            3. Keep responses under 150 words
            4. End with a clarifying question"""
        },
        *format_history(get_history(session_id)[-4:])
    ]
    
    try:
        response = client.chat.completions.create(
            messages=messages,
            model="llama3-8b-8192",
            temperature=0.7,
            max_tokens=500,
            timeout=10
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logger.error("Groq API call failed: %s", str(e))
        raise

def format_history(history: List) -> List[Dict]:
    """Format conversation history"""
    return [{"role": msg["role"], "content": msg["content"]} for msg in history]

def success_response(session_id: str, reply: str, context: str) -> Dict:
    """Successful response format"""
    return {
        "reply": reply,
        "context": encrypt_data(context),
        "history": get_history(session_id)
    }

def error_response(session_id: str, error_msg: str) -> Dict:
    """Error response format"""
    user_msg = "I'm having technical difficulties. Please try again later."
    add_message(session_id, "bot", user_msg)
    return {
        "reply": user_msg,
        "error": error_msg,
        "history": get_history(session_id)
    }

@app.post("/feedback")
async def handle_feedback(request: FeedbackRequest):
    """Feedback endpoint"""
    try:
        record_feedback(
            request.session_id,
            request.rating,
            request.comments
        )
        log_analytics(
            event_type="feedback",
            session_id=request.session_id,
            details={
                "rating": request.rating,
                "comments": request.comments
            }
        )
        return {"status": "Feedback recorded successfully"}
    except Exception as e:
        logger.error(f"Feedback error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process feedback"
        )

@app.delete("/history/{session_id}")
async def clear_history_endpoint(session_id: str):
    """Clear history endpoint"""
    try:
        clear_history(session_id)
        return {"status": "History cleared successfully"}
    except Exception as e:
        logger.error(f"History clear error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear history"
        )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "operational",
        "version": "1.0.0",
        "components": {
            "rag": "active",
            "llm": "active",
            "database": "active",
            "adzuna_api": "active" if ADZUNA_APP_ID and ADZUNA_APP_KEY else "inactive",
            "ticketmaster_api": "active" if TICKETMASTER_API_KEY else "inactive"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
