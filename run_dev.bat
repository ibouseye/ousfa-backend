@echo off
set FLASK_APP=app.py
set FLASK_DEBUG=1
echo Starting Flask server in debug mode...
python -m flask run