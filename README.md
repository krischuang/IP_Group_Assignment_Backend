# UTSFE — Backend API

UTSFE (UTS Frontend Engineering) is a content-publishing platform where users can read articles, manage their profile, and reset their password. Administrators can publish, edit, and delete articles and manage all user accounts. This repository contains the **FastAPI backend** that powers the platform.

**Problem it solves:** Provides a secure, role-based REST API for article management and user authentication, including JWT-based sessions, RSA-encrypted password transport, email OTP password reset, Cloudflare Turnstile bot protection, and AI-generated article summaries via OpenRouter.

---

## Technical Stack

| Layer | Technology |
|---|---|
| Web framework | [FastAPI](https://fastapi.tiangolo.com/) |
| ASGI server | [Uvicorn](https://www.uvicorn.org/) |
| Database | [MongoDB](https://www.mongodb.com/) |
| ODM | [Beanie](https://beanie-odm.dev/) (async MongoDB ODM built on Motor) |
| Authentication | JWT (`python-jose`) + bcrypt (`passlib`) |
| Password transport | RSA-PKCS1v15 encryption (`cryptography`) |
| Bot protection | Cloudflare Turnstile (`httpx`) |
| Email | `aiosmtplib` (async SMTP, Gmail App Password) |
| AI summaries | OpenAI-compatible SDK → [OpenRouter](https://openrouter.ai/) free models |
| Settings | `pydantic-settings` (`.env` file) |

**Python version:** 3.12+

---

## Getting Started

### 1. Clone & create a virtual environment

```bash
git clone <repo-url>
cd IP_Group_Assignment_Backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Generate the RSA key pair

The server needs an RSA key pair so the client can encrypt passwords before sending them. Run the following once; the generated files are `.gitignore`d:

```bash
python -c "
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

key = rsa.generate_private_key(public_exponent=65537, key_size=2048)

with open('private_key.pem', 'wb') as f:
    f.write(key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.TraditionalOpenSSL,
        serialization.NoEncryption()
    ))
with open('public_key.pem', 'wb') as f:
    f.write(key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo
    ))
print('Keys generated.')
"
```

### 4. Configure environment variables

Copy `.env.example` to `.env` and fill in all values:

```bash
cp .env.example .env
```

| Variable | Description | Example |
|---|---|---|
| `MONGODB_URI` | MongoDB connection string | `mongodb://localhost:27017` |
| `DB_NAME` | Database name | `ip_group` |
| `JWT_SECRET` | Secret used to sign JWTs — use a long random string | `openssl rand -hex 32` |
| `JWT_EXPIRE_MINUTES` | JWT lifetime in minutes | `60` |
| `ROOT_PATH` | FastAPI `root_path` (set when served behind a reverse proxy sub-path) | `` |
| `TURNSTILE_SECRET_KEY` | Cloudflare Turnstile **secret** key (from the Turnstile dashboard) | `0x4AAAA...` |
| `SMTP_HOST` | SMTP server hostname | `smtp.gmail.com` |
| `SMTP_PORT` | SMTP port (587 for STARTTLS) | `587` |
| `SMTP_USERNAME` | SMTP login email address | `you@gmail.com` |
| `SMTP_PASSWORD` | SMTP App Password (Gmail: [create one here](https://myaccount.google.com/apppasswords)) | `abcd efgh ijkl mnop` |
| `SMTP_FROM` | Sender address shown in emails | `you@gmail.com` |
| `RESET_TOKEN_EXPIRE_MINUTES` | OTP expiry window | `15` |
| `OPENROUTER_API_KEY` | OpenRouter API key for AI summaries | `sk-or-v1-...` |

### 5. Run the development server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The interactive API docs are available at `http://localhost:8000/docs`.

---

## API Overview

| Prefix | Description |
|---|---|
| `POST /auth/register` | Create a new user account |
| `POST /auth/login` | Authenticate and receive a JWT |
| `GET /auth/me` | Get the authenticated user's profile |
| `POST /auth/me` | Update profile (full name, bio, avatar URL) |
| `GET /auth/public-key` | Fetch the server's RSA public key for password encryption |
| `POST /auth/forgot-password` | Send a 6-digit OTP to the user's email |
| `POST /auth/validate-reset-token` | Verify the OTP and mark it as verified |
| `POST /auth/reset-password` | Set a new password (requires a verified token) |
| `GET /articles/` | List all articles (public) |
| `GET /articles/{id}` | Get a single article (public) |
| `POST /articles/` | Create an article (authenticated) |
| `PUT /articles/{id}` | Update an article (owner only) |
| `DELETE /articles/{id}` | Delete an article (owner only) |
| `GET /admin/stats` | Total user count (admin only) |
| `GET /admin/users` | List all users with optional search (admin only) |
| `PUT /admin/users/{id}` | Update user role / details (admin only) |
| `DELETE /admin/users/{id}` | Delete a user (admin only) |
| `POST /ai-tools/summary/jobs` | Start an async AI summary job |
| `GET /ai-tools/summary/jobs/{job_id}` | Poll job status and retrieve result |

---

## Folder Structure

```
IP_Group_Assignment_Backend/
│
├── app/                        # Main application package
│   ├── main.py                 # FastAPI app factory, lifespan hooks, router registration
│   ├── config.py               # Pydantic-settings: loads all env variables
│   ├── database.py             # MongoDB connection helpers (connect / close)
│   ├── dependencies.py         # FastAPI dependency injection: get_current_user, require_admin
│   ├── keys.py                 # Loads RSA private/public key pair from PEM files
│   │
│   ├── models/                 # Beanie document models (MongoDB collections)
│   │   ├── user.py             # User document — stores credentials, role, profile
│   │   ├── article.py          # Article document — title, content, AI summary fields
│   │   ├── counter.py          # Auto-increment counter for user_id / article_id
│   │   └── password_reset.py   # Password reset OTP token — email, token, expiry, used/verified flags
│   │
│   ├── routers/                # Route handlers (one module per feature area)
│   │   ├── auth.py             # Registration, login, /me, forgot/reset password endpoints
│   │   ├── admin.py            # Admin-only user management CRUD
│   │   ├── article.py          # Article CRUD endpoints + AI job trigger on create
│   │   └── ai_tools.py         # Async AI summary job: create job, run in background, poll status
│   │
│   └── utils/                  # Stateless helper utilities
│       ├── rsa_crypto.py       # Decrypts a base64-encoded RSA-encrypted password from the client
│       ├── email.py            # Sends the HTML OTP reset email via aiosmtplib
│       └── turnstile.py        # Verifies a Cloudflare Turnstile challenge token
│
├── requirements.txt            # All Python dependencies with minimum version pins
├── .env.example                # Template for required environment variables (safe to commit)
├── .env                        # Actual secrets — never committed (listed in .gitignore)
└── README.md                   # This file
```

---

## Database Collections

| Collection | Model | Purpose |
|---|---|---|
| `users` | `User` | Registered user accounts with hashed passwords |
| `articles` | `Article` | Published articles with AI summary fields |
| `counters` | `Counter` | Auto-increment sequences for `user_id` and `article_id` |
| `password_reset_tokens` | `PasswordResetToken` | Short-lived OTP tokens for the forgot-password flow |

A MongoDB export (`ip_group.json` or `.bson`) is included in the `db_export/` folder in the root repository.

---

## Deployment

The backend is containerised and deployed automatically via GitHub Actions on every push to `main`. The workflow file is at `.github/workflows/deploy.yml`.

For manual deployment:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
```
