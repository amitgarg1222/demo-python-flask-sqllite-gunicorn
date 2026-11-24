# Flask + SQLite In-Memory Web App

A lightweight Python Flask task manager backed by a shared-cache SQLite in-memory database (`file:ec2_task_db?mode=memory&cache=shared`).

## Quick Local Run
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000 in your browser.

## Production Run (Single Gunicorn Worker for Shared In-Memory State)
```bash
gunicorn --workers 1 --threads 4 --bind 127.0.0.1:8000 app:app
```
