# Hierarchical AI Agent System – Prototype

**A minimal, three-tier AI-agent framework for task orchestration and high-accuracy content delivery.**

## Key Features
- **Director Agent**  
  Routes user requests (e.g., “send email”) to specialized departments.
- **Communications Dept**  
  Uses two parallel DraftReviewAgents for consensus-driven drafts.
- **Email Agent**  
  Wraps SMTP via Flask-Mail to send finalized messages.
- **Streaming Edge Interface**  
  Demonstrates low-latency streaming interactions with AutoGen.

## Tech Stack
- **Language & Frameworks:** Python 3.10+, AutoGen, Flask  
- **Database:** SQLite (embedded)  
- **Messaging:** In-memory queues (prototype)  
- **Deployment:** Run locally or in Docker for parity

## Getting Started
1. **Clone** the repo  
2. **Install** dependencies: `pip install -r requirements.txt`  
3. **Run** the Flask server: `python app.py`  
4. **Send** a task via `POST /task` (see swagger docs)

## Next Steps
- Swap routing to an LLM-based intent classifier  
- Add more departments (Research, Planning, Vision)  
- Migrate to Postgres & Redis for MVP

---

> _This prototype validates the core Director → Department → Tool workflow and lays the foundation for a fully extensible, hierarchical AI-agent ecosystem._  
