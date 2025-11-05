python -m venv venv || pause && exit
venv\Scripts\pip install -r requirements.txt || pause && exit
venv\Scripts\pip install pyinstaller || pause && exit

venv\Scripts\pyinstaller --onefile main.py || pause
