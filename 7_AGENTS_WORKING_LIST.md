# 🤖 THE 7 AI AGENTS - Complete Working List

**Project:** Multi-Agent PDF Intelligence + Language Learning Platform  
**Total Agents:** 7 Specialized AI Workers  
**Created:** December 5, 2025

---

## 📋 QUICK OVERVIEW

Your system uses **7 specialized AI agents** that work together like an assembly line to process PDFs and provide intelligent learning features.

---

## 🔧 THE 7 AGENTS - HOW EACH ONE WORKS

### **AGENT 1: PDF Upload Agent** 🔍

**File:** `backend/agents/pdf_upload_agent.py`

**Job:** Quality Control Inspector - First line of defense

**What it does:**
1. ✅ Validates PDF file (format, size, page count)
2. 📄 Extracts text from PDF using pdfplumber
3. 📝 Gets metadata (title, author, creation date)
4. 🌍 Detects language (English, Hindi, Spanish, etc.)
5. 🤖 Sends first 5000 characters to Gemini AI
6. 🎯 Gemini analyzes: "What's this PDF about? What difficulty level?"

**Input:**
```python
{
    "file_path": "/uploads/sample.pdf",
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "enable_ocr": False
}
```

**Output:**
```python
{
    "success": True,
    "data": {
        "file_size": 1024000,
        "page_count": 10,
        "detected_language": "en",
        "ai_analysis": {
            "topic": "Python Programming",
            "difficulty": "Intermediate"
        }
    }
}
```

**When it runs:** Every time a user uploads a PDF

**API Endpoint:** Called internally during `POST /api/pdfs/upload`

---

### **AGENT 2: Extraction Agent** 📚

**File:** `backend/agents/extraction_agent.py`

**Job:** Content Analyzer - Extracts learning materials

**What it does:**
1. 📖 Reads full text from PDF
2. 🎯 Asks Gemini: "Extract 5-10 main topics from this text"
3. 📝 Asks Gemini: "Extract key vocabulary with definitions"
4. ✏️ Asks Gemini: "Extract grammar points" (for language PDFs)
5. ✂️ Splits text into chunks (1000 chars, 200 overlap)
6. 💾 Stores chunks in Chroma vector database for searching

**Input:**
```python
{
    "file_path": "/uploads/sample.pdf",
    "pdf_id": "642e20c7-39ba-4c5b-ab1e-562ec3dcffde",
    "language": "en"
}
```

**Output:**
```python
{
    "success": True,
    "data": {
        "topics": [
            {
                "name": "Introduction to Python",
                "description": "Basic syntax and concepts",
                "difficulty": "Beginner",
                "key_vocabulary": ["variable", "function", "loop"]
            }
        ],
        "key_vocabulary": [
            {
                "word": "variable",
                "definition": "A storage location with a name",
                "difficulty": "Beginner"
            }
        ],
        "grammar_points": [],
        "chunks_indexed": 42
    }
}
```

**When it runs:** Immediately after PDF upload is validated

**API Endpoint:** Called internally during `POST /api/pdfs/upload`

---

### **AGENT 3: Context Guard Agent** 🛡️

**File:** `backend/agents/context_guard_agent.py`

**Job:** Gatekeeper - Prevents irrelevant questions

**What it does:**
1. 📋 Gets list of topics from PDF (from database)
2. ❓ Receives user's question
3. 🤖 Asks Gemini: "Is this question relevant to these topics?"
4. ✅ Returns: Yes/No + reason + related topics

**Input:**
```python
{
    "topics": [
        {"name": "Python Basics"},
        {"name": "Functions"}
    ],
    "query": "How do I define a function in Python?"
}
```

**Output:**
```python
{
    "success": True,
    "data": {
        "is_relevant": True,
        "reason": "Question is about functions, which is covered in the PDF",
        "related_topics": ["Python Basics", "Functions"]
    }
}
```

**Example - Irrelevant Question:**
```
Question: "What's the weather today?"
Result: {
    "is_relevant": False,
    "reason": "Weather is not related to PDF topics about Python"
}
```

**When it runs:** Before answering any user question

**API Endpoint:** Called internally during `POST /api/chat/question`

---

### **AGENT 4: QA Agent** 💬

**File:** `backend/agents/qa_agent.py`

**Job:** Knowledge Expert - Answers questions using PDF content

**What it does:**
1. 🔍 Receives question from user
2. 🗄️ Searches Chroma vector DB for similar text chunks
3. 📄 Retrieves top 5 most relevant chunks
4. 📋 Compiles chunks into context
5. 🤖 Sends to Gemini: "Context: {chunks}. Question: {question}. Answer based ONLY on context."
6. 💯 Calculates confidence score (how sure the answer is)
7. 📖 Identifies source page number
8. 🎚️ Adjusts language complexity based on user level

**Input:**
```python
{
    "question": "How do I define a function?",
    "pdf_id": "642e20c7-39ba-4c5b-ab1e-562ec3dcffde",
    "language_level": "Intermediate"
}
```

**Process:**
```
1. Search vector DB → Find chunks about "functions"
2. Get top 5 chunks:
   - "Functions are defined using def..."
   - "Example: def my_function():"
   - "Functions can take parameters..."
3. Send to Gemini with question
4. Gemini generates answer using only these chunks
```

**Output:**
```python
{
    "success": True,
    "data": {
        "answer": "In Python, you define a function using the 'def' keyword followed by the function name and parentheses. Example: def my_function(): ...",
        "source_page": 3,
        "confidence": 0.92,
        "language_level": "Intermediate",
        "context_used": 5
    }
}
```

**When it runs:** When user asks a question

**API Endpoint:** `POST /api/chat/question`

**Frontend:** Available in Agent Selector dropdown → "💬 Ask Question"

---

### **AGENT 5: Translator Agent** 🌍

**File:** `backend/agents/translator_agent.py`

**Job:** Linguist - Translates content to other languages

**What it does:**
1. 📄 Receives PDF content or topics
2. 🎯 Gets target language (Spanish, French, Hindi, etc.)
3. 🤖 Sends to Gemini: "Translate this to {language}. Maintain educational structure."
4. 🔤 Adds pronunciation hints (for Hindi, Chinese, etc.)
5. 📚 Translates topic names and descriptions
6. ✅ Returns translated content

**Input:**
```python
{
    "file_id": "642e20c7-39ba-4c5b-ab1e-562ec3dcffde",
    "target_language": "es"  # Spanish
}
```

**Output:**
```python
{
    "success": True,
    "data": {
        "translated_topics": [
            {
                "name": "Introducción a Python",
                "description": "Sintaxis básica y conceptos",
                "difficulty": "Principiante"
            }
        ],
        "translated": "Python es un lenguaje de programación...",
        "target_language": "es"
    }
}
```

**Supported Languages:**
- Spanish (es)
- French (fr)
- German (de)
- Hindi (hi)
- Chinese (zh)
- Japanese (ja)
- Portuguese (pt)

**When it runs:** When user requests translation

**API Endpoint:** `POST /api/translate`

**Frontend:** Available in Agent Selector dropdown → "🌍 Translate Content"

---

### **AGENT 6: Language Coach Agent** 🎓

**File:** `backend/agents/language_coach_agent.py`

**Job:** Language Teacher - Provides grammar & vocabulary feedback

**What it does:**
1. 📝 Receives text from user (e.g., "I is going to school")
2. 🤖 Sends to Gemini: "Analyze this sentence for language learners. Find: grammar mistakes, vocabulary suggestions, fluency notes, encouragement"
3. ✏️ Gemini detects mistakes: "I is" → "I am"
4. 📚 Suggests better vocabulary: "going" → "traveling", "walking"
5. 💬 Evaluates fluency: "Good sentence structure!"
6. 💪 Provides encouragement: "Great job! Keep practicing!"
7. 💾 Logs mistake to database for future reports

**Input:**
```python
{
    "user_output": "I is going to school",
    "language": "en"
}
```

**Output:**
```python
{
    "success": True,
    "data": {
        "grammar_feedback": "Small correction needed: 'I is' should be 'I am'. The verb 'to be' changes based on the subject.",
        "vocabulary_suggestions": [
            {"word": "traveling", "context": "Alternative to 'going'"},
            {"word": "walking", "context": "More specific"},
            {"word": "heading", "context": "Casual alternative"}
        ],
        "fluency_notes": "The sentence structure is good! Just needs the grammar fix.",
        "confidence": 0.98,
        "encouragement": "You're doing great! This is a common mistake. Keep practicing!"
    }
}
```

**When it runs:** When user submits text for feedback

**API Endpoint:** `POST /api/language-feedback`

**Frontend:** Available in Agent Selector dropdown → "🎓 Get Language Feedback"

---

### **AGENT 7: Flag Reporter Agent** 📊

**File:** `backend/agents/flag_reporter_agent.py`

**Job:** Progress Analyst - Generates personalized learning reports

**What it does:**
1. 📊 Retrieves all Q&A sessions for a PDF/user
2. 📝 Retrieves all language mistakes logged
3. 🧮 Calculates accuracy: (correct answers / total questions) × 100
4. 🔍 Identifies learning gaps:
   - Topics with low confidence scores
   - Repeated mistake types
   - Weak areas
5. 🤖 Sends analysis to Gemini: "Based on this data, generate 3-5 recommendations"
6. 💡 Returns personalized action items

**Input:**
```python
{
    "pdf_id": "642e20c7-39ba-4c5b-ab1e-562ec3dcffde",
    "user_id": "123e4567-e89b-12d3-a456-426614174000"
}
```

**Analysis Process:**
```
1. Get Q&A sessions:
   - 20 questions asked
   - 17 with high confidence (>0.8)
   - 3 with low confidence (<0.7)

2. Get mistakes:
   - 5 grammar mistakes
   - 3 vocabulary mistakes
   - Topics: "Advanced grammar", "Idioms"

3. Calculate:
   - Accuracy: 17/20 = 85%
   - Gaps: ["Advanced grammar", "Idioms"]

4. Ask Gemini for recommendations
```

**Output:**
```python
{
    "success": True,
    "data": {
        "summary": "You've asked 20 questions with 85% accuracy. You're making good progress!",
        "accuracy": 85,
        "learning_gaps": [
            "Advanced grammar structures",
            "Idiomatic expressions",
            "Verb conjugation in past tense"
        ],
        "recommendations": [
            "Practice verb conjugation exercises",
            "Study common idioms and their usage",
            "Review advanced grammar rules",
            "Read more intermediate-level texts",
            "Focus on past tense practice"
        ]
    }
}
```

**When it runs:** When user requests a learning report

**API Endpoint:** `GET /api/reports/{file_id}?user_id={user_id}`

**Frontend:** Available in Agent Selector dropdown → "📊 Generate Learning Report"

---

## 🔄 HOW AGENTS WORK TOGETHER

### **Complete Workflow: From Upload to Report**

```
USER UPLOADS PDF
       ↓
   AGENT 1 (PDF Upload)
   ├─ Validates file
   ├─ Extracts text
   ├─ Detects language
   └─ Analyzes topic
       ↓
   AGENT 2 (Extraction)
   ├─ Extracts topics
   ├─ Extracts vocabulary
   ├─ Creates chunks
   └─ Indexes in vector DB
       ↓
   ✅ PDF READY FOR USE
       ↓
   ┌────────────────────────────┐
   │                            │
   ▼                            ▼
USER ASKS QUESTION      USER SUBMITS TEXT
       ↓                        ↓
   AGENT 3 (Guard)        AGENT 6 (Coach)
   ├─ Check relevance     ├─ Analyze grammar
   └─ Is relevant?        ├─ Suggest vocab
       ↓ YES              └─ Encourage
   AGENT 4 (QA)               ↓
   ├─ Search chunks       LOG MISTAKE
   ├─ Ask Gemini              ↓
   └─ Return answer       SAVE TO DB
       ↓
   LOG Q&A SESSION
       ↓
   SAVE TO DB
       │
       └───────────────────────┐
                               ▼
                       USER REQUESTS REPORT
                               ↓
                       AGENT 7 (Reporter)
                       ├─ Analyze sessions
                       ├─ Find gaps
                       ├─ Calculate accuracy
                       └─ Generate recommendations
                               ↓
                       ✅ LEARNING REPORT
```

---

## 📊 AGENT COMPARISON TABLE

| Agent | Primary Function | Uses Gemini? | Uses Vector DB? | User-Facing? |
|-------|-----------------|--------------|-----------------|--------------|
| **1. Upload** | Validate & analyze PDF | ✅ Yes | ❌ No | ❌ No (internal) |
| **2. Extraction** | Extract topics/vocab | ✅ Yes | ✅ Yes (stores) | ❌ No (internal) |
| **3. Guard** | Check relevance | ✅ Yes | ❌ No | ❌ No (internal) |
| **4. QA** | Answer questions | ✅ Yes | ✅ Yes (retrieves) | ✅ Yes |
| **5. Translator** | Translate content | ✅ Yes | ❌ No | ✅ Yes |
| **6. Coach** | Provide feedback | ✅ Yes | ❌ No | ✅ Yes |
| **7. Reporter** | Generate reports | ✅ Yes | ❌ No | ✅ Yes |

---

## 🎯 WHEN EACH AGENT RUNS

### **Automatic (Internal)**
- ✅ **Agent 1** - Runs on every PDF upload
- ✅ **Agent 2** - Runs immediately after Agent 1
- ✅ **Agent 3** - Runs before answering any question

### **On-Demand (User Triggered)**
- 🎯 **Agent 4** - When user asks a question
- 🌍 **Agent 5** - When user requests translation
- 🎓 **Agent 6** - When user submits text for feedback
- 📊 **Agent 7** - When user requests a learning report

---

## 💡 KEY CONCEPTS

### **1. Agent Inheritance**
```
BaseAgent (abstract)
  ├─ LLMAgent (uses Gemini)
  │   ├─ Agent 1 (Upload)
  │   ├─ Agent 3 (Guard)
  │   ├─ Agent 5 (Translator)
  │   ├─ Agent 6 (Coach)
  │   └─ Agent 7 (Reporter)
  └─ StorageAgent (uses Vector DB)
      ├─ Agent 2 (Extraction)
      └─ Agent 4 (QA)
```

### **2. Standardized Response**
All agents return the same format:
```python
{
    "success": bool,
    "data": dict,
    "error": str or None,
    "execution_time": float
}
```

### **3. Error Handling**
Every agent has:
- Try-except blocks
- Fallback responses
- Detailed logging
- User-friendly error messages

### **4. Database Logging**
Agents log to database:
- Agent 1 → `pdfs` table
- Agent 2 → `topics` table
- Agent 4 → `qa_sessions` table
- Agent 6 → `language_mistakes` table
- Agent 7 → `learning_reports` table

---

## 🚀 SUMMARY

### **The Assembly Line:**

1. **Agent 1 (Inspector)** → Checks if PDF is valid ✅
2. **Agent 2 (Analyzer)** → Extracts all learning content 📚
3. **Agent 3 (Gatekeeper)** → Blocks bad questions 🛡️
4. **Agent 4 (Expert)** → Answers questions with sources 💬
5. **Agent 5 (Linguist)** → Translates to other languages 🌍
6. **Agent 6 (Teacher)** → Corrects your mistakes 🎓
7. **Agent 7 (Analyst)** → Shows your progress 📊

### **All Working Together:**
- Upload PDF → Agents 1 & 2 process it
- Ask questions → Agents 3 & 4 answer
- Get feedback → Agent 6 helps you
- See progress → Agent 7 reports

**Result: Complete intelligent learning platform!** 🎉

---

**File:** `/home/santoshyadav_951942/Language_Learning_Chatbot_Project/7_AGENTS_WORKING_LIST.md`  
**Created:** December 5, 2025  
**Status:** ✅ All 7 agents implemented and tested

