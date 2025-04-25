# src/ethical.py
import spacy
import re
from typing import Optional, Dict, Any, List, Tuple

# Load spaCy model
nlp = spacy.load("en_core_web_sm")

# More comprehensive bias patterns
BIAS_PATTERNS = {
    "gender_exclusionary": [
        "only women", "women only", "female-only", "males only", "only men", 
        "men only", "male-dominated", "female-dominated"
    ],
    "stereotyping": [
        "women are better at", "men are better at", "typical female job", 
        "typical male job", "women should", "men should"
    ]
}

def check_bias(text: str) -> Tuple[bool, Optional[str]]:
    """
    Check if text contains potentially biased language.
    
    Returns:
        Tuple of (is_biased, bias_type)
    """
    text_lower = text.lower()
    
    # Check direct pattern matches
    for bias_type, patterns in BIAS_PATTERNS.items():
        if any(pattern in text_lower for pattern in patterns):
            return True, bias_type
    
    # More sophisticated checks could be added here
    # (e.g., using NLP techniques to detect subtle bias)
    
    return False, None

def get_ethical_response(bias_type: Optional[str] = None) -> str:
    """Return an appropriate ethical response based on bias type"""
    
    if bias_type == "gender_exclusionary":
        return ("Our platform promotes equal opportunities for all genders. "
                "I can help you find roles matching your skills rather than "
                "focusing on gender-specific positions. What skills or experience "
                "would you like to search for?")
    
    if bias_type == "stereotyping":
        return ("I'd like to focus on individual skills and qualifications rather "
                "than generalizations. Could you tell me more about the specific "
                "job requirements or qualifications you're interested in?")
    
    # Default response for other types of bias
    return ("I'm committed to providing inclusive and unbiased information. "
            "How can I help you find opportunities based on skills and interests?")

def analyze_ethical_concerns(text: str) -> Dict[str, Any]:
    """
    Comprehensive ethical analysis of user input.
    Returns dict with ethical analysis results.
    """
    is_biased, bias_type = check_bias(text)
    
    return {
        "is_biased": is_biased,
        "bias_type": bias_type,
        "ethical_response": get_ethical_response(bias_type) if is_biased else None
    }
