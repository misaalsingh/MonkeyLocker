# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MonkeyLocker is a face recognition and classroom management system. Users can enroll faces, authenticate via facial recognition or password/Google OAuth2, and manage virtual rooms/classrooms with image sharing and event logging. Ideally this would be used to store shared memories and create virtual "boards". For exmaple, a room can be made for Spring Break 2026 in Madrid for everyone who went on the trip. Kinda like a google photos meets Pinterest. Initially, I think I will have a login and face enrollment with the facial recoginition being the "password" to get into shared rooms. Ideally though I want gesture recognition to be the password to get into the room. Hence the use of mediapipe and tensorflow for my CV workflows.

## Repository Structure

```
MonkeyLocker/
├── MonkeyLockerUI/           # React + TypeScript + Vite frontend
├── Monkey_Locker_Service/    # Honestly I built the backend out too robustly and I got confused when making my front end. This is a hotch potch mix of my schema and the basic backend logic. Use this as reference but this isn't the real backend that will be used
├── Monkey_Locker_Cervesa/    # The real backend. Originally it was a copy of the Monkey Locker Service folder. This currently has basic auth and event logging.
├── Docker/                   # Docker configuration
└── terraform/                # Terraform configuration
```

## Commands

### Frontend (MonkeyLockerUI/)
```bash
npm run dev       # Start dev server with HMR
npm run build     # TypeScript compile + Vite bundle
npm run lint      # Run ESLint
npm run preview   # Preview production build
```

### Backend (Monkey_Locker_Service/ or Monkey_Locker_Cervesa/)
```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python main.py           # Start FastAPI server on :8000 with auto-reload
pytest                   # Run tests
pytest --cov             # Run tests with coverage
```

## Backend Architecture

Both backend services follow the same layered pattern:

- **`models/`** — SQLModel ORM models (SQLite dev / PostgreSQL prod). Tables auto-created on startup.
- **`schemas/`** — Pydantic request/response validation schemas.
- **`routers/`** — FastAPI route handlers (thin layer, delegates to services).
- **`services/`** — Business logic (facial recognition, auth, event logging, S3/local storage).
- **`dependencies/`** — FastAPI `Depends()` providers for auth guards, DB sessions, pagination, validation.

### Key Services
- **`facial_recognition.py`**: Enrollment (extract + store embedding) and authentication (cosine distance matching) using DeepFace (Facenet512), dlib, and MediaPipe. Embeddings stored as binary blobs. Threshold configurable via `.env` (default 0.5).
- **`auth_service.py`**: JWT token issuance/refresh, bcrypt password hashing, Google OAuth2 flow.
- **`event_logger.py`**: Structured audit trail for all auth, user, room, image, and security events.
- **`storage.py`**: Abstraction over local filesystem and AWS S3.
- **`db_connection.py`**: SQLAlchemy session management; SQL echo enabled (all queries logged).

### Monkey_Locker_Service vs. Monkey_Locker_Cervesa
- **Monkey_Locker_Service** is the primary service with full routers: auth, users, rooms, images, events.
- **Monkey_Locker_Cervesa** is a secondary/specialized service focused on facial recognition and OAuth2; has separate `Facial_Recognition/` and `OAuth2/` modules. Routers cover auth, users, events.

## Configuration

Both backends rely on a `.env` file (excluded from git). Key variables:
- `DATABASE_URL` — SQLite URI for dev, PostgreSQL for prod
- `JWT_SECRET` — Secret for signing tokens
- `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` — Google OAuth2 credentials
- `AWS_*` — S3 bucket and credentials (when using cloud storage)
- `FACE_RECOGNITION_THRESHOLD` — Cosine distance threshold (default `0.5`)

## Data Model Highlights

- **User**: stores face embedding as a binary blob, supports Google OAuth fields, soft-delete, and account deactivation with reason.
- **Room**: creator-based permissions, privacy settings, role-based membership (admin/moderator/member), archive support.
- **Event**: comprehensive audit log with categories AUTH, USER, ROOM, IMAGE, SECURITY.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 19, TypeScript, Vite 7 |
| Backend | FastAPI 0.109, Python 3.13, Uvicorn |
| ORM | SQLModel + SQLAlchemy 2.0, Alembic |
| Face Recognition | DeepFace 0.0.93, dlib, OpenCV, TensorFlow 2.20, MediaPipe |
| Auth | python-jose (JWT), passlib[bcrypt], Google OAuth2 |
| Storage | Local filesystem or AWS S3 (boto3) |
| Testing | pytest, pytest-asyncio, pytest-cov |

## Future Steps


MVP Version
- Get the google auth and basic sign on set up
- Work on the facial enrollment
- Get the room setup figured out and the abilitiy to add pictues and share with others
- AWS S3 storage set up for images uploaded

Beta Version
- Hand and gesture recognition for getting into rooms
- Image analysis to see who's in which picture to make filtering easier
- Encryption on images to make storage more secure
- Basic CI/CD and test + prod environment set ups