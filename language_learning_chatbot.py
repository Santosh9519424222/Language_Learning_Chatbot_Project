
# Language-Learning Chatbot Project

from langchain.chat_models import ChatOpenAI
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
import sqlite3
import os
from datetime import datetime
from collections import Counter
import openai
import csv
import spacy

nlp = spacy.load('en_core_web_sm')

try:
    openai_api_key = "your_openai_api_key"
    if not openai_api_key:
        raise ValueError('OpenAI API key not found. Please set it as an environment variable.')
except Exception as e:
    print(f"Error: {e}")
    exit(1)

llm = ChatOpenAI(temperature=0, openai_api_key=openai_api_key)
memory = ConversationBufferMemory()
conversation = ConversationChain(llm=llm, memory=memory)

conn = sqlite3.connect('user_mistakes.db')
cursor = conn.cursor()
cursor.execute("""CREATE TABLE IF NOT EXISTS mistakes (
                  id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user TEXT,
                  mistake TEXT,
                  timestamp DATETIME,
                  feedback TEXT
                  )""")
conn.commit()

def get_user_details():
    print("Welcome to the Language-Learning Chatbot!")
    user_name = input("Enter your name: ")
    supported_languages = ['English', 'French', 'Spanish', 'German', 'Italian', 'Chinese', 'Japanese', 'Korean', 'Hindi', 'Portuguese', 'Arabic']

    while True:
        learning_language = input("What language do you want to learn? ")
        if learning_language.capitalize() not in supported_languages:
            print("Invalid language. Please choose a valid language from the supported list:")
            print(", ".join(supported_languages))
        else:
            break

    while True:
        known_language = input("What language do you already know? ")
        if known_language.capitalize() not in supported_languages:
            print("Invalid language. Please choose a valid language from the supported list:")
            print(", ".join(supported_languages))
        else:
            break

    proficiency_level = input("What is your current proficiency level (Beginner, Intermediate, Advanced)? ")
    return user_name, learning_language.capitalize(), known_language.capitalize(), proficiency_level

user_name, learning_language, known_language, proficiency_level = get_user_details()

def analyze_mistakes(user_input):
    doc = nlp(user_input)
    mistakes = [token.text for token in doc if token.pos_ in ['VERB', 'NOUN', 'ADJ'] and token.is_oov]
    return mistakes

def interact_with_user():
    print(f"Great! Let's start a conversation in {learning_language}.")
    print("Type 'exit' to end the conversation.")
    while True:
        user_input = input(f"You ({learning_language}): ")
        if user_input.lower() == 'exit':
            break

        response = conversation.predict(input=user_input)
        print(f"Chatbot: {response}")

        mistakes = analyze_mistakes(user_input)
        if mistakes:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            feedback = "Consider revising these words: " + ', '.join(mistakes)
            cursor.execute("INSERT INTO mistakes (user, mistake, timestamp, feedback) VALUES (?, ?, ?, ?)", (user_name, user_input, timestamp, feedback))
            conn.commit()
    print("Conversation ended.")

def generate_feedback():
    cursor.execute("SELECT mistake, timestamp, feedback FROM mistakes WHERE user = ?", (user_name,))
    mistakes = cursor.fetchall()
    with open('mistakes_report.csv', 'w', newline='') as csvfile:
        fieldnames = ['Mistake', 'Timestamp', 'Feedback']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in mistakes:
            writer.writerow({'Mistake': row[0], 'Timestamp': row[1], 'Feedback': row[2]})
    print("Report exported to mistakes_report.csv")
    conn.close()

interact_with_user()
generate_feedback()
