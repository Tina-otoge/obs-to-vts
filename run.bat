cd %~dp0

python -m venv venv || pause && exit
.\venv\Scripts\pip install -r requirements.txt || pause && exit
.\venv\Scripts\python main.py || pause
