# Kompetenz- und Projektmanagementsystem

Dieses System ist eine Protoyp, mit der Unternehmen die Fähigkeiten ihrer Mitarbeiter und die Zuteilung zu Projekten verwalten können. Die Anwendung basiert auf Python und verwendet Flask als Framework. **Du brauchst Python und Node.js auf deinem Computer!**


## 🛠️ Voraussetzung

- **Python 3.7 oder höher**
- **pip**
- **Node.js und npm**
  
### 🐍 Python installieren

1. Gehe zu [python.org/downloads](https://www.python.org/downloads/)

### 🟩 Node.js installieren

Gehe zu [nodejs.org/download](https://nodejs.org/en/download/) und installiere die LTS-Version.

## ⚡ Installation & Setup

### 1. Repository klonen
```bash
git clone <repository-url>
cd DSS-main
```
Falls sie kein Git haben, kannstder Code auch direkt als ZIP von GitHub heruntergeladen und entpacken werden.

### 2. Virtuelle Umgebung erstellen (optional)

**Windows:**
```bash@
python -m venv env
env\Scripts\activate
```
**macOS/Linux:**
```bash
python3 -m venv env
source env/bin/activate
```

### 3. Abhängigkeiten installieren

**Python-Abhängigkeiten:**
```bash
pip install -r requirements.txt
```

**Frontend-Abhängigkeiten (für das Styling):**
```bash
npm install
npx tailwindcss -i ./src/input.css -o ./static/output.css
```

### 4. Anwendung starten
```bash
python main.py
```
Anwendung im Browser öffnen:  
[http://localhost:5000](http://localhost:5000)

### 4. Tesnutzer

## Admin
E-Mail: admin@test.de
Passwort: admin

## Nutzer ohne Adminrechte
E-Mail: erika@test.de
Passwort: erika

E-Mail: max@test.de
Passwort: max

E-Mail: tom@test.de
Passwort: tom
