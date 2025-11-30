# 🚀 QUICK START GUIDE

## Get Your Multi-Agent PDF Intelligence Platform Running in 10 Minutes!

### Prerequisites
- Python 3.11+
- PostgreSQL
- Git
- Gemini API Key ([Get it FREE here](https://ai.google.dev/))

---

## Step 1: Setup Environment (2 minutes)

```bash
cd /home/santoshyadav_951942/Language_Learning_Chatbot_Project

# Create .env file
cp .env.example .env

# Edit .env and add your GEMINI_API_KEY
nano .env
```

**Required in .env**:
```bash
GEMINI_API_KEY=your_gemini_api_key_here
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/pdf_learning_db
```

---

## Step 2: Install Dependencies (3 minutes)

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm
```

---

## Step 3: Setup Database (2 minutes)

```bash
# Start PostgreSQL
sudo service postgresql start

# Create database
sudo -u postgres createdb pdf_learning_db

# Initialize tables
python3 -c "from models.database import init_db; init_db()"
```

---

## Step 4: Run Server (1 minute)

```bash
# Start the server
uvicorn main:app --reload --port 8080
```

**Server will start at**: http://localhost:8080

---

## Step 5: Test API (2 minutes)

Open your browser:
- **API Docs**: http://localhost:8080/docs
- **Health Check**: http://localhost:8080/health

Or run the test suite:
```bash
# In a new terminal
cd backend
python3 test_api.py
```

---

## 🎉 You're Done!

Your Multi-Agent PDF Intelligence Platform is now running!

### Try These Commands:

**Create a user**:
```bash
curl -X POST http://localhost:8080/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "username": "learner",
    "email": "learner@example.com",
    "language_focus": "Spanish",
    "proficiency_level": "Beginner"
  }'
```

**Upload a PDF**:
```bash
curl -X POST http://localhost:8080/api/pdfs/upload \
  -F "file=@your_pdf.pdf" \
  -F "user_id=YOUR_USER_ID"
```

**Check health**:
```bash
curl http://localhost:8080/health
```

---

## 📚 Next Steps

1. **Read the full documentation**: `README.md`
2. **Explore the API**: http://localhost:8080/docs
3. **Run all tests**: `python3 test_api.py`
4. **Deploy to cloud**: See `FINAL_COMPLETION.md`

---

## 🆘 Troubleshooting

**Database connection fails?**
```bash
sudo service postgresql start
sudo -u postgres createdb pdf_learning_db
```

**Import errors?**
```bash
pip install -r requirements.txt --force-reinstall
```

**Gemini API errors?**
- Check your API key in `.env`
- Verify at: https://ai.google.dev/

---

## ✅ Verify Everything Works

- [ ] Server starts without errors
- [ ] Health endpoint returns 200
- [ ] API docs load at /docs
- [ ] Can create a user via API
- [ ] Database tables exist

---

**Need Help?** Check `FINAL_COMPLETION.md` for detailed instructions.

**Ready to Deploy?** See deployment section in `README.md`.

