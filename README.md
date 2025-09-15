# Prototyp - Entscheidungsunterstützungssystem

Dieses System ist eine Protoyp eines Entscheidungsunterstützungssystem zur Identifikation von Kompetenzenlücken im Data Science Bereicht.


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
git clone https://github.com/nika171/DSS.git
cd DSS
```
Falls sie kein Git haben, kann der Code auch direkt als ZIP von GitHub heruntergeladen und entpacken werden.

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
**Windows:**
```bash@
python main.py
```
**macOS/Linux:**
```bash
python3 main.py
```
Anwendung im Browser öffnen:  
[http://localhost:5000](http://localhost:5000)

### 4. Tesnutzer

#### Admin
E-Mail: admin@test.de
Passwort: admin

#### Nutzer ohne Adminrechte
E-Mail: erika@test.de
Passwort: erika

E-Mail: max@test.de
Passwort: max

E-Mail: tom@test.de
Passwort: tom
