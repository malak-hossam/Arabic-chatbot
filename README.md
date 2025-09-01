# Arabic Chatbot (Gemini + LangChain)

## Project Description
This project is an **Arabic educational chatbot** built with **FastAPI**, **Google Gemini API**, and **LangChain**.  
It interacts with students, answers questions, generates grammar exercises, evaluates answers, and integrates with microservices for **morphology** and **lexical analysis**.

---

## Table of Contents
- [Features](#features)
- [Project Structure](#project-structure)
- [Prerequisites](#prerequisites)
- [API Usage](#api-usage)
- [Docker](#docker)
- [Configuration Notes](#configuration-notes)
- [Requirements](#requirements)
- [Author](#author)
- [License](#license)

---

## Features
- **Conversational Memory** using LangChain’s `ConversationBufferMemory`.
- **Intent Detection** for meaning, antonym, plural, parsing, writing, exercise generation, and answer evaluation.
- **Educational Tools**: creates grammar exercises and evaluates student answers with constructive feedback.
- **Integrations**:
  - Morphology API: https://malak-hossam-morpology.hf.space
  - Word Meaning API: https://malak-hossam-word-meaning.hf.space

---

## Project Structure
- arabic-chatbot-gemini-langchain/
  - main.py
  - requirements.txt
  - Dockerfile
  - README.md

---

## Prerequisites
- Python 3.9+ (recommended)
- A valid **Google Gemini API key** (set as an environment variable)
- Git (for cloning the repo)

---

## API Usage
- **Endpoint**
  
      POST /chat

- **Request Body (JSON)**
  
      {
        "user_id": "student123",
        "message": "أعرب الجملة: النجاح هدفُ الطموحين"
      }

- **Response (JSON)**
  
      {
        "response": "النجاح: مبتدأ مرفوع بالضمة. هدفُ: خبر مرفوع وهو مضاف. الطموحين: مضاف إليه مجرور بالياء."
      }

**Notes**
- If the message intent is morphology or lexical lookup, the service forwards to the linked microservices and returns formatted results.
- The bot preserves short chat history per `user_id` to improve coherence.

---

## Docker
1. **Build the image**
   
       docker build -t arabic-chatbot .

2. **Run the container**
   
       docker run -p 8000:8000 -e GOOGLE_API_KEY="YOUR_KEY_HERE" arabic-chatbot

3. **Open the service**
   
       http://localhost:8000

---

## Configuration Notes
- **Environment Variable**: `GOOGLE_API_KEY` (preferred) for Gemini access.
- **Timeouts/Reliability**: External microservices may fail; the app returns friendly error messages when dependencies are unreachable.

---

## Requirements
- fastapi
- uvicorn
- requests
- google-generativeai
- langchain

(These are listed in `requirements.txt`.)

---

## Author
**Malak Hossam**  
AI Engineer | NLP & Deep Learning Enthusiast

---

## License
This project is provided for educational and research purposes.  
You may adapt or extend it for your own use. For commercial usage, please review third-party API licenses (Google Gemini, etc.).
