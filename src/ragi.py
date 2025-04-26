import pandas as pd
import json
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import os
import logging
from typing import List, Dict, Any, Optional

EMBEDDING_MODEL = 'all-MiniLM-L6-v2'
BATCH_SIZE = 1000
MAX_LIVE_JOBS = 5
MAX_LIVE_EVENTS = 3
MAX_DESCRIPTION_LENGTH = 100
EVENT_DESCRIPTION_LENGTH = 150

logger = logging.getLogger(_name_)

class RAGSystem:
    def _init_(self):
        """Initialize RAG system with comprehensive validation"""
        self.jobs_df, self.sessions = self._load_datasets_with_fallback()
        self.model = None
        self.job_index = None
        self.session_index = None
        self._initialize_system()

        self.SYNONYM_MAP = {
            "tech": ["technology", "software", "IT", "engineering"],
            "job": ["position", "role", "opportunity"],
            "remote": ["work from home", "wfh", "virtual"],
            "event": ["conference", "meetup", "workshop"],
            "session": ["workshop", "seminar", "webinar"],
            "career": ["professional", "employment", "vocation"],
            "women": ["female", "gender diversity"],
            "mentorship": ["guidance", "coaching", "advising"],
            "delhi": ["new delhi", "delhi ncr"],
            "mumbai": ["bombay"],
            "bangalore": ["bengaluru"],
            "hyderabad": ["cyberabad"],
            "chennai": ["madras"],
            "pune": ["pimpri", "chinchwad"],
            "kolkata": ["calcutta"]
        }

    def _load_datasets_with_fallback(self) -> tuple:
        """Load datasets with multiple fallback mechanisms"""
        try:
            base_path = os.path.dirname(_file_)
            jobs_path = os.path.join(base_path, "../data/job_listing_data.csv")
            sessions_path = os.path.join(base_path, "../data/session_details.json")
            
            jobs_df = pd.read_csv(jobs_path)
            with open(sessions_path, "r") as f:
                sessions = json.load(f)
                
            logger.info("Datasets loaded successfully")
            return jobs_df, sessions
            
        except Exception as e:
            logger.error(f"Dataset loading failed: {str(e)}")
            return pd.DataFrame(columns=['title', 'description', 'location', 'company']), []

    def _initialize_system(self):
        """Centralized initialization with validation"""
        try:
            self.model = SentenceTransformer(EMBEDDING_MODEL)
            logger.info(f"Model loaded: {EMBEDDING_MODEL}")
            
            if not self.jobs_df.empty:
                self._create_job_index()
            if self.sessions:
                self._create_session_index()
                
        except Exception as e:
            logger.error(f"System initialization failed: {str(e)}")
            self.model = None
            self.job_index = None
            self.session_index = None

    def _create_job_index(self):
        """Create FAISS index for jobs with batch processing"""
        try:
            job_descriptions = self.jobs_df['description'].fillna('').astype(str).tolist()
            job_embeddings = []
            
            for i in range(0, len(job_descriptions), BATCH_SIZE):
                batch = job_descriptions[i:i+BATCH_SIZE]
                job_embeddings.extend(self.model.encode(batch))
            
            if job_embeddings:
                self.job_index = faiss.IndexFlatL2(len(job_embeddings[0]))
                self.job_index.add(np.array(job_embeddings))
                logger.info(f"Created job index with {len(job_embeddings)} embeddings")
                
        except Exception as e:
            logger.error(f"Job index creation failed: {str(e)}")
            self.job_index = None

    def _create_session_index(self):
        """Create FAISS index for sessions"""
        try:
            session_texts = [s.get("description", "") for s in self.sessions]
            session_embeddings = self.model.encode(session_texts)
            
            self.session_index = faiss.IndexFlatL2(session_embeddings.shape[1])
            self.session_index.add(np.array(session_embeddings))
            logger.info(f"Created session index with {len(session_texts)} embeddings")
            
        except Exception as e:
            logger.error(f"Session index creation failed: {str(e)}")
            self.session_index = None

    def _expand_query(self, query: str) -> List[str]:
        """Generate query variations using synonyms"""
        if not query or not isinstance(query, str):
            return []
            
        variations = [query.lower()]
        words = query.lower().split()
        
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

    def _safe_search(self, index, data_source, query: str, k: int) -> List[Dict]:
        """Safe search with validation"""
        if not query or index is None or not data_source:
            return []
            
        try:
            query_embedding = self.model.encode([query])
            distances, indices = index.search(query_embedding, k)
            return [data_source[i] for i in indices[0] if i < len(data_source)]
        except Exception as e:
            logger.error(f"Search failed for query '{query}': {str(e)}")
            return []

    def get_relevant_jobs(self, query: str, k: int = 2) -> List[Dict]:
        """Get relevant jobs with validation"""
        if not self.jobs_df.empty:
            return self._safe_search(self.job_index, self.jobs_df.to_dict('records'), query, k)
        return []

    def get_relevant_sessions(self, query: str, k: int = 2) -> List[Dict]:
        """Get relevant sessions with validation"""
        if self.sessions:
            return self._safe_search(self.session_index, self.sessions, query, k)
        return []

    def _format_job(self, job: Dict) -> Dict:
        """Standardize job format with robust field access"""
        if not isinstance(job, dict):
            return {}
            
        return {
            'title': str(job.get('title', job.get('Title', 'No title'))).strip(),
            'description': self._truncate_text(
                str(job.get('description', job.get('Description', ''))),
                MAX_DESCRIPTION_LENGTH
            ),
            'location': str(job.get('location', job.get('Location', 'Remote'))).strip(),
            'company': str(job.get('company', job.get('Company', 'Unknown Company'))).strip(),
            'source': 'Adzuna',
            'url': str(job.get('url', job.get('redirect_url', ''))).strip()
        }

    def _format_event(self, event: Dict) -> Dict:
        """Standardize event format with robust field access"""
        if not isinstance(event, dict):
            return {}
            
        return {
            'name': str(event.get('name', 'Untitled Event')).strip(),
            'description': self._truncate_text(
                str(event.get('description', '')),
                EVENT_DESCRIPTION_LENGTH
            ),
            'date': self._parse_event_date(event.get('start', {})),
            'venue': str(event.get('venue', 'Venue not specified')).strip(),
            'url': str(event.get('url', '')).strip()
        }

    def _parse_event_date(self, date_info: Dict) -> str:
        """Safely parse event date"""
        if not isinstance(date_info, dict):
            return 'Date not available'
            
        date_str = str(date_info.get('localDate', '')).strip()
        time_str = str(date_info.get('localTime', '')).strip()
        return ' '.join(filter(None, [date_str, time_str])) or 'Date not available'

    def _truncate_text(self, text: str, max_length: int) -> str:
        """Smart text truncation with ellipsis"""
        if not isinstance(text, str):
            return ''
            
        text = text.strip()
        if len(text) <= max_length:
            return text
        return text[:max_length-3].rsplit(' ', 1)[0] + '...'

    def _deduplicate_items(self, items: List[Dict], key_field: str) -> List[Dict]:
        """Remove duplicates based on key field"""
        if not items or not key_field:
            return []
            
        seen = set()
        unique_items = []
        
        for item in items:
            if not isinstance(item, dict):
                continue
                
            key = item.get(key_field)
            if key and key not in seen:
                seen.add(key)
                unique_items.append(item)
                
        return unique_items

    def _format_section(self, title: str, items: List[str]) -> str:
        """Format context section with validation"""
        if not items:
            return ""
            
        return f"### {title}\n" + '\n'.join(
            item for item in items if isinstance(item, str)
        )

    def get_context(self, query: str, location: str = "") -> str:
        """Build comprehensive context with error handling"""
        if not query or not isinstance(query, str):
            return "Please provide a valid query."
            
        try:
            query_variations = self._expand_query(query)
            logger.info(f"Processing query: '{query}' with variations: {query_variations}")
            
            results = {
                'local_jobs': [],
                'live_jobs': [],
                'live_events': [],
                'sessions': []
            }
            
            for variation in query_variations:
                results['local_jobs'].extend(self.get_relevant_jobs(variation))
                results['sessions'].extend(self.get_relevant_sessions(variation))
                
                try:
                    results['live_jobs'].extend(self.get_live_jobs(variation, location))
                except Exception as e:
                    logger.error(f"Live jobs API failed: {str(e)}")
                    
                try:
                    results['live_events'].extend(self.get_live_events(variation, location))
                except Exception as e:
                    logger.error(f"Live events API failed: {str(e)}")
            
            local_jobs = self._deduplicate_items(results['local_jobs'], 'title')[:3]
            live_jobs = self._deduplicate_items(results['live_jobs'], 'title')[:3]
            live_events = self._deduplicate_items(results['live_events'], 'name')[:2]
            sessions = self._deduplicate_items(results['sessions'], 'title')[:2]
            
            sections = []
            
            if local_jobs:
                job_items = [
                    f"• *{job.get('title', 'No title')}* "
                    f"({job.get('location', 'Location not specified')})\n"
                    f"  {job.get('company', 'Company not specified')}\n"
                    f"  {job.get('description', '')}"
                    for job in local_jobs
                ]
                sections.append(self._format_section("🌟 Local Job Opportunities", job_items))
                
            if live_jobs:
                live_job_items = [
                    f"• *{job.get('title', 'No title')}* at "
                    f"{job.get('company', 'Company not specified')} "
                    f"({job.get('location', 'Location not specified')})\n"
                    f"  {job.get('description', '')}\n"
                    f"  [Apply Here]({job.get('url', '')})"
                    for job in live_jobs if job.get('url')
                ]
                sections.append(self._format_section("🚀 Live Job Listings", live_job_items))
                
            if live_events:
                event_items = [
                    f"• *{event.get('name', 'Untitled Event')}*\n"
                    f"  {event.get('venue', 'Venue not specified')} "
                    f"({event.get('date', 'Date not available')})\n"
                    f"  {event.get('description', '')}\n"
                    f"  [More Info]({event.get('url', '')})"
                    for event in live_events if event.get('url')
                ]
                sections.append(self._format_section("📅 Upcoming Events", event_items))
                
            if sessions:
                session_items = [
                    f"• *{session.get('title', 'Untitled Session')}*\n"
                    f"  {session.get('date', 'Date not available')}\n"
                    f"  {session.get('description', '')}"
                    for session in sessions
                ]
                sections.append(self._format_section("🎓 Local Sessions", session_items))
            
            return '\n\n'.join(sections) if sections else "No relevant results found."
            
        except Exception as e:
            logger.error(f"Context generation failed: {str(e)}", exc_info=True)
            return "I encountered an error while processing your request. Please try again later."

rag_system = RAGSystem()

def get_context_for_query(query: str, location: str = "") -> str:
    """Public API endpoint with error boundary"""
    return rag_system.get_context(query, location)

if _name_ == "_main_":
    logging.basicConfig(level=logging.INFO)
    
    test_cases = [
        ("tech jobs in delhi", "Delhi"),
        ("python developer", ""),
        ("", "Mumbai"),  
        (123, "Bangalore"),  
        ("women in tech events", "")
    ]
    
    for query, location in test_cases:
        print(f"\n{' TEST CASE ':-^80}")
        print(f"Query: {query}\nLocation: {location or 'N/A'}")
        
        context = get_context_for_query(str(query) if query else "", location)
        print(f"\n{' RESPONSE ':-^80}\n{context}")
