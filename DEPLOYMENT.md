# LOCALServe Public Deployment Guide

This document describes how LOCALServe is deployed for public access.

---

## ⚡ Option 1: Instant Public Access via Live Tunnel (Active Right Now!)

A secure public HTTPS tunnel is currently running from your local server:

- **Public URL**: [https://shaggy-windows-wink.loca.lt](https://shaggy-windows-wink.loca.lt)
- **Tunnel Password / IP (if prompted by Localtunnel)**: `218.248.4.14`

> Anyone on any mobile phone, tablet, or external computer can open this URL right now to test the site, perform voice searches, inspect pharmacies, and request medicines!

---

## ☁️ Option 2: 24/7 Permanent Cloud Hosting on Render (Free)

For a permanent public deployment that stays online 24/7 (even when your laptop is turned off), follow these 3 simple steps:

### Step 1: Push Project to GitHub
1. Create a free account at [GitHub.com](https://github.com).
2. Create a new repository named `localserve`.
3. In your project directory, run:
```bash
git init
git add .
git commit -m "Initial commit of LOCALServe platform"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/localserve.git
git push -u origin main
```

### Step 2: Deploy on Render.com (100% Free)
1. Go to [Render.com](https://render.com) and sign in with your GitHub account.
2. Click **New +** → **Web Service**.
3. Select your `localserve` GitHub repository.
4. Fill in the following details (pre-configured in the repository):
   - **Name**: `localserve`
   - **Environment**: `Python 3`
   - **Region**: `Singapore` or `Oregon`
   - **Build Command**: `pip install -r requirements.txt && python seed_data.py`
   - **Start Command**: `gunicorn wsgi:app`
   - **Plan**: `Free`
5. Click **Create Web Service**.

Within 2 to 3 minutes, Render will build the environment and assign you a permanent public URL:
👉 **`https://localserve.onrender.com`**

---

## 🐍 Option 3: Deploy on PythonAnywhere (Free Academic Host)

PythonAnywhere is especially well-suited for college BTech projects using SQLite:

1. Register a free account at [PythonAnywhere.com](https://www.pythonanywhere.com).
2. Go to the **Consoles** tab and open a **Bash** console.
3. Clone your repository:
   ```bash
   git clone https://github.com/YOUR_USERNAME/localserve.git
   cd localserve
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   python seed_data.py
   ```
4. Go to the **Web** tab:
   - Click **Add a new web app**.
   - Select **Manual configuration** → **Python 3.10**.
   - Set **Virtualenv path**: `/home/YOUR_USERNAME/localserve/.venv`
   - Click the link to edit the **WSGI configuration file** and update it to:
     ```python
     import sys
     path = '/home/YOUR_USERNAME/localserve'
     if path not in sys.path:
         sys.path.append(path)

     from app import create_app
     application = create_app()
     ```
5. Click the green **Reload** button.
Your app will be live at:
👉 **`https://YOUR_USERNAME.pythonanywhere.com`**

---

## 🔒 Production Architecture & Files Included

The project already contains all required production deployment configurations:
- `wsgi.py`: Universal WSGI production entry point for Python servers.
- `Procfile`: Process declaration for containerized and PaaS runners (`web: gunicorn wsgi:app`).
- `render.yaml`: Blueprint configuration for Render 1-click deployments.
- `requirements.txt`: Frozen production dependencies including `gunicorn`.
- `.gitignore`: Prevents temporary logs, virtual environments, and caches from being uploaded.
