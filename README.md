# 🧠 Smart Attendance System

A smart, secure, and deep learning-powered **Attendance System** built with **Django**. It uses **MTCNN** for real-time face detection, **VGGFace2** for face recognition, and an **anti-spoofing model** to distinguish real faces from fake ones (e.g. photos or videos).

## 📸 Features

- 🔍 Face Detection using **MTCNN**
- 🧬 Face Recognition via **VGGFace2 Embeddings**
- 🛡️ **Anti-Spoofing** to block fake or replay attempts
- 🗂️ Admin Panel to manage students and attendance
- 🧑‍🎓 Student onboarding with face image registration
- 📊 Attendance reporting (by student, date, or session)
- 🎥 Live webcam integration for real-time processing

---

## 🧱 Tech Stack

| Layer     | Tools Used                                |
|-----------|--------------------------------------------|
| Backend   | Python, Django, SQLite                     |
| ML Models | MTCNN (face detection), VGGFace2 (recognition) |
| Security  | Anti-spoofing using CNN-based classifier   |
| Frontend  | HTML, CSS, Bootstrap                       |
| Deployment| Docker, Gunicorn |

---

## 🚀 Getting Started

### 1. Clone the Repo

```bash
git clone https://github.com/divyeshlathiya/Smart-Attendance-System.git
cd Smart-Attendance-System
```

### 2. Setup Virtual Environment & Install Requirements

```bash
python -m venv venv
source venv/bin/activate     # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Migrate Database

```bash
python manage.py makemigrations
python manage.py migrate
```

### 4. Create Superuser (Admin)

```bash
python manage.py createsuperuser
```

### 5. Run the Server

```bash
python manage.py runserver
```

Visit: `http://127.0.0.1:8000/`

---

## 🔐 Setup the `.env` File

Create a `.env` file in the root directory of your project to securely store sensitive environment variables.

### ✅ Example `.env` file

```env
# Supabase Credentials
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-key

# Django Settings
SECRET_KEY=your-django-secret-key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
```

## 🔐 Anti-Spoofing Module

The system includes a CNN-based anti-spoofing layer that checks if the detected face is real or a spoof (photo/video). If spoofed, attendance is not marked and an alert is logged.

---

## 🧠 Face Recognition Pipeline

1. **Detection** - Real-time face detection using MTCNN.
2. **Embedding** - Embeddings generated via VGGFace2.
3. **Comparison** - Match embeddings with the registered database using cosine similarity.
4. **Spoof Check** - Confirm liveness via anti-spoofing model.

---

## 📂 Project Structure

```
Face-Recognition-System/
├── Attendence_System/       # Django project config
├── attendence_sys/          # Core app logic
├── resources/               # ML models (anti-spoofing, embeddings)
├── src/                     # Recognition + webcam pipeline
├── static/                  # CSS, JS
├── templates/               # Frontend templates
├── Dockerfile               # Docker support
├── Procfile                 # For Heroku deployment
└── requirements.txt
```

---

## ✍️ Author & Team Member

**1. Divyesh Lathiya**
**2. Dev Mistri**
**3. Mohit Rupchandani**
