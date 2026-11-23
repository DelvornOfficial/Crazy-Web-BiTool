# 🛡️ Next Level Cheat — High-Security FastAPI & PostgreSQL Backend

Modern, high-performance, and hardened backend engine for **Next Level Cheat**. Built with **FastAPI**, **SQLAlchemy 2.0 (Async)**, and **PostgreSQL 16**, featuring comprehensive Anti-SQL Injection validation, Anti-Brute Force rate limiting, and an integrated Admin Management Portal.

---

## 🌟 Security Architecture Highlights

1. **100% Anti-SQL Injection Guarantee**:
   - Zero raw SQL strings or string formatting anywhere in the codebase.
   - All inputs strictly validated with Pydantic v2 regex constraint schemas (`^[a-zA-Z0-9_\-\.]{3,32}$`).
   - All queries bound and parameterized via SQLAlchemy 2.0 asynchronous ORM (`select(Model).where(Model.field == param)`).
2. **Anti-Brute Force & Credential Shield**:
   - Sliding-window IP rate limiting (10 attempts per minute max).
   - Dynamic account lockout (5 failed attempts locks target account for 15 minutes).
   - Constant-time password verification using salted `bcrypt` / `scrypt` to defeat side-channel timing attacks.
3. **Comprehensive Audit Logging**:
   - Every login attempt, failed verification, IP lockout, and release change is permanently logged with IP address, user-agent, timestamp, and status.
4. **Resilient Local & Cloud Database Layer**:
   - Runs on PostgreSQL 16 in production.
   - Automatically falls back to SQLite (`./data/local.db`) for immediate zero-dependency local testing if PostgreSQL is temporarily offline.

---

## 📁 Directory Structure

```
backend/
├── app/
│   ├── api/
│   │   ├── deps.py               # Dependency injection (Auth, real client IP extraction)
│   │   └── v1/
│   │       ├── admin.py          # Dashboard analytics & audit logs endpoints
│   │       ├── auth.py           # High-security login, JWT session, password changes
│   │       ├── downloads.py      # Telemetry & tracked APK download redirect
│   │       └── releases.py       # Public version API & admin CRUD
│   ├── core/
│   │   ├── config.py             # Pydantic BaseSettings environment manager
│   │   ├── database.py           # SQLAlchemy async engine & session maker
│   │   ├── rate_limiter.py       # In-memory token bucket & brute-force tracker
│   │   └── security.py           # Constant-time hashing & JWT engine
│   ├── models/                   # SQLAlchemy 2.0 Async ORM Models
│   │   ├── admin.py
│   │   ├── app_release.py
│   │   ├── audit_log.py
│   │   └── download_log.py
│   ├── schemas/                  # Pydantic v2 strict request/response validation
│   │   ├── analytics.py
│   │   ├── auth.py
│   │   └── release.py
│   ├── static/admin/             # High-Security Admin Portal UI (HTML5/CSS3/ES6)
│   │   ├── index.html
│   │   ├── admin.css
│   │   ├── admin.js
│   │   └── logo.png
│   └── main.py                   # FastAPI application initialization & lifespan
├── .env                          # Local environment variables
├── .env.example                  # Template configuration for production
├── Dockerfile                    # Production container build
├── docker-compose.yml            # Multi-container orchestration (FastAPI + PostgreSQL)
├── requirements.txt              # Production Python dependencies
└── README.md                     # Documentation
```

---

## 🚀 Quick Start — Local Development

### Option 1: Direct Python Run (Fastest)

1. **Navigate to the backend directory**:
   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment**:
   ```bash
   # Windows (PowerShell)
   python -m venv venv
   .\venv\Scripts\Activate.ps1

   # Linux / macOS
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Start the development server**:
   ```bash
   uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
   ```

5. **Access the application**:
   - 💻 **Admin Console**: [http://localhost:8000/admin](http://localhost:8000/admin)
   - 📚 **Swagger Interactive API Docs**: [http://localhost:8000/api/docs](http://localhost:8000/api/docs)
   - 🩺 **Health Check**: [http://localhost:8000/api/health](http://localhost:8000/api/health)

> **Default Superadmin Credentials:**
> - **Username**: `admin`
> - **Password**: `NextLevelAdmin@2026!`

---

### Option 2: Local Multi-Container Run with Docker

Run both PostgreSQL 16 and FastAPI in isolated containers:

```bash
docker compose up -d --build
```

View real-time logs:
```bash
docker compose logs -f
```

Stop containers:
```bash
docker compose down
```

---

## 🌐 Production VPS Deployment Guide

Deploying onto an Ubuntu 22.04 / 24.04 LTS Cloud VPS (DigitalOcean, Hetzner, AWS, Linode, Hostinger).

### Step 1: VPS Server Preparation
SSH into your VPS as `root` or a sudo user:
```bash
ssh root@YOUR_VPS_IP

# Update package lists
sudo apt update && sudo apt upgrade -y

# Install Docker & Docker Compose Plugin
sudo apt install -y curl ufw git
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER
```

### Step 2: Configure Firewall (UFW)
```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### Step 3: Clone Project & Configure Production Environment
```bash
mkdir -p /var/www/nextlevelcheat
cd /var/www/nextlevelcheat
# Clone or copy your backend directory here

cd backend
cp .env.example .env
nano .env
```

Make sure to adjust the following in `.env`:
- `ENVIRONMENT="production"`
- `DEBUG=False`
- `SECRET_KEY="<generate-a-strong-64-character-random-hex-string>"`
- `FIRST_SUPERADMIN_PASSWORD="<choose-a-strong-custom-password>"`
- `ALLOWED_ORIGINS="https://yourdomain.com,https://api.yourdomain.com"`

Generate a secure secret key:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### Step 4: Launch Containers with Docker Compose
```bash
docker compose -f docker-compose.yml up -d --build
```

Check container status:
```bash
docker compose ps
```

---

### Step 5: Setup Nginx Reverse Proxy with Free SSL (Let's Encrypt)

1. **Install Nginx & Certbot**:
   ```bash
   sudo apt install -y nginx python3-certbot-nginx
   ```

2. **Create Nginx site configuration**:
   ```bash
   sudo nano /etc/nginx/sites-available/api.yourdomain.com
   ```

   Paste the following configuration:
   ```nginx
   server {
       server_name api.yourdomain.com;

       # Max upload file size for releases
       client_max_body_size 100M;

       location / {
           proxy_pass http://127.0.0.1:8000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;

           # Security buffer timeouts
           proxy_connect_timeout 60s;
           proxy_read_timeout 60s;
       }
   }
   ```

3. **Enable configuration and obtain SSL certificate**:
   ```bash
   sudo ln -s /etc/nginx/sites-available/api.yourdomain.com /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl restart nginx

   # Obtain SSL certificate
   sudo certbot --nginx -d api.yourdomain.com
   ```

4. **Your Backend is Live with HTTPS**:
   - Admin Panel: `https://api.yourdomain.com/admin`
   - API Docs: `https://api.yourdomain.com/api/docs`

---

## 🔒 Security & Anti-SQL Injection Verification

To verify that the API is fully immune to SQL injections:
- All queries utilize SQLAlchemy async statements with parameterized values (`where(Model.username == payload.username)`).
- If an attacker submits `' OR '1'='1` or `; DROP TABLE admins;`, Pydantic's regex validation rejects the payload with `422 Unprocessable Entity` before it reaches any database engine.
- Even if a payload bypasses schema regex, SQLAlchemy executes parameterized SQL queries where malicious characters are treated strictly as string literals, preventing any SQL syntax execution.
