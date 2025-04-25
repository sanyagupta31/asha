# Asha-AI-Bot

# Asha AI Chatbot

Asha AI is a conversational assistant for women’s career empowerment, built for the JobsForHer Foundation. It provides real-time access to job listings, events, mentorship programs, and more—using Retrieval-Augmented Generation (RAG), ethical AI, and Indian-contextual awareness.

---

## Features

- **Multi-turn conversation** with session management
- **Semantic search** over local and live (Adzuna, Ticketmaster) datasets
- **Real-time job and event retrieval**
- **Indian city and synonym-aware query expansion**
- **Bias and ambiguity detection**
- **User feedback and analytics**
- **Production-ready FastAPI backend**
- **Modern React frontend**

---

## Quickstart

### 1. Clone the Repository


### 2. Set Up Environment

Create a `.env` file in the project root:

> GROQ_API_KEY=your_groq_api_key

>  ADZUNA_APP_ID=your_adzuna_app_id

> ADZUNA_APP_KEY=your_adzuna_app_key

> TICKETMASTER_API_KEY=your_ticketmaster_api_key(Consumer Key TO BE CONSIDERED)


### 3. Install Backend Dependencies(ALL TO BE WRITTEN IN TERMINAL)

> python -m venv .venv(VERSION 10.9.9 IS COMPATIBLE)

> .venv\Scripts\activate on Windows (ACTIVATION OF VIRTUAL EENVIRONMENT

> pip install -r requirements.txt



### 4. Start the Backend

> uvicorn src.appp:app --reload

