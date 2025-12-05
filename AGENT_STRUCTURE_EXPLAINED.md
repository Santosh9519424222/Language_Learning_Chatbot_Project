# 🤖 AGENT STRUCTURE - How Agents Process Uploaded PDFs

**Complete Guide to the 7 AI Agents Architecture**

---

## 📊 OVERVIEW: Multi-Agent System Architecture

Your project uses a **multi-agent architecture** where each agent has a specific responsibility. Think of it like a **factory assembly line** where each worker (agent) performs one specialized task.

---

## 🏗️ BASE AGENT STRUCTURE

### **1. BaseAgent (Abstract Class)**

All agents inherit from this base class located in `backend/agents/base_agent.py`

```python
class BaseAgent:
    """
    Abstract base class for all AI agents
    Provides common functionality
    """
    
    def __init__(self, name: str, model: str = "gemini-pro"):
        self.name = name              # Agent identifier
        self.model = model            # LLM model to use
        self.logger = logging.getLogger(name)
    
    @abstractmethod
    def process(self, **kwargs) -> AgentResponse:
        """
        Main processing method
        Must be implemented by each agent
        """
        pass
    
    def _create_response(self, success, data, error, execution_time):
        """
        Standardized response format
        All agents return the same structure
        """
        return {
            "success": bool,
            "data": dict,
            "error": str or None,
            "execution_time": float,
            "model": str,
            "tokens_used": int or None
        }
```

### **2. Specialized Base Classes**

```python
class LLMAgent(BaseAgent):
    """
    For agents that use Gemini AI
    """
    def __init__(self, gemini_client, name, model):
        super().__init__(name, model)
        self.gemini_client = gemini_client
    
    def generate_text(self, prompt, temperature, max_tokens):
        """Call Gemini API with error handling"""
        return self.gemini_client.generate_content(...)


class StorageAgent(BaseAgent):
    """
    For agents that access vector storage
    """
    def __init__(self, vector_store, name, model):
        super().__init__(name, model)
        self.vector_store = vector_store
    
    def search_similar(self, query, pdf_id, top_k):
        """Search Chroma DB for similar content"""
        return self.vector_store.retrieve_relevant_chunks(...)
```

---

## 📋 THE 7 AGENTS - Complete Structure

### **AGENT 1: PDFUploadAgent** 🔍

**File:** `backend/agents/pdf_upload_agent.py`

**Class Structure:**
```python
class PDFUploadAgent(LLMAgent):
    """
    First agent in the pipeline
    Validates and processes uploaded PDFs
    """
    
    def __init__(self, gemini_client):
        super().__init__(gemini_client, name="pdf_upload")
    
    def process(self, file_path, user_id, enable_ocr=False):
        """
        Main processing method
        
        Steps:
        1. Validate PDF file
        2. Extract text
        3. Get metadata
        4. Detect language
        5. AI analysis
        """
        
        # Step 1: Validate
        validation = validate_pdf(file_path)
        if not validation['valid']:
            return error_response
        
        # Step 2: Extract text
        text_data = extract_text_from_pdf(file_path)
        full_text = text_data['full_text']
        
        # Step 3: Metadata
        metadata = get_pdf_metadata(file_path)
        
        # Step 4: Language detection
        language = detect_language(full_text)
        
        # Step 5: AI analysis
        ai_result = self._analyze_content_with_ai(full_text[:5000])
        
        return {
            "success": True,
            "data": {
                "file_size": validation['file_size'],
                "page_count": validation['page_count'],
                "detected_language": language,
                "metadata": metadata,
                "ai_analysis": {
                    "topic": "Computer Science",
                    "difficulty": "Intermediate"
                }
            }
        }
    
    def _analyze_content_with_ai(self, text):
        """
        Send text to Gemini for analysis
        """
        prompt = f"""Analyze this PDF and identify:
        - Main topic
        - Difficulty level (Beginner/Intermediate/Advanced)
        - Key subjects
        
        Text: {text}
        
        Return JSON format"""
        
        response = self.generate_text(prompt, temperature=0.3)
        return parse_json(response)
```

**Input:**
```python
{
    "file_path": "/path/to/uploaded.pdf",
    "user_id": "123e4567-e89b-12d3-a456-426614174000",
    "enable_ocr": False
}
```

**Output:**
```python
{
    "success": True,
    "data": {
        "file_size": 1024000,      # bytes
        "page_count": 10,
        "detected_language": "en",
        "metadata": {
            "title": "Learning Python",
            "author": "John Doe",
            "creation_date": "2024-01-01"
        },
        "ai_analysis": {
            "topic": "Programming - Python",
            "difficulty": "Intermediate",
            "subjects": "functions, classes, OOP"
        }
    },
    "execution_time": 2.5
}
```

---

### **AGENT 2: ExtractionAgent** 📚

**File:** `backend/agents/extraction_agent.py`

**Class Structure:**
```python
class ExtractionAgent(LLMAgent, StorageAgent):
    """
    Extracts educational content from PDFs
    Uses both Gemini AI and Vector Store
    """
    
    def __init__(self, gemini_client, vector_store):
        LLMAgent.__init__(self, gemini_client, "extraction")
        self.vector_store = vector_store
    
    def process(self, file_path, pdf_id, language):
        """
        Extract learning content
        
        Steps:
        1. Extract full text
        2. Extract topics using AI
        3. Extract vocabulary
        4. Extract grammar points
        5. Create text chunks
        6. Index in vector store
        """
        
        # Step 1: Get text
        extraction = extract_text_from_pdf(file_path)
        full_text = extraction['full_text']
        
        # Step 2: Extract topics
        topics = self._extract_topics(full_text, language)
        # Returns: [
        #   {
        #     "name": "Chapter 1: Introduction",
        #     "description": "Basic concepts...",
        #     "difficulty": "Beginner",
        #     "key_vocabulary": "variable, function, loop"
        #   }
        # ]
        
        # Step 3: Extract vocabulary
        vocabulary = self._extract_vocabulary(full_text, language)
        # Returns: [
        #   {
        #     "word": "variable",
        #     "definition": "A storage location...",
        #     "difficulty": "Beginner"
        #   }
        # ]
        
        # Step 4: Grammar points (for language learning)
        grammar = self._extract_grammar_points(full_text, language)
        
        # Step 5: Create chunks
        chunks = extract_text_chunks(file_path, chunk_size=1000)
        # Returns: [
        #   {
        #     "text": "Variables are...",
        #     "page": 1,
        #     "chunk_id": 0
        #   }
        # ]
        
        # Step 6: Index chunks
        if self.vector_store:
            self.vector_store.add_pdf_chunks(pdf_id, chunks)
        
        return {
            "success": True,
            "data": {
                "topics": topics,
                "key_vocabulary": vocabulary,
                "grammar_points": grammar,
                "chunks_indexed": len(chunks)
            }
        }
    
    def _extract_topics(self, text, language):
        """
        Use Gemini to extract topics
        """
        prompt = f"""Extract main topics from this text.
        For each topic provide: name, description, difficulty.
        
        Text: {text[:3000]}
        
        Return JSON array"""
        
        response = self.generate_text(prompt, temperature=0.5)
        return parse_json(response)
    
    def _extract_vocabulary(self, text, language):
        """
        Use Gemini to extract vocabulary
        """
        prompt = f"""Extract 10-15 key vocabulary terms.
        For each: word, definition, difficulty level.
        
        Text: {text[:2000]}
        
        Return JSON array"""
        
        response = self.generate_text(prompt, temperature=0.3)
        return parse_json(response)
```

**Input:**
```python
{
    "file_path": "/path/to/uploaded.pdf",
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
                "key_vocabulary": "variable, function, print"
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
        "chunks_indexed": 42,
        "text_length": 15000,
        "pages_processed": 10
    },
    "execution_time": 5.2
}
```

---

### **AGENT 3: ContextGuardAgent** 🛡️

**File:** `backend/agents/context_guard_agent.py`

**Class Structure:**
```python
class ContextGuardAgent(LLMAgent):
    """
    Validates that user questions are relevant to PDF
    Prevents users from asking unrelated questions
    """
    
    def process(self, topics, query):
        """
        Check if query is relevant to PDF topics
        
        Steps:
        1. Get PDF topics
        2. Analyze user query
        3. Check relevance
        4. Return verdict
        """
        
        # Compile topics into context
        topics_text = "\n".join([t['name'] for t in topics])
        
        # Ask Gemini to check relevance
        prompt = f"""
        PDF Topics: {topics_text}
        User Question: {query}
        
        Is this question relevant to the PDF topics?
        Return JSON: {{"is_relevant": true/false, "reason": "..."}}
        """
        
        response = self.generate_text(prompt, temperature=0.2)
        result = parse_json(response)
        
        return {
            "success": True,
            "data": {
                "is_relevant": result['is_relevant'],
                "reason": result['reason'],
                "related_topics": topics[:3]
            }
        }
```

**Input:**
```python
{
    "topics": [
        {"name": "Python Basics", "description": "..."},
        {"name": "Functions", "description": "..."}
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
        "reason": "Question is about functions which is covered in the PDF",
        "related_topics": ["Python Basics", "Functions"]
    }
}
```

---

### **AGENT 4: QAAgent** 💬

**File:** `backend/agents/qa_agent.py`

**Class Structure:**
```python
class QAAgent(LLMAgent, StorageAgent):
    """
    Answers questions about PDF content
    Uses RAG (Retrieval-Augmented Generation)
    """
    
    def __init__(self, gemini_client, vector_store):
        LLMAgent.__init__(self, gemini_client, "qa")
        self.vector_store = vector_store
    
    def process(self, question, pdf_id, language_level="Intermediate"):
        """
        Answer user question
        
        Steps:
        1. Retrieve relevant chunks from vector store
        2. Compile context
        3. Send to Gemini with context
        4. Generate answer
        5. Calculate confidence
        6. Adjust for user level
        """
        
        # Step 1: Retrieve context
        context_chunks = []
        if self.vector_store:
            success, chunks = self.search_similar(
                query=question,
                pdf_id=pdf_id,
                top_k=5
            )
            if success:
                context_chunks = chunks
        
        # Step 2: Compile context
        context = "\n\n".join([c['text'] for c in context_chunks])
        
        # Step 3: Generate answer
        prompt = f"""
        Context from PDF:
        {context}
        
        User Question: {question}
        User Level: {language_level}
        
        Answer the question based ONLY on the context above.
        Adjust language complexity for {language_level} level.
        Cite the page number if possible.
        """
        
        answer = self.generate_text(prompt, temperature=0.5)
        
        # Step 4: Calculate confidence
        confidence = self._calculate_confidence(answer, context)
        
        # Step 5: Identify source
        source_page = context_chunks[0]['page'] if context_chunks else 1
        
        return {
            "success": True,
            "data": {
                "answer": answer,
                "source_page": source_page,
                "confidence": confidence,
                "language_level": language_level,
                "context_used": len(context_chunks)
            }
        }
    
    def _calculate_confidence(self, answer, context):
        """
        Calculate how confident we are in the answer
        Based on context overlap
        """
        if not context:
            return 0.5  # Low confidence without context
        
        # Check if answer references context
        words_in_context = set(context.lower().split())
        words_in_answer = set(answer.lower().split())
        overlap = len(words_in_context & words_in_answer)
        
        return min(0.9, overlap / 100)  # Cap at 0.9
```

**Input:**
```python
{
    "question": "How do I define a function?",
    "pdf_id": "642e20c7-39ba-4c5b-ab1e-562ec3dcffde",
    "language_level": "Intermediate"
}
```

**Output:**
```python
{
    "success": True,
    "data": {
        "answer": "In Python, you define a function using the 'def' keyword followed by the function name and parentheses. For example: def my_function(): ...",
        "source_page": 3,
        "confidence": 0.92,
        "language_level": "Intermediate",
        "context_used": 5
    },
    "execution_time": 1.8
}
```

---

### **AGENT 5: TranslatorAgent** 🌍

**File:** `backend/agents/translator_agent.py`

**Class Structure:**
```python
class TranslatorAgent(LLMAgent):
    """
    Translates PDF content to target languages
    """
    
    def process(self, content, topics, target_language):
        """
        Translate content
        
        Steps:
        1. Get content to translate
        2. Send to Gemini for translation
        3. Add pronunciation hints (for Hindi, etc.)
        4. Return translated content
        """
        
        # Translate main content
        prompt = f"""
        Translate this text to {target_language}.
        Maintain educational structure and clarity.
        
        Text: {content[:1000]}
        
        Return translated text only.
        """
        
        translated = self.generate_text(prompt, temperature=0.3)
        
        # Translate topics
        translated_topics = []
        for topic in topics[:10]:
            topic_prompt = f"""
            Translate this topic to {target_language}:
            Name: {topic['name']}
            Description: {topic['description']}
            
            Return JSON with translated name and description.
            """
            result = self.generate_text(topic_prompt, temperature=0.3)
            translated_topics.append(parse_json(result))
        
        return {
            "success": True,
            "data": {
                "original": content[:100],
                "translated": translated,
                "translated_topics": translated_topics,
                "target_language": target_language
            }
        }
```

---

### **AGENT 6: LanguageCoachAgent** 🎓

**File:** `backend/agents/language_coach_agent.py`

**Class Structure:**
```python
class LanguageCoachAgent(LLMAgent):
    """
    Provides language learning feedback
    Most important for your project!
    """
    
    def process(self, user_output, language="en"):
        """
        Analyze user's language output
        
        Steps:
        1. Send to Gemini for analysis
        2. Detect grammar mistakes
        3. Suggest vocabulary improvements
        4. Provide encouragement
        5. Calculate confidence
        """
        
        prompt = f"""
        Analyze this {language} sentence for language learners:
        
        Sentence: "{user_output}"
        
        Provide:
        1. Grammar feedback (corrections needed)
        2. Vocabulary suggestions (better words)
        3. Fluency notes (how natural it sounds)
        4. Encouragement (positive feedback)
        
        Return JSON format.
        """
        
        response = self.generate_text(prompt, temperature=0.5)
        analysis = parse_json(response)
        
        return {
            "success": True,
            "data": {
                "grammar_feedback": analysis.get('grammar', 'Good!'),
                "vocabulary_suggestions": analysis.get('vocabulary', []),
                "fluency_notes": analysis.get('fluency', 'Natural'),
                "confidence": 0.95,
                "encouragement": "Great job! Keep practicing!"
            }
        }
```

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
            {"word": "heading", "context": "More casual alternative"}
        ],
        "fluency_notes": "The sentence structure is good! Just needs the grammar fix.",
        "confidence": 0.98,
        "encouragement": "You're doing great! This is a common mistake. Keep practicing!"
    }
}
```

---

### **AGENT 7: FlagReporterAgent** 📊

**File:** `backend/agents/flag_reporter_agent.py`

**Class Structure:**
```python
class FlagReporterAgent(LLMAgent):
    """
    Generates personalized learning reports
    """
    
    def process(self, session_data, user_id):
        """
        Generate learning report
        
        Steps:
        1. Retrieve all Q&A sessions
        2. Retrieve all language mistakes
        3. Calculate accuracy
        4. Identify learning gaps
        5. Generate recommendations
        """
        
        # Analyze session data
        qa_sessions = session_data['qa_sessions']
        mistakes = session_data['mistakes']
        
        # Calculate accuracy
        total_questions = len(qa_sessions)
        high_confidence = sum(1 for q in qa_sessions if q['confidence'] > 0.8)
        accuracy = (high_confidence / total_questions) * 100 if total_questions > 0 else 0
        
        # Identify gaps
        gap_topics = self._identify_gaps(qa_sessions, mistakes)
        
        # Generate recommendations using Gemini
        prompt = f"""
        User Learning Data:
        - Questions asked: {total_questions}
        - Accuracy: {accuracy}%
        - Common mistakes: {[m['mistake_type'] for m in mistakes[:5]]}
        - Weak topics: {gap_topics}
        
        Generate 3-5 personalized recommendations for improvement.
        Return JSON array of recommendations.
        """
        
        recommendations = self.generate_text(prompt, temperature=0.6)
        
        return {
            "success": True,
            "data": {
                "summary": f"You've asked {total_questions} questions with {accuracy:.1f}% accuracy",
                "accuracy": accuracy,
                "learning_gaps": gap_topics,
                "recommendations": parse_json(recommendations)
            }
        }
    
    def _identify_gaps(self, qa_sessions, mistakes):
        """
        Identify topics user struggles with
        """
        low_confidence_topics = [
            q['topic'] for q in qa_sessions 
            if q['confidence'] < 0.7
        ]
        
        mistake_topics = [m['context'] for m in mistakes]
        
        # Combine and count
        all_gaps = low_confidence_topics + mistake_topics
        return list(set(all_gaps))[:5]  # Top 5 unique gaps
```

---

## 🔄 COMPLETE WORKFLOW: How Agents Work Together

### **PDF Upload Flow:**

```
┌────────────────────────────────────────────────────────────┐
│ USER UPLOADS PDF                                           │
└─────────────────────┬──────────────────────────────────────┘
                      │
                      ▼
┌────────────────────────────────────────────────────────────┐
│ AGENT 1: PDFUploadAgent                                    │
│ ├─ Validates: Size < 50MB? Pages < 500? Format = PDF?     │
│ ├─ Extracts: Full text using pdfplumber                   │
│ ├─ Detects: Language (English, Hindi, Spanish, etc.)      │
│ ├─ Analyzes: Topic, difficulty with Gemini AI             │
│ └─ Returns: {file_size, pages, language, topic}           │
└─────────────────────┬──────────────────────────────────────┘
                      │
                      ▼
┌────────────────────────────────────────────────────────────┐
│ SAVE TO DATABASE: pdfs table                               │
│ ├─ id: UUID                                                │
│ ├─ filename: "learning.pdf"                                │
│ ├─ language: "en"                                          │
│ ├─ pages: 10                                               │
│ └─ status: "processing"                                    │
└─────────────────────┬──────────────────────────────────────┘
                      │
                      ▼
┌────────────────────────────────────────────────────────────┐
│ AGENT 2: ExtractionAgent                                   │
│ ├─ Extracts: 5-10 main topics using Gemini                │
│ ├─ Extracts: Vocabulary with definitions                  │
│ ├─ Extracts: Grammar points (if language PDF)             │
│ ├─ Creates: Text chunks (1000 chars, 200 overlap)         │
│ └─ Indexes: Chunks in Chroma vector DB                    │
└─────────────────────┬──────────────────────────────────────┘
                      │
                      ▼
┌────────────────────────────────────────────────────────────┐
│ SAVE TO DATABASE: topics table                             │
│ ├─ For each topic:                                         │
│ │   ├─ topic_name: "Introduction"                         │
│ │   ├─ description: "Basic concepts..."                   │
│ │   ├─ vocabulary: [{word, definition}]                   │
│ │   └─ difficulty: "Beginner"                             │
└─────────────────────┬──────────────────────────────────────┘
                      │
                      ▼
┌────────────────────────────────────────────────────────────┐
│ UPDATE DATABASE: pdfs.status = "completed"                 │
└─────────────────────┬──────────────────────────────────────┘
                      │
                      ▼
┌────────────────────────────────────────────────────────────┐
│ RETURN TO FRONTEND: "✅ PDF ready for Q&A!"                │
└────────────────────────────────────────────────────────────┘
```

### **Question Answering Flow:**

```
┌────────────────────────────────────────────────────────────┐
│ USER ASKS: "What is the main topic?"                       │
└─────────────────────┬──────────────────────────────────────┘
                      │
                      ▼
┌────────────────────────────────────────────────────────────┐
│ AGENT 3: ContextGuardAgent                                 │
│ ├─ Gets: PDF topics from database                         │
│ ├─ Checks: Is question relevant to topics?                │
│ ├─ Asks Gemini: "Is this question about the PDF?"         │
│ └─ Returns: {is_relevant: true, reason: "..."}            │
└─────────────────────┬──────────────────────────────────────┘
                      │
                      ▼ IF RELEVANT
┌────────────────────────────────────────────────────────────┐
│ CHROMA VECTOR SEARCH                                        │
│ ├─ Convert question to embedding (vector)                 │
│ ├─ Search similar chunks in Chroma DB                     │
│ ├─ Retrieve top 5 most relevant chunks                    │
│ └─ Returns: [{text, page, similarity_score}]              │
└─────────────────────┬──────────────────────────────────────┘
                      │
                      ▼
┌────────────────────────────────────────────────────────────┐
│ AGENT 4: QAAgent                                           │
│ ├─ Compiles context from chunks                           │
│ ├─ Sends to Gemini: "Context: {chunks}, Question: {q}"    │
│ ├─ Gemini generates answer based on context               │
│ ├─ Calculates confidence score (0-1)                      │
│ └─ Identifies source page                                 │
└─────────────────────┬──────────────────────────────────────┘
                      │
                      ▼
┌────────────────────────────────────────────────────────────┐
│ SAVE TO DATABASE: qa_sessions table                        │
│ ├─ question: "What is the main topic?"                    │
│ ├─ answer: "The main topic is..."                         │
│ ├─ confidence_score: 0.92                                 │
│ ├─ source_page: 1                                         │
│ └─ timestamp: now()                                       │
└─────────────────────┬──────────────────────────────────────┘
                      │
                      ▼
┌────────────────────────────────────────────────────────────┐
│ RETURN TO FRONTEND:                                         │
│ {                                                          │
│   "answer": "The main topic is...",                       │
│   "source_page": 1,                                       │
│   "confidence": 0.92                                      │
│ }                                                          │
└────────────────────────────────────────────────────────────┘
```

---

## 🎯 KEY DESIGN PATTERNS

### **1. Single Responsibility Principle**
Each agent has ONE job:
- PDFUploadAgent → Only validates & uploads
- ExtractionAgent → Only extracts content
- QAAgent → Only answers questions

### **2. Standardized Response Format**
All agents return the same structure:
```python
{
    "success": bool,
    "data": dict,
    "error": str or None,
    "execution_time": float
}
```

### **3. Error Handling**
Every agent has try-except blocks:
```python
try:
    result = agent.process(...)
    if not result['success']:
        handle_error(result['error'])
except Exception as e:
    log_error(e)
    return fallback_response
```

### **4. Logging**
Every agent logs its actions:
```python
logger.info(f"[PDFUploadAgent] Processing file: {filename}")
logger.warning(f"[QAAgent] Low confidence: {confidence}")
logger.error(f"[ExtractionAgent] Failed: {error}")
```

---

## 💡 SUMMARY

**Your agent structure is like a factory assembly line:**

1. **PDFUploadAgent** = Quality Control Inspector
   - Checks if PDF is valid
   - Extracts basic info

2. **ExtractionAgent** = Content Analyzer
   - Reads everything
   - Finds important parts
   - Creates searchable index

3. **ContextGuardAgent** = Gatekeeper
   - Makes sure questions are relevant
   - Prevents spam/unrelated queries

4. **QAAgent** = Knowledge Expert
   - Uses context to answer questions
   - Provides sources

5. **TranslatorAgent** = Linguist
   - Translates to other languages
   - Maintains meaning

6. **LanguageCoachAgent** = Teacher
   - Corrects mistakes
   - Encourages learning

7. **FlagReporterAgent** = Report Writer
   - Analyzes progress
   - Provides recommendations

**Each agent is independent but works together in sequence to process PDFs and provide intelligent responses!**

---

**File Location:** `/home/santoshyadav_951942/Language_Learning_Chatbot_Project/AGENT_STRUCTURE_EXPLAINED.md`

