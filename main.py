# Import aller benötigten Flask-Module und Erweiterungen
from collections import defaultdict  # Für verschachtelte Dictionaries
from flask import Flask, render_template, flash, request, redirect, url_for  # Basis Flask-Funktionalität
from flask_login import (UserMixin, LoginManager, login_user, login_required, 
                         logout_user, current_user)  # User-Session-Management
from flask_migrate import Migrate  # Datenbank-Migrationen
from flask_sqlalchemy import SQLAlchemy  # ORM für Datenbankoperationen
from flask_wtf import FlaskForm  # Formular-Handling mit CSRF-Schutz
from sqlalchemy.orm import joinedload  # Optimierte Datenbankabfragen mit Joins
from werkzeug.security import generate_password_hash, check_password_hash  # Passwort-Hashing für Sicherheit
from wtforms import StringField, SubmitField, PasswordField, BooleanField  # Formularfelder
from wtforms.validators import DataRequired  # Formularvalidierung

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'  # Datenbankpfad
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False 
app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'  # Für Flash-Messages und CSRF!

db = SQLAlchemy(app)  
migrate = Migrate(app, db)  

# Nutzer-Tabelle mit Login
class Users(db.Model, UserMixin):
  
    id = db.Column(db.Integer, primary_key=True)  
    name = db.Column(db.String(100), nullable=False)  
    email = db.Column(db.String(100), nullable=False, unique=True)  
    admin = db.Column(db.Boolean, default=False, nullable=False)   
    password_hash = db.Column(db.String(128))  # Gehashtes Passwort 
    should_update_competences = db.Column(db.Boolean, default=False, nullable=False) 
    
    # Beziehung zu Nutzer-Kompetenzen (1:n)
    competences = db.relationship('UsersCompetence', backref='user')

    @property 
    def password(self):
        raise AttributeError('Passwort ist nicht lesbar')
    
    @password.setter 
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
         
    def __repr__(self):
        return f'<User {self.name}>'
    
# Kompetenzgruppen-Tabelle     
class CompetenceGroup(db.Model):

    id = db.Column(db.Integer, primary_key=True) 
    name = db.Column(db.String(100), nullable=False, unique=True) 

    # 1:n Beziehung zu Kompetenzen 
    competences = db.relationship('Competence', backref='competence_group', lazy=True)

# Kompetenz-Tabelle  
class Competence(db.Model):

    id = db.Column(db.Integer, primary_key=True) 
    name = db.Column(db.String(100), nullable=False)  
    competence_group_id = db.Column(db.Integer, db.ForeignKey('competence_group.id'), nullable=False)  

    # 1:n Beziehung zu Kompetenzen 
    knowledge_skills = db.relationship('KnowledgeSkills', backref='competence', lazy=True)

# Wissen und Fähigkeiten-Tabelle  
class KnowledgeSkills(db.Model):

    id = db.Column(db.Integer, primary_key=True) 
    name = db.Column(db.String(100), nullable=False) 
    competence_id = db.Column(db.Integer, db.ForeignKey('competence.id'), nullable=False) 

    # 1:n Beziehung zu Benutzer-Kompetenzen 
    user_assignments = db.relationship('UsersCompetence', backref='knowledge_skill', lazy=True)

# Nutzerkompetenzen mit Level-Tabelle  
class UsersCompetence(db.Model):
    
    id = db.Column(db.Integer, primary_key=True)  
    users_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False) 
    knowledge_skill_id = db.Column(db.Integer, db.ForeignKey('knowledge_skills.id'), nullable=False)  
    competence_level = db.Column(db.String(100), nullable=False)  # Kompetenzniveau ( "Kenner", "Könner", "Experte")


# Many-to-Many Beziehung zwischen Projekten und Nutzern
projekt_user = db.Table('projekt_user',
    db.Column('project_id', db.Integer, db.ForeignKey('project.id'), primary_key=True),
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True)
)

# Projekt-Tabelle 
class Project(db.Model):
    
    id = db.Column(db.Integer, primary_key=True)  
    project_name = db.Column(db.String(100), nullable=False)  
    status = db.Column(db.String(100))  # Projektstatus ( "Aktiv", "Abgeschlossen")
    notiz = db.Column(db.Text)
    
  
    requirements = db.relationship('ProjectRequirement', backref='project', lazy=True)  # 1:n zu Anforderungen
    users = db.relationship('Users', secondary=projekt_user, backref='projects')  # Zugewiesene Nutzer

# Projektanforderungen-Tabelle 
class ProjectRequirement(db.Model):
    
    id = db.Column(db.Integer, primary_key=True)  
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'), nullable=False)  
    knowledge_skill_id = db.Column(db.Integer, db.ForeignKey('knowledge_skills.id'), nullable=False) 
    competence_level = db.Column(db.String(20))  

    knowledge_skill = db.relationship('KnowledgeSkills')

    
# === FORMULAR-DEFINITIONEN ===
# Formular zum Hinzufügen neuer Nutzer
class AddUserForm(FlaskForm):
    
    name = StringField("Name", validators=[DataRequired()], 
                      render_kw={"placeholder": "Name"})  
    email = StringField("E-Mailadresse", validators=[DataRequired()], 
                       render_kw={"placeholder": "E-Mailadresse"})  
    password_hash = PasswordField("Passwort", validators=[DataRequired()], 
                                 render_kw={"placeholder": "Passwort"}) 
    admin = BooleanField("Soll der Nutzer Admin-Rechte erhalten?")  
    submit = SubmitField("Erstellen")  

# Formular zum Login
class LoginForm(FlaskForm):
    
    email = StringField("E-Mailadresse", validators=[DataRequired()]) 
    password = PasswordField("Password", validators=[DataRequired()]) 
    submit = SubmitField("Anmelden") 

# Leeres Formular für CSRF-Schutz in Admin-Kompetenz-Bearbeitung
class AdminCompetenceForm(FlaskForm):
    pass  # Felder werden dynamisch im Template erstellt

# === FLASK-LOGIN KONFIGURATION ===

login_manager = LoginManager()
login_manager.init_app(app)  #
login_manager.login_view = 'login'  # Weiterleitung bei nicht autorisierten Zugriffen


@login_manager.user_loader
def load_user(user_id):
    return Users.query.get(int(user_id)) 
 
# === ROUTEN ===

@app.route('/')
def index():
    return redirect(url_for('login'))

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)

            if user.admin:
                return redirect(url_for('admin'))
            else:
                return redirect(url_for('dashboard'))
        else:
            flash('Ungültige E-Mail oder Passwort.', 'error')

    return render_template('login.html', form=form)

# Logout
@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# Dashboard
@app.route('/dashboard', methods=['GET', 'POST'])
@login_required
def dashboard():
    # Alle Kompetenzen des aktuellen Benutzers laden
    user_competences = UsersCompetence.query.filter_by(users_id=current_user.id).all()

    # Verschachtelte Struktur erstellen: {category: {group: [kompetenzen]}}
    kompetenzstruktur = defaultdict(lambda: defaultdict(list))

    # Kompetenzen nach Kategorie und Gruppe organisieren
    for uc in user_competences:
        knowledge_skill = uc.knowledge_skill  # Zugehörige Kompetenz laden

        # Prüfen ob alle Beziehungen existieren 
        if not knowledge_skill or not knowledge_skill.competence or not knowledge_skill.competence.competence_group:
            continue  

        competence = knowledge_skill.competence  
        competence_group = competence.competence_group  

        # Kompetenz zur entsprechenden Kategorie/Gruppe hinzufügen
        kompetenzstruktur[competence_group][competence].append({
            "name": knowledge_skill.name,
            "level": uc.competence_level
        })

    # Projekte des aktuellen Benutzers laden (mit allen notwendigen Beziehungen)
    user_projects = Project.query.filter(Project.users.contains(current_user)).options(
        db.joinedload(Project.requirements).joinedload(ProjectRequirement.knowledge_skill).joinedload(KnowledgeSkills.competence).joinedload(Competence.competence_group),
        db.joinedload(Project.users)
    ).all()

    # Projektkompetenzen strukturieren
    def structure_project_competences(project):
        project_competence_structure = defaultdict(lambda: defaultdict(list))
        for requirement in project.requirements:
            if (requirement.knowledge_skill and 
                requirement.knowledge_skill.competence and 
                requirement.knowledge_skill.competence.competence_group):
                
                group = requirement.knowledge_skill.competence.competence_group
                competence = requirement.knowledge_skill.competence
                
                project_competence_structure[group][competence].append({
                    "name": requirement.knowledge_skill.name,
                    "level": requirement.competence_level
                })
        return dict(project_competence_structure)

    # Projektkompetenzen für jedes Projekt strukturieren
    for project in user_projects:
        project.competence_structure = structure_project_competences(project)

    return render_template('dashboard.html', 
                         kompetenzstruktur=kompetenzstruktur, 
                         show_competence_update_hint=current_user.should_update_competences, 
                         user_projects=user_projects,
                         form=AdminCompetenceForm())

# Kompetenz-Update-Hinweis ausblenden
@app.route('/dismiss_competence_hint', methods=['POST'])
@login_required
def dismiss_competence_hint():
    # CSRF-Schutz durch Form-Validierung
    form = AdminCompetenceForm()
    if not form.validate_on_submit():
        flash('Ungültige Anfrage.', 'error')
        return redirect(url_for('dashboard'))
        
    current_user.should_update_competences = False
    db.session.commit()
    
    # Prüfen ob zur Kompetenz-Seite weitergeleitet werden soll
    if request.form.get('redirect_to_competence') == 'true':
        return redirect(url_for('competence'))
    else:
        return redirect(url_for('dashboard'))

# Neues Projekt erstellen
@app.route('/project', methods=['GET', 'POST'])
@login_required
def project():
    # Form für CSRF-Schutz erstellen
    form = AdminCompetenceForm()
    
    if request.method == "POST" and form.validate_on_submit(): 
        neuer_name = request.form.get('project_name')
        notiz = request.form.get('notiz', '')  
        
        neues_projekt = Project(project_name=neuer_name, notiz=notiz)
        db.session.add(neues_projekt)
        db.session.commit()  

        # Projektanforderungen verarbeiten und speichern
        for key in request.form:
            # Suche nach Formularfeldern die Kompetenzen definieren
            if key.startswith('projektkompetenzen['):
                knowledge_skill_id_str = key[len('projektkompetenzen['):-1]
                level = request.form.get(key) 

                try:
                    knowledge_skill_id = int(knowledge_skill_id_str)
                except ValueError:
                    continue 

                # Neue Projektanforderung erstellen
                neue_anforderung = ProjectRequirement(
                    project_id=neues_projekt.id,
                    knowledge_skill_id=knowledge_skill_id,
                    competence_level=level
                )
                db.session.add(neue_anforderung)
        
        db.session.commit() 
        flash('Projekt wurde erfolgreich erstellt.', 'success')
        return redirect(url_for('admin')) 

    # Alle Kategorien mit zugehörigen Gruppen und Kompetenzen laden 
    competence_groups = CompetenceGroup.query.options(
        db.joinedload(CompetenceGroup.competences).joinedload(Competence.knowledge_skills)
    ).all()

    return render_template('project.html', competence_groups=competence_groups, form=form)

# Nutzer hinzufügen
@app.route("/adduser", methods=['GET', 'POST'])
@login_required 
def add_user():
    
    form = AddUserForm() 
    
    
    if form.validate_on_submit():
        user = Users.query.filter_by(email=form.email.data).first()
        
        if user is None: 
            hashed_password = generate_password_hash(form.password_hash.data)
            
            # Neuen Benutzer erstellen
            user = Users(
                name=form.name.data, 
                email=form.email.data, 
                password_hash=hashed_password, 
                admin=form.admin.data
            )
            db.session.add(user)
            db.session.commit()
            
            flash(f'Nutzer {form.name.data} wurde erfolgreich erstellt.', 'success')
    
            # Formularfelder nach erfolgreichem Speichern leeren
            form.name.data = '' 
            form.email.data = ''
            form.password_hash.data = ''
            form.admin.data = False
        else:
            flash('Diese E-Mail-Adresse ist bereits registriert.', 'error')
    
    # Alle Nutzer für die Tabelle laden (alphabetisch sortiert)
    users = Users.query.order_by(Users.name.asc()).all()
    
    return render_template('add_user.html', form=form, users=users)

# Kompetenzen mit Level pflegen
@app.route("/competence", methods=['GET', 'POST'])
@login_required
def competence():
    # Form für CSRF-Schutz erstellen
    form = AdminCompetenceForm()
    
    if request.method == 'POST' and form.validate_on_submit():
        for key in request.form:
            if key.startswith("kompetenzen["):
                knowledge_skill_id_str = key[12:-1] 
                level = request.form[key] 

              
                try:
                    knowledge_skill_id = int(knowledge_skill_id_str)
                except ValueError:
                    continue 

                # Prüfen ob Benutzer bereits ein Level für diese Wissen und Fähigkeiten hat
                existing = UsersCompetence.query.filter_by(
                    users_id=current_user.id,
                    knowledge_skill_id=knowledge_skill_id
                ).first()

                if existing:
                    existing.competence_level = level
                else: 
                    new_competence = UsersCompetence(
                        users_id=current_user.id,
                        knowledge_skill_id=knowledge_skill_id,
                        competence_level=level
                    )
                    db.session.add(new_competence)
        
        db.session.commit()  
        flash('Kompetenzen wurden erfolgreich gespeichert.', 'success')
        return redirect(url_for('competence'))

  
    competence_groups = CompetenceGroup.query.options(
        db.joinedload(CompetenceGroup.competences).joinedload(Competence.knowledge_skills)
    ).all()
    # Kompetenzen des aktuellen Nutzers als Dictionary für die Vorauswahl
    current_competences = {uc.knowledge_skill_id: uc.competence_level for uc in current_user.competences}

    return render_template('competence.html', 
                           competence_groups=competence_groups, 
                           current_competences=current_competences,
                           form=form)

# Admin-Bereich
@app.route("/admin", methods=['GET', 'POST'])
@login_required
def admin():
    # Form für CSRF-Schutz erstellen
    form = AdminCompetenceForm()
    
    projekte = Project.query.options(db.joinedload(Project.users)).all()
    all_users = Users.query.all()
    competence_to_group = {}
    all_knowledge_skills = KnowledgeSkills.query.options(
        db.joinedload(KnowledgeSkills.competence).joinedload(Competence.competence_group)
    ).all()

    for knowledge_skill in all_knowledge_skills:
        if knowledge_skill.competence and knowledge_skill.competence.competence_group:
            competence_to_group[knowledge_skill.id] = knowledge_skill.competence.competence_group.name

    selected_project = None
    vergleich = []
    anforderungen = {}
    strukturierte_anforderungen = {}
    
    level_map = {"Kenner": 1, "Könner": 2, "Experte": 3}

    if request.method == 'POST':
        project_id = request.form.get('project_id', type=int)
        if project_id:
            selected_project = Project.query.get_or_404(project_id)
            anforderungen = _get_project_requirements(project_id)
            strukturierte_anforderungen = _structure_requirements(anforderungen)
            vergleich = _compare_user_skills(all_users, anforderungen, level_map)


    ampel_info = {projekt.id: check_kompetenz_abdeckung(projekt) for projekt in projekte}
    fehlende_kompetenzen = _calculate_missing_competences(projekte)
    competence_to_group = _get_competence_to_group_mapping()
    
    # Bereits zugewiesene Benutzer für das ausgewählte Projekt ermitteln
    already_assigned_user_ids = []
    if selected_project:
        already_assigned_user_ids = [user.id for user in selected_project.users]

    return render_template(
        'admin.html',
        projekte=projekte,
        selected_project=selected_project,
        vergleich=vergleich,
        anforderungen=anforderungen,
        strukturierte_anforderungen=strukturierte_anforderungen,
        competence_to_group=competence_to_group,
        ampel_info=ampel_info,
        fehlende_kompetenzen=fehlende_kompetenzen,
        already_assigned_user_ids=already_assigned_user_ids,
        all_users=all_users,
        form=form
    )

# Projektanforderungen laden
def _get_project_requirements(project_id):
    anforderungen_query = ProjectRequirement.query.filter_by(project_id=project_id).all()
    return {r.knowledge_skill_id: r.competence_level for r in anforderungen_query}

# Strukturiert Anforderungen hierarchisch
def _structure_requirements(anforderungen):
    strukturierte_anforderungen = {}
    competence_groups = CompetenceGroup.query.options(
        db.joinedload(CompetenceGroup.competences).joinedload(Competence.knowledge_skills)
    ).all()

    for competence_group in competence_groups:
        strukturierte_anforderungen[competence_group.name] = {}
        for competence in competence_group.competences:
            knowledge_skills_list = []
            for knowledge_skill in competence.knowledge_skills:
                if knowledge_skill.id in anforderungen:
                    knowledge_skills_list.append({
                        "id": knowledge_skill.id,
                        "name": knowledge_skill.name,
                        "level": anforderungen[knowledge_skill.id]
                    })
            if knowledge_skills_list:
                strukturierte_anforderungen[competence_group.name][competence.name] = knowledge_skills_list

    return strukturierte_anforderungen


# Vergleicht Benutzer-Skills mit Projektanforderungen
def _compare_user_skills(all_users, anforderungen, level_map):
    vergleich = []
    
    for user in all_users:
        if user.admin:
            continue
        
       
        user_skills = {c.knowledge_skill_id: c.competence_level for c in user.competences}
        skills_info = {}  

        # Für jede Projektanforderung prüfen wie gut der Benutzer passt
        for skill, projekt_level in anforderungen.items():
            user_level = user_skills.get(skill)  
            
            nutzer_val = level_map.get(user_level, 0)
            projekt_val = level_map.get(projekt_level, 0)

            # Symbol basierend auf Kompetenz-Vergleich bestimmen
            if user_level is None:
                symbol = "❌"  # Nutzer hat diese Kompetenz gar nicht
                user_level = "Nichts"
            elif nutzer_val >= projekt_val:
                symbol = "✅"  # Nutzer erfüllt Anforderung (richtige oder höhere Bewertungsgruppe)
            else:
                symbol = "⚠️"  # Nutzer hat die Kompetenz, aber in niedrigerer Bewertungsgruppe

            skills_info[skill] = {
                "user_level": user_level,
                "projekt_level": projekt_level,
                "symbol": symbol
            }

        # Nutzer mit seinen Kompetenz-Infos zur Vergleichsliste hinzufügen
        vergleich.append({"user": user, "skills": skills_info})
    
    return vergleich

# Berechnet fehlende Kompetenzen für Projekte (inkl. Kompetenzen mit zu niedrigem Level)
def _calculate_missing_competences(projekte):
    fehlende_kompetenzen = {}
    alle_knowledge_skills = {c.id: c.name for c in KnowledgeSkills.query.all()}
    level_map = {"Kenner": 1, "Könner": 2, "Experte": 3}

    for projekt in projekte:
        # Sammle alle Anforderungen mit ihren Leveln
        required_skills = {}
        for requirement in projekt.requirements:
            required_skills[requirement.knowledge_skill_id] = requirement.competence_level
        
        # Sammle alle Kompetenzen aller zugewiesenen Nutzer mit ihren höchsten Leveln
        combined_user_skills = {}
        if projekt.users:
            for user in projekt.users:
                user_competences = UsersCompetence.query.filter_by(users_id=user.id).all()
                for competence in user_competences:
                    skill_id = competence.knowledge_skill_id
                    user_level = competence.competence_level
                    
                    # Behalte das höchste Level pro Kompetenz unter allen Nutzern
                    if skill_id not in combined_user_skills:
                        combined_user_skills[skill_id] = user_level
                    else:
                        current_level_val = level_map.get(combined_user_skills[skill_id], 0)
                        new_level_val = level_map.get(user_level, 0)
                        if new_level_val > current_level_val:
                            combined_user_skills[skill_id] = user_level

        # Prüfe welche Kompetenzen fehlen oder zu niedrig sind
        fehlende_namen = []
        for skill_id, required_level in required_skills.items():
            skill_name = alle_knowledge_skills.get(skill_id, f"Unbekannt (ID {skill_id})")
            
            if skill_id not in combined_user_skills:
                # Kompetenz fehlt komplett
                fehlende_namen.append(f"{skill_name}")
            else:
                user_level = combined_user_skills[skill_id]
                required_level_val = level_map.get(required_level, 0)
                user_level_val = level_map.get(user_level, 0)
                
                if user_level_val < required_level_val:
                    # Kompetenz ist vorhanden, aber Level zu niedrig
                    fehlende_namen.append(f"{skill_name}")
        
        fehlende_kompetenzen[projekt.id] = fehlende_namen

    return fehlende_kompetenzen

# Erstellt Mapping von Kompetenz-ID zu Gruppenname
def _get_competence_to_group_mapping():
    competence_to_group = {}
    all_knowledge_skills = KnowledgeSkills.query.options(
        db.joinedload(KnowledgeSkills.competence).joinedload(Competence.competence_group)
    ).all()
    
    for knowledge_skill in all_knowledge_skills:
        if knowledge_skill.competence and knowledge_skill.competence.competence_group:
            competence_to_group[knowledge_skill.id] = knowledge_skill.competence.competence_group.name
    
    return competence_to_group


# Berechnet Ampel-Status für Projektkompetenzen
def check_kompetenz_abdeckung(projekt):
    # Wenn keine Nutzer zugewiesen sind → Rot
    if not projekt.users:
        return "rot"

    # Level-Mapping für Vergleiche
    level_map = {"Kenner": 1, "Könner": 2, "Experte": 3}
    
    # Sammle alle Anforderungen mit ihren Leveln
    required_skills = {}
    for requirement in projekt.requirements:
        required_skills[requirement.knowledge_skill_id] = requirement.competence_level
    
    if not required_skills:
        return "gruen"  # Keine Anforderungen definiert
    
    # Sammle alle Kompetenzen aller zugewiesenen Nutzer mit ihren Leveln
    combined_user_skills = {}
    for user in projekt.users:
        user_competences = UsersCompetence.query.filter_by(users_id=user.id).all()
        for competence in user_competences:
            skill_id = competence.knowledge_skill_id
            user_level = competence.competence_level
            
            # Behalte das höchste Level pro Kompetenz unter allen Nutzern
            if skill_id not in combined_user_skills:
                combined_user_skills[skill_id] = user_level
            else:
                current_level_val = level_map.get(combined_user_skills[skill_id], 0)
                new_level_val = level_map.get(user_level, 0)
                if new_level_val > current_level_val:
                    combined_user_skills[skill_id] = user_level
    
    # Prüfe jede Anforderung
    fully_covered = True
    partially_covered = False
    
    for skill_id, required_level in required_skills.items():
        if skill_id not in combined_user_skills:
            # Kompetenz fehlt komplett
            fully_covered = False
        else:
            user_level = combined_user_skills[skill_id]
            required_level_val = level_map.get(required_level, 0)
            user_level_val = level_map.get(user_level, 0)
            
            if user_level_val >= required_level_val:
                # Kompetenz ist ausreichend abgedeckt
                partially_covered = True
            else:
                # Kompetenz ist vorhanden, aber Level zu niedrig
                fully_covered = False
                partially_covered = True
    
    # Ampel-Logik:
    if fully_covered and len(required_skills) > 0:
        return "gruen"  # Alle Anforderungen mit richtigem Level abgedeckt
    elif partially_covered:
        return "gelb"   # Teilweise abgedeckt oder Level zu niedrig
    else:
        return "rot"    # Keine Abdeckung



# Projekt abschließen
@app.route('/projekt_abschliessen', methods=['POST'])
@login_required
def projekt_abschliessen():
    # CSRF-Schutz durch Form-Validierung
    form = AdminCompetenceForm()
    if not form.validate_on_submit():
        flash('Ungültige Anfrage.', 'error')
        return redirect(url_for('admin'))
        
    project_id = request.form.get('project_id')  
    notiz = request.form.get('notiz')  

    if not project_id:
        return redirect(url_for('admin')) 
    
 
    projekt = Project.query.get(project_id)
    if projekt:
        projekt.status = 'Abgeschlossen' 
        projekt.notiz = notiz  
        
        # Flag für alle zugewiesenen Mitarbeiter setzen, dass sie ihre Kompetenzen aktualisieren sollen
        for user in projekt.users:
            if not user.admin:
                user.should_update_competences = True
        
        db.session.commit()
        flash(f'Projekt "{projekt.project_name}" wurde erfolgreich abgeschlossen.', 'success')
    
    return redirect(url_for('admin'))

# History-Route: Zeigt abgeschlossene Projekte
@app.route('/history', methods=['GET', 'POST'])
@login_required
def history():
    # Form für CSRF-Schutz erstellen
    form = AdminCompetenceForm()
    
    projekte = Project.query.filter_by(status='Abgeschlossen').options(
        db.joinedload(Project.requirements).joinedload(ProjectRequirement.knowledge_skill),
        db.joinedload(Project.users)
    ).all()
    return render_template('history.html', projekte=projekte, form=form) 

# Benutzer zu Projekt zuweisen
@app.route('/projekt_zuweisen', methods=['POST'])
@login_required
def projekt_zuweisen():
    # CSRF-Schutz durch Form-Validierung
    form = AdminCompetenceForm()
    if not form.validate_on_submit():
        flash('Ungültige Anfrage.', 'error')
        return redirect(url_for('admin'))
  
    project_id = request.form.get('project_id') 
    user_ids = request.form.getlist('user_ids[]') 

    projekt = Project.query.get_or_404(project_id) 

    assigned_count = 0
    
    # Jeden ausgewählten Benutzer dem Projekt zuweisen
    for uid in user_ids:
        try:
            user = Users.query.get(int(uid))
            if user and user not in projekt.users:
                projekt.users.append(user)
                assigned_count += 1
        except ValueError:  
            continue    
    if assigned_count > 0:        
        db.session.commit()  
        flash(f' Nutzer wurde(n) erfolgreich dem Projekt zugewiesen.', 'success')
    
    return redirect(url_for('admin'))

# Admin-Kompetenz-Route: Admins können Kompetenzen anderer Nutzer bearbeiten
@app.route('/admin_competence/<int:user_id>', methods=['GET', 'POST'])
@login_required
def admin_competence(user_id):
    if not current_user.admin:
        return redirect(url_for('dashboard'))
    
    # Zielnutzter laden
    target_user = Users.query.get_or_404(user_id)
    
    form = AdminCompetenceForm()
    
    if request.method == 'POST' and form.validate_on_submit():  
        for key in request.form:
            # Suche nach Kompetenz-Feldern 
            if key.startswith("kompetenzen["):
                knowledge_skill_id_str = key[12:-1]  
                level = request.form[key]  

              
                try:
                    knowledge_skill_id = int(knowledge_skill_id_str)
                except ValueError:
                    continue  

                existing = UsersCompetence.query.filter_by(
                    users_id=target_user.id,
                    knowledge_skill_id=knowledge_skill_id
                ).first()

                if existing:
                    # Vorhandenes Level aktualisieren
                    existing.competence_level = level
                else:
                    new_competence = UsersCompetence(
                        users_id=target_user.id,
                        knowledge_skill_id=knowledge_skill_id,
                        competence_level=level
                    )
                    db.session.add(new_competence)
        
        db.session.commit()  
        return redirect(url_for('admin_user_management'))

    competence_groups = CompetenceGroup.query.options(
        db.joinedload(CompetenceGroup.competences).joinedload(Competence.knowledge_skills)
    ).all()
    
    # Aktuelle Kompetenzen des Zielnutzers laden
    current_competences = {
        uc.knowledge_skill_id: uc.competence_level
        for uc in UsersCompetence.query.filter_by(users_id=target_user.id).all()
    }
    
    return render_template('admin_competence.html', 
                         competence_groups=competence_groups, 
                         target_user=target_user,
                         current_competences=current_competences,
                         form=form)  

# Admin-Nutzer-Verwaltung
@app.route('/admin_users', methods=['GET'])
@login_required
def admin_user_management():
    if not current_user.admin:
        return redirect(url_for('dashboard'))
    
    # Alle Nutzer laden 
    users = Users.query.filter(Users.id != current_user.id).all()
    
    return render_template('admin_user_management.html', users=users)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    
    app.run(debug=True)

