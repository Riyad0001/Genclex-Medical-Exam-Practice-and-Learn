# Genclex (StemRN) — Medical Exam Practice & Learning Platform

Genclex is an AI-powered learning and test-prep platform designed for nursing students and healthcare professionals preparing for the **NCLEX** and clinical certifications. It combines realistic exam simulations with real-time AI tutoring, pharmacology tools, and smart study aids.

---

## ✨ Features

- **🩺 NCLEX Exam Practice Engine**: Adaptive practice tests, customizable question banks, full mock exams, and in-depth clinical rationales.
- **🎙️ Real-time AI Medical Tutor**: Voice-to-voice and text tutoring powered by OpenAI Realtime WebRTC and streaming chat.
- **📝 Notes to Quiz & Flashcards**: Transform lecture notes into active-recall flashcard decks and practice quizzes with spaced repetition tracking.
- **💊 Pharmacology Drug Cards & Care Plans**: Interactive drug reference cards, side-effect profiles, and structured nursing care plan builders.
- **📊 ECG Mastery & Concept Visualizer**: Visual ECG rhythm interpretation practice and disease concept mapping.
- **🔐 Auth & User Management**: Secure JWT auth, Google OAuth login, email verification, and password resets.
- **💳 Subscription & Billing**: Complete Stripe integration with tiered subscriptions, invoice management, and webhooks.

---

## 🛠️ Tech Stack

- **Backend**: Python 3.11+, Django 6.0, Django REST Framework (DRF)
- **Real-Time / Async**: Django Channels, Daphne, WebSockets
- **Database**: PostgreSQL (Production) / SQLite (Local Dev)
- **Cloud & Storage**: AWS S3 (Media & Static files)
- **AI Services**: OpenAI (GPT-4o, Realtime API), Anthropic Claude
- **Payments**: Stripe API & Webhooks
- **Admin Panel**: Django Unfold with custom dashboards & CKEditor 5

---

## 🚀 Getting Started

### 1. Clone the repository
```bash
git clone https://github.com/Riyad0001/Genclex-Medical-Exam-Practice-and-Learn.git
cd Genclex-Medical-Exam-Practice-and-Learn
```

### 2. Set up virtual environment
```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
Copy the example environment file and add your credentials:
```bash
cp .env.example .env
```

### 5. Run migrations & start server
```bash
python manage.py migrate
python manage.py runserver
```
The API server will run at `http://127.0.0.1:8000/`.

---

## 🐳 Docker Setup

Run the entire application stack (Web + Nginx) with Docker Compose:

```bash
docker compose up -d --build
```

---

## 📄 License
Private repository. All rights reserved.
