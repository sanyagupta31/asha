# src/ragi.py
import pandas as pd
import json
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import os
import logging
from typing import List, Dict, Any

# Configuration
EMBEDDING_MODEL = 'all-MiniLM-L6-v2'
BATCH_SIZE = 1000
MAX_LIVE_JOBS = 5
MAX_LIVE_EVENTS = 3
MAX_DESCRIPTION_LENGTH = 100
EVENT_DESCRIPTION_LENGTH = 150

# Initialize logging
logger = logging.getLogger(__name__)

# API integrations
from src.api_integrations import fetch_live_jobs, fetch_live_events

def load_datasets():
    """Load datasets with enhanced error handling and path validation"""
    try:
        base_path = os.path.dirname(__file__)
        jobs_path = os.path.join(base_path, "../data/job_listing_data.csv")
        sessions_path = os.path.join(base_path, "../data/session_details.json")
        
        jobs_df = pd.read_csv(jobs_path)
        with open(sessions_path, "r") as f:
            sessions = json.load(f)
            
        logger.info("Datasets loaded successfully")
        return jobs_df, sessions
        
    except Exception as e:
        logger.error(f"Dataset loading failed: {str(e)}", exc_info=True)
        return pd.DataFrame(), []

class RAGSystem:
    def __init__(self):
        """Initialize RAG system with comprehensive validation"""
        self.jobs_df, self.sessions = load_datasets()
        self.model = None
        self.job_index = None
        self.session_index = None
        self._initialize_system()

        # India-specific synonyms
        self.SYNONYM_MAP = {
            "tech": ["technology", "software", "IT", "engineering"],
            "job": ["position", "role", "opportunity"],
            "remote": ["work from home", "wfh", "virtual"],
            "event": ["conference", "meetup", "workshop"],
            "session": ["workshop", "seminar", "webinar"],
            "career": ["professional", "employment", "vocation"],
            "women": ["female", "gender diversity"],
            "mentorship": ["guidance", "coaching", "advising"],
            # Indian city mappings
            "delhi": ["new delhi", "delhi ncr"],
            "mumbai": ["bombay"],
            "bangalore": ["bengaluru"],
            "hyderabad": ["cyberabad"],
            "chennai": ["madras"],
            "pune": ["pimpri", "chinchwad"],
            "kolkata": ["calcutta"]
        }

        # Ambiguity detection terms
        self.AMBIGUOUS_TERMS = {
            "bank": ["financial institution", "side of a river"],
            "python": ["programming language", "snake"],
            "java": ["programming language", "coffee"],
            "coach": ["mentor", "sports trainer"],
            "apple": ["company", "fruit"]
        }

    def _initialize_system(self):
        """Centralized initialization logic"""
        if not self.jobs_df.empty:
            self._initialize_model()
            self._create_indices()

    def _initialize_model(self):
        """Model initialization with error handling"""
        try:
            self.model = SentenceTransformer(EMBEDDING_MODEL)
            logger.info(f"Successfully initialized model: {EMBEDDING_MODEL}")
        except Exception as e:
            logger.error(f"Model initialization failed: {str(e)}")
            self.model = None

    def _create_indices(self):
        """Index creation with batch processing and validation"""
        if self.model is None:
            return

        try:
            # Job index
            job_descriptions = self.jobs_df['description'].tolist()
            job_embeddings = []
            for i in range(0, len(job_descriptions), BATCH_SIZE):
                batch = job_descriptions[i:i+BATCH_SIZE]
                job_embeddings.extend(self.model.encode(batch))
            
            self.job_index = faiss.IndexFlatL2(len(job_embeddings[0]))
            self.job_index.add(np.array(job_embeddings))
            logger.info(f"Created job index with {len(job_embeddings)} embeddings")

            # Session index
            session_texts = [s["description"] for s in self.sessions]
            if session_texts:
                session_embeddings = self.model.encode(session_texts)
                self.session_index = faiss.IndexFlatL2(session_embeddings.shape[1])
                self.session_index.add(np.array(session_embeddings))
                logger.info(f"Created session index with {len(session_texts)} embeddings")

        except Exception as e:
            logger.error(f"Index creation failed: {str(e)}", exc_info=True)
            self.job_index = None
            self.session_index = None

    def _expand_query(self, query: str) -> List[str]:
        """Generate India-aware query variations using synonyms"""
        variations = [query.lower()]
        words = query.lower().split()
        
        # Replace each word with synonyms if available
        for i, word in enumerate(words):
            if word in self.SYNONYM_MAP:
                for syn in self.SYNONYM_MAP[word]:
                    new_variation = words.copy()
                    new_variation[i] = syn
                    variations.append(" ".join(new_variation))
        
        # Location-aware variations
        if " in " in query.lower():
            base = query.lower().split(" in ")[0]
            variations.append(f"{base} near me")
        
        return list(set(variations))

    def detect_ambiguity(self, query: str) -> str:
        """Check for ambiguous terms and return clarification prompt"""
        for term, meanings in self.AMBIGUOUS_TERMS.items():
            if term in query.lower():
                return f"I noticed you mentioned '{term}'. Did you mean: {', '.join(meanings)}?"
        return ""

    def _safe_search(self, index, data_source, query: str, k: int):
        """Generic search with validation and error handling"""
        if not query or index is None:
            return []
        try:
            query_embedding = self.model.encode([query])
            distances, indices = index.search(query_embedding, k)
            return [data_source[i] for i in indices[0]]
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            return []

    def get_relevant_jobs(self, query: str, k: int = 2) -> List[Dict]:
        return self._safe_search(self.job_index, self.jobs_df.to_dict('records'), query, k)

    def get_relevant_sessions(self, query: str, k: int = 2) -> List[Dict]:
        return self._safe_search(self.session_index, self.sessions, query, k)

    def get_live_jobs(self, query: str, location: str = "") -> List[Dict]:
        """Retrieve and format live jobs with enhanced validation"""
        try:
            raw_jobs = fetch_live_jobs(query, location)[:MAX_LIVE_JOBS]
            return [self._format_job(job) for job in raw_jobs if isinstance(job, dict)]
        except Exception as e:
            logger.error(f"Live job retrieval failed: {str(e)}")
            return []

    def _format_job(self, job: Dict) -> Dict:
        """Standardize job format across sources"""
        return {
            'title': self._safe_get(job, ['title'], 'No title').strip(),
            'description': self._truncate_text(self._safe_get(job, ['description'], ''), MAX_DESCRIPTION_LENGTH),
            'location': self._safe_get(job, ['location', 'display_name'], 'Remote').strip(),
            'company': self._safe_get(job, ['company', 'display_name'], 'Unknown Company').strip(),
            'source': 'Adzuna',
            'url': self._safe_get(job, ['redirect_url'], '').strip()
        }

    def get_live_events(self, query: str, location: str = "") -> List[Dict]:
        """Retrieve and format live events with Ticketmaster integration"""
        try:
            raw_events = fetch_live_events(query, location)[:MAX_LIVE_EVENTS]
            return [self._format_event(event) for event in raw_events if isinstance(event, dict)]
        except Exception as e:
            logger.error(f"Live event retrieval failed: {str(e)}")
            return []

    def _format_event(self, event: Dict) -> Dict:
        """Standardize event format for Ticketmaster"""
        return {
            'name': self._safe_get(event, ['name'], 'Untitled Event').strip(),
            'description': self._truncate_text(self._safe_get(event, ['description'], ''), EVENT_DESCRIPTION_LENGTH),
            'date': self._parse_event_date(event.get('start', {})),
            'venue': self._safe_get(event, ['venue'], 'Venue not specified').strip(),
            'url': self._safe_get(event, ['url'], '').strip()
        }

    def _parse_event_date(self, date_info: Dict) -> str:
        """Extract and format event date"""
        date_str = date_info.get('localDate', '')
        time_str = date_info.get('localTime', '')
        return ' '.join(filter(None, [date_str, time_str])) or 'Date not available'

    def _safe_get(self, data: Dict, keys: List, default: str = '') -> str:
        """Safely retrieve nested dictionary values"""
        try:
            for key in keys:
                data = data.get(key, {})
            return str(data).strip() if data else default
        except Exception:
            return default

    def _truncate_text(self, text: str, max_length: int) -> str:
        """Smart text truncation with ellipsis"""
        text = text.strip()
        if len(text) <= max_length:
            return text
        return text[:max_length-3].rsplit(' ', 1)[0] + '...'

    def get_context(self, query: str, location: str = "") -> str:
        """Build comprehensive context with structured sections"""
        # Expand query variations
        query_variations = self._expand_query(query)
        logger.info(f"Expanded queries: {query_variations}")
        
        # Collect results from all variations
        all_results = {
            'local_jobs': [],
            'live_jobs': [],
            'live_events': [],
            'sessions': []
        }
        
        for variation in query_variations:
            all_results['local_jobs'].extend(self.get_relevant_jobs(variation))
            all_results['live_jobs'].extend(self.get_live_jobs(variation, location))
            all_results['live_events'].extend(self.get_live_events(variation, location))
            all_results['sessions'].extend(self.get_relevant_sessions(variation))
        
        # Deduplicate results
        def deduplicate(items, key_field):
            seen = set()
            return [item for item in items 
                    if (key := item.get(key_field)) not in seen and not seen.add(key)]
        
        local_jobs = deduplicate(all_results['local_jobs'], 'title')[:3]
        live_jobs = deduplicate(all_results['live_jobs'], 'title')[:3]
        live_events = deduplicate(all_results['live_events'], 'name')[:2]
        sessions = deduplicate(all_results['sessions'], 'title')[:2]
        
        # Build context sections with improved formatting
        context_sections = []
        
        if local_jobs:
            context_sections.append(self._format_section(
                "🌟 Local Job Opportunities",
                [f"• **{job['title']}** ({job['location']})\n  {job['company']}\n  {job['description']}" 
                 for job in local_jobs]
            ))

        if live_jobs:
            context_sections.append(self._format_section(
                "🚀 Live Job Listings",
                [f"• **{job['title']}** at {job['company']} ({job['location']})\n  {job['description']}\n  [Apply Here]({job['url']})" 
                 for job in live_jobs if job['url']]
            ))

        if live_events:
            context_sections.append(self._format_section(
                "📅 Upcoming Events",
                [f"• **{event['name']}**\n  {event['venue']} ({event['date']})\n  {event['description']}\n  [More Info]({event['url']})" 
                 for event in live_events if event['url']]
            ))

        if sessions:
            context_sections.append(self._format_section(
                "🎓 Local Sessions",
                [f"• **{session['title']}**\n  {session['date']}\n  {session['description']}" 
                 for session in sessions]
            ))

        return '\n\n'.join(context_sections) if context_sections else ""

    def _format_section(self, title: str, items: List[str]) -> str:
        """Format context section with consistent styling"""
        return f"### {title}\n" + '\n'.join(items)

# Initialize system
rag_system = RAGSystem()

def get_context_for_query(query: str, location: str = "") -> str:
    """Public API endpoint with error boundary"""
    try:
        return rag_system.get_context(query, location)
    except Exception as e:
        logger.error(f"Context generation failed: {str(e)}", exc_info=True)
        return "I encountered an error while processing your request. Please try again later."

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    test_cases = [
        ("tech jobs in delhi", "Delhi"),
        ("IT positions in bengaluru", ""),
        ("career workshop mumbai", "Mumbai"),
        ("women in tech events", ""),
        ("bank jobs", ""),  # Test ambiguity
        ("python developer", "")  # Test ambiguity
    ]
    
    for query, location in test_cases:
        print(f"\n{' TEST CASE ':-^80}")
        print(f"Query: {query}\nLocation: {location or 'N/A'}")
        
        # Check ambiguity first
        ambiguity = rag_system.detect_ambiguity(query)
        if ambiguity:
            print(f"\nAMBIGUITY DETECTED: {ambiguity}")
            continue
            
        context = get_context_for_query(query, location)
        print(f"\n{' RESPONSE ':-^80}\n{context or 'No relevant results found'}")
