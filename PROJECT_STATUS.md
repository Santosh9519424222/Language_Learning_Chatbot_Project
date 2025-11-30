# Multi-Agent PDF Intelligence + Language Learning Platform

## 🎯 Project Overview
Production-ready AI-powered platform for PDF-based language learning with 7 specialized AI agents.

**Author**: Santosh Yadav (B.Tech IT 2024)  
**Stack**: React TypeScript + FastAPI + PostgreSQL + Gemini API  
**Deployment**: Firebase Hosting + Google Cloud Run  
**Budget**: ₹0 (GitHub Student credits)

---

## ✅ COMPLETED PHASES (1-6)

### Phase 1: FastAPI Backend ✅
- **File**: `backend/main.py`
- Complete FastAPI app with CORS, health checks, structured logging
- Request ID middleware for tracing
- Environment-aware configuration
- Database, Vector Store, and Gemini initialization

### Phase 2: Database Models ✅
- **File**: `backend/models/database.py`
- 8 SQLAlchemy models: Users, PDFs, Topics, QASessions, LanguageMistakes, Flags, Translations, LearningReports
- Proper relationships, indexes, and constraints
- Connection pooling for Cloud Run

### Phase 3: Pydantic Schemas ✅
- **File**: `backend/models/schemas.py`
- 20+ request/response schemas with validation
- Enums for languages, difficulty levels, mistake types
- Example values and docstrings

### Phase 4: PDF Handler ✅
- **File**: `backend/storage/pdf_handler.py`
- Validation, extraction, chunking, metadata
- Language detection with langdetect
- Vocabulary section detection

### Phase 5: Vector Store ✅
- **File**: `backend/storage/vector_store.py`
- Chroma DB with persistent storage
- Semantic search with all-MiniLM-L6-v2 embeddings
- Thread-safe operations

### Phase 6: System Prompts ✅
- **File**: `backend/prompts/system_prompts.py`
- 7 production-ready agent prompts with JSON output formats
- Each prompt is 200-300 words with specific instructions

### Configuration Files ✅
- `backend/config/gemini_config.py`: Gemini API client with rate limiting
- `backend/config/gcp_config.py`: Google Cloud Platform integration

### Middleware ✅
- `backend/middleware/logging.py`: JSON structured logging for Cloud Run
- `backend/middleware/error_handler.py`: Comprehensive error handling

---

## 📋 REMAINING PHASES (7-16)

### Phase 7: Individual Agents
**Status**: Need to create 8 agent files

**Files to create**:
```
backend/agents/
├── __init__.py
├── base_agent.py          # Abstract base class
├── pdf_upload_agent.py    # Validates PDFs
├── extraction_agent.py    # Extracts topics/vocabulary
├── context_guard_agent.py # Validates question relevance
├── qa_agent.py            # Answers questions
├── translator_agent.py    # Translates content
├── language_coach_agent.py # Provides feedback
└── flag_reporter_agent.py  # Generates reports
```

**Key Features Each Agent Needs**:
- Inherit from BaseAgent
- Call Gemini API via self.gemini_client
- Parse JSON responses
- Error handling with retries
- Logging for debugging

---

### Phase 8: LangGraph Orchestrator
**File**: `backend/agents/orchestrator.py`

**Requirements**:
- ConversationState TypedDict
- PDFOrchestratorAgent class
- LangGraph StateGraph workflow
- Nodes for each agent
- Conditional edges based on state
- 30-second timeout per agent

---

### Phase 9: API Routes (10 Endpoints)
**File**: `backend/routes/api.py`

**Endpoints**:
1. `POST /api/pdfs/upload` - Upload and process PDF
2. `GET /api/pdfs/{file_id}/topics` - Get extracted topics
3. `POST /api/chat/question` - Ask questions
4. `GET /api/pdfs/{file_id}` - Get PDF metadata
5. `POST /api/language-feedback` - Get language feedback
6. `POST /api/translate` - Translate content
7. `POST /api/language-coach/analyze` - Analyze mistakes
8. `GET /api/reports/{file_id}` - Generate learning report
9. `GET /api/pdfs/{file_id}/sessions` - Get Q&A history
10. `GET /api/health` - Already in main.py

---

### Phase 10: Utilities
**Files**:
- `backend/utils/helpers.py`: Helper functions for IDs, formatting, exports

---

### Phase 11-16: Frontend
**Files needed**:
- `frontend/package.json`
- `frontend/tsconfig.json`
- `frontend/src/App.tsx`
- `frontend/src/index.tsx`
- `frontend/src/components/*` (20+ components)
- `frontend/src/pages/*` (4 pages)
- `frontend/src/services/api.ts`
- `frontend/src/types/index.ts`

---

## 🚀 DEPLOYMENT FILES NEEDED

### Backend Deployment
**Files**:
1. `backend/Dockerfile`
2. `backend/cloudbuild.yaml`
3. `.github/workflows/backend-deploy.yml`

### Frontend Deployment
**Files**:
1. `frontend/firebase.json`
2. `frontend/.firebaserc`
3. `.github/workflows/frontend-deploy.yml`

### Environment Configuration
**Files**:
1. `.env.example`
2. `.env.development`
3. `.env.production`

---

## 🔧 ENVIRONMENT VARIABLES NEEDED

```bash
# Backend (.env)
ENVIRONMENT=production
PORT=8080
DATABASE_URL=postgresql://user:pass@host:5432/dbname
GEMINI_API_KEY=your_gemini_api_key
GCP_PROJECT_ID=your-gcp-project-id
GCS_BUCKET_NAME=pdf-learning-pdfs
CHROMA_PERSIST_DIR=/data/chroma_db
LOG_LEVEL=INFO

# Frontend (.env)
REACT_APP_API_URL=https://your-cloud-run-url.run.app
REACT_APP_ENVIRONMENT=production
```

---

## 📦 DEPENDENCIES INSTALLED

### Backend (requirements.txt) ✅
- FastAPI, Uvicorn, Pydantic
- SQLAlchemy, PostgreSQL
- ChromaDB, sentence-transformers
- pdfplumber, PyPDF2
- google-generativeai, langchain
- spacy, langdetect

### Frontend (package.json) - TODO
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "typescript": "^5.0.0",
    "@types/react": "^18.2.0",
    "axios": "^1.6.0",
    "react-router-dom": "^6.20.0",
    "zustand": "^4.4.0",
    "@mui/material": "^5.15.0",
    "react-pdf": "^7.6.0",
    "react-markdown": "^9.0.0",
    "recharts": "^2.10.0"
  }
}
```

---

## 🗄️ DATABASE SETUP

### PostgreSQL Schema
```sql
-- Run this to create the database
CREATE DATABASE pdf_learning_db;

-- Tables are auto-created by SQLAlchemy on first run
-- See backend/models/database.py for schema
```

### Cloud SQL Connection String
```
postgresql://postgres:PASSWORD@/pdf_learning_db?host=/cloudsql/PROJECT:REGION:INSTANCE
```

---

## 🧪 TESTING COMMANDS

```bash
# Backend tests
cd backend
pytest tests/ -v --cov

# Frontend tests
cd frontend
npm test

# Integration tests
python -m pytest tests/integration/
```

---

## 🔍 NEXT IMMEDIATE STEPS

1. **Create all 8 agent files** (Phase 7)
2. **Create orchestrator** (Phase 8)
3. **Create API routes** (Phase 9)
4. **Create Dockerfile and deployment configs**
5. **Test locally with docker-compose**
6. **Deploy to Google Cloud Run**
7. **Build React frontend**
8. **Deploy to Firebase Hosting**

---

## 🎓 AGENT ARCHITECTURE

```
User Request
     ↓
Orchestrator (LangGraph)
     ↓
[1] PDF Upload Agent → Validates PDF
     ↓
[2] Extraction Agent → Extracts topics/vocab
     ↓
[3] Context Guard → Validates question
     ↓
[4] QA Agent → Answers from PDF
     ↓
[6] Language Coach → Analyzes mistakes
     ↓
[7] Flag Reporter → Generates report
```

---

## 💡 KEY DESIGN DECISIONS

1. **Gemini FREE tier**: 60 req/min with rate limiting
2. **Chroma DB**: Persistent, no GPU needed
3. **all-MiniLM-L6-v2**: Fast CPU embeddings
4. **PostgreSQL**: Scalable, ACID compliant
5. **JSON logging**: Cloud Run compatible
6. **UUID file naming**: Avoid conflicts
7. **Page-level chunking**: Better context

---

## 📊 PROJECT METRICS

- **Total Files**: ~60 files
- **Lines of Code**: ~15,000+ lines
- **Agents**: 7 AI agents
- **API Endpoints**: 10 REST endpoints
- **Database Tables**: 8 tables
- **Frontend Components**: 20+ components
- **Deployment Targets**: 2 (Cloud Run + Firebase)

---

## 🔒 SECURITY CONSIDERATIONS

1. **API Key Management**: Use Secret Manager
2. **CORS**: Restricted to Firebase domain
3. **Input Validation**: Pydantic schemas
4. **SQL Injection**: SQLAlchemy ORM
5. **Rate Limiting**: Per-user quotas
6. **File Upload**: Size/type validation
7. **Prompt Injection**: Context Guard blocks

---

## 📈 SCALABILITY

- **Database**: Connection pooling
- **Vector Store**: Persistent, scalable
- **API**: Async FastAPI
- **Cloud Run**: Auto-scaling 0-100 instances
- **Firebase**: CDN-backed hosting
- **Caching**: Redis for sessions (future)

---

## 🎯 SUCCESS CRITERIA

✅ Upload PDF and extract topics  
✅ Ask questions and get answers  
✅ Receive language feedback  
✅ Generate learning reports  
✅ Translate content  
✅ Track progress over time  
✅ Mobile responsive UI  
✅ < 2 second response time  
✅ 99.5% uptime  

---

## 📞 SUPPORT & DOCUMENTATION

- **API Docs**: `/docs` (Swagger UI)
- **ReDoc**: `/redoc`
- **Health Check**: `/health`
- **GitHub**: [Your repo URL]
- **Portfolio**: [Your portfolio URL]

---

## 🏆 COMPETITIVE ADVANTAGES

1. **7 Specialized Agents** vs single chatbot
2. **PDF-based Learning** vs generic chat
3. **Personalized Reports** with gap analysis
4. **Multi-language Support** (11 languages)
5. **Free Tier** using Gemini FREE API
6. **Production-Ready** with monitoring
7. **Portfolio Quality** for job interviews

---

## 🔄 CONTINUOUS IMPROVEMENT

### Future Enhancements:
- [ ] Voice pronunciation analysis
- [ ] Spaced repetition flashcards
- [ ] Progress gamification
- [ ] Collaborative learning rooms
- [ ] Mobile app (React Native)
- [ ] Integration with Anki
- [ ] AI conversation practice
- [ ] Video content support

---

## 📝 LICENSE
MIT License - Free for portfolio and commercial use

---

## 👤 AUTHOR
**Santosh Yadav**  
B.Tech IT Graduate 2024  
GitHub Student Developer  
[LinkedIn] | [GitHub] | [Portfolio]

---

**Last Updated**: November 30, 2025  
**Version**: 1.0.0  
**Status**: Backend 60% Complete, Frontend 0% Complete

