#  GenAI Course Purchase Chatbot

An intelligent course enrollment chatbot built with **LangGraph**, **Groq LLaMA**, **FastAPI**, and **Streamlit** — featuring a full **Human-in-the-Loop (HITL)** workflow and **PostgreSQL** database integration.

## Project Overview

CourseBot is a conversational AI sales assistant that helps users explore and enroll in Generative AI courses. It collects user details step-by-step, pauses for human review before confirming enrollment, and saves all data to a PostgreSQL database.

##  Tech Stack

| Layer        | Technology                          |
|--------------|--------------------------------------|
| LLM          | Groq — LLaMA 3.1 8B Instant         |
| Agent Framework | LangGraph (StateGraph + MemorySaver) |
| Backend API  | FastAPI + Uvicorn (streaming NDJSON) |
| Frontend     | Streamlit                            |
| Database     | PostgreSQL + pgvector + SQLAlchemy   |
| ORM Service  | SQLAlchemy + custom EnrollmentService |


##  Human-in-the-Loop (HITL) Architecture

The project implements **3 dedicated HITL nodes** with **4 total interrupts** using LangGraph's `interrupt()` and `Command(resume=...)` pattern.

```
User fills 5 fields one by one via chat
        ↓
Agent calls confirm_enrollment
        ↓
Router intercepts → user_review_node
        ↓
INTERRUPT 1 — shows summary → waits for decision

   approve  →  tools (confirm_enrollment runs)
                 → agent → save_user_details → DB → DONE

    edit     →  user_edit_node
                 INTERRUPT 2 — which field to change?
                 INTERRUPT 3 — what is the new value?
                 → agent → confirm_enrollment → INTERRUPT 1 again

   cancel   →  user_cancel_node
                 INTERRUPT 4 — are you sure? yes / no
                 yes → agent → cancelled → DONE
                 no  → agent → confirm_enrollment → INTERRUPT 1 again
```


##  Project Structure

```
genai_course_bot/
│
├── agent.py                        # LangGraph agent + 3 HITL nodes
├── app.py                          # FastAPI backend with streaming endpoints
├── streamlit_app.py                # Streamlit frontend UI
├
│
├── tools/
│   ├── get_course_info_tools.py    # Tool — fetch course details
│   ├── confirm_enrollment_tools.py # Tool — confirm enrollment trigger
│   └── save_user_details_tools.py  # Tool — save to PostgreSQL
│
├── db/
│   ├── database.py                 # SQLAlchemy engine + SessionLocal + init_db
│   ├── models.py                   # EnrollmentUser ORM model + pgvector column
│   └── service.py                  # EnrollmentService — CRUD operations
│
├── utils/
│   ├── config.py                   # Load env variables
│   └── logger.py                   # Custom logger
│
├── .env                            # API keys and DB URL 
├── requirements.txt                # Python dependencies
└── README.md
```
### 1. Clone the repository
```bash
git clone https://github.com/anjalimahapatra2004/course_bot
cd course_bot
```

### 2. Create virtual environment
```bash
python -m venv venv
source venv/Scripts/activate   
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Create `.env` file
```env
GROQ_API_KEY=your_groq_api_key_here
MODEL_NAME=llama-3.1-8b-instant
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/yourdbname
```

### 5. Start FastAPI backend
```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

### 6. Start Streamlit frontend (new terminal)
```bash
streamlit run streamlit_app.py
```
##  API Endpoints

| Method | Endpoint       | Description                              |
|--------|----------------|------------------------------------------|
| POST   | `/chat`        | Send user message — returns NDJSON stream |
| POST   | `/resume`      | Resume paused graph after HITL decision  |
| GET    | `/enrollments` | Fetch all enrollment records from DB     |
| GET    | `/health`      | Health check                             |

---

##  Available Courses

| Course ID        | Name                              | Price    | Duration |
|------------------|-----------------------------------|----------|----------|
| genai_beginner   | Generative AI for Beginners       | ₹3,999   | 4 weeks  |
| genai_advanced   | Advanced GenAI & Agentic Systems  | ₹12,499  | 8 weeks  |
| llmops           | LLMOps & DevOps for AI            | ₹8,299   | 6 weeks  |

---

##  Features

- Conversational enrollment flow — collects 5 fields one by one
- 3 HITL nodes with 4 interrupts — approve, edit, cancel
- PostgreSQL integration with pgvector support
- Streaming responses via NDJSON
- Session memory using LangGraph MemorySaver
- Quick Enroll form on right panel
- Clear chat with new session support

---
