Asha AI Bot 🤖✨
---

Asha AI is a conversational assistant designed for women’s career empowerment, developed for the JobsForHer Foundation.
It provides real-time access to job listings, events, mentorship programs, and more — powered by Retrieval-Augmented Generation (RAG), ethical AI principles, and Indian-contextual awareness.
---

🚀 Features
🗣️ Multi-turn conversations with session management

🔎 Semantic search across local and external datasets (Adzuna, Ticketmaster)

⚡ Real-time job and event retrieval

🏙️ Indian cities and synonym-aware query expansion

⚖️ Bias and ambiguity detection

📈 User feedback and analytics support

🛠️ Production-ready FastAPI backend

🎨 Lightweight frontend (HTML, CSS, JS)

🏗️ Technologies Used
Backend: FastAPI, Python 3.10

Frontend: HTML, CSS, JavaScript

APIs Integrated:

Adzuna (Jobs Search API)

Ticketmaster (Events API)

GROQ (LLM API for chat generation)

Other Key Components: Semantic Search, Query Expansion, Bias Detection, Session Management

⚙️ Setup Instructions
1. Clone the Repository
bash
Copy code
git clone https://github.com/sanyagupta31/asha-ai-bot.git
cd asha-ai-bot
2. Set Up Environment Variables
Create a .env file in the root directory with the following keys:

ini
Copy code
GROQ_API_KEY=your_groq_api_key
ADZUNA_APP_ID=your_adzuna_app_id
ADZUNA_APP_KEY=your_adzuna_app_key
TICKETMASTER_API_KEY=your_ticketmaster_api_key
Ensure you replace the placeholders with your actual API keys.

3. Backend Setup
Set up a virtual environment and install the dependencies:

bash
Copy code
python -m venv .venv
.venv\Scripts\activate    # On Windows
# or for Mac/Linux:
# source .venv/bin/activate
pip install -r requirements.txt
4. Start the Backend Server
Run the following command to start the FastAPI backend server:

bash
Copy code
uvicorn src.appp:app --reload
The backend will now be running on http://127.0.0.1:8000.

5. Frontend Setup
Open the index.html file from the frontend folder directly in your browser.

The frontend connects automatically to the backend for real-time interactions.

🛣️ Project Architecture
plaintext
Copy code
Frontend (HTML/CSS/JS) ↔ FastAPI Backend
              ↳ Query Expansion
              ↳ Bias Detection
              ↳ Semantic Search + API Retrieval
              ↳ LLM (GROQ) Processing
              ↳ Return Results to Frontend
🛤️ Future Development
Frontend: Transition to ReactJS for improved user experience

Database Integration: For user personalization and data storage

Advanced Bias Detection: Implementing ML models for more sophisticated bias detection

User Authentication: Adding profile management and login functionality

Offline Caching: Enable offline access to job/event data
---
🤝 Contribution
Contributions are welcome! Please open an issue to discuss major changes before submitting a pull request.
---
📄 License
This project is licensed under the MIT License.
---
🌟 Acknowledgments
JobsForHer Foundation for supporting women’s career development

Adzuna and Ticketmaster for their powerful APIs

The open-source community for inspiration and tools
---
🔥 Empowering Careers, One Chat at a Time!
"Conversational AI bot for women's career empowerment"










