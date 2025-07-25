{\rtf1\ansi\ansicpg1252\deff0\nouicompat\deflang1033{\fonttbl{\f0\fnil\fcharset0 Times New Roman;}}
{\*\generator Riched20 10.0.19041}\viewkind4\uc1 
\pard\sa200\sl240\slmult1\qj\f0\fs28\lang9 # Language-Learning Chatbot Project\par
\par
## Overview\par
\par
This is a language-learning chatbot built using OpenAI's GPT models with LangChain. It helps users practice and improve their language skills by engaging in conversation and providing feedback on mistakes made during the interaction.\par
\par
## Features\par
\par
- Supports multiple languages.\par
- Provides instant feedback on mistakes.\par
- Stores user mistakes in a SQLite database.\par
- Generates a CSV report with detailed feedback.\par
\par
## Requirements\par
\par
- Python 3.8+\par
- OpenAI (`pip install openai`)\par
- LangChain (`pip install langchain`)\par
- SpaCy (`pip install spacy`)\par
- SQLite (Built-in with Python)\par
\par
## Setup\par
\par
1. Install dependencies:\par
\par
   pip install openai langchain spacy\par
   python -m spacy download en_core_web_sm\par
   \par
\par
2. Set your OpenAI API key directly in the code:\par
   openai_api_key = "your_openai_api_key"\par
\par
## Running the Chatbot\par
\par
Run the chatbot using the following command:\par
\par
\par
python language_learning_chatbot.py\par
\par
\par
## Output\par
\par
- Feedback is stored in an SQLite database (`user_mistakes.db`).\par
- A report is generated as a CSV file (`mistakes_report.csv`) after each session.\par
\par
## Note\par
\par
Ensure you have an internet connection to access the OpenAI API.\par
\par
## Author\par
\par
Your Name\par
\par
Santosh Kumar\\\par
9519424222\\\par
santosh.9519422gmail.com\par
}
 