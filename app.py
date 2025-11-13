import os, json
from datetime import datetime, date
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from threading import Lock

BASE = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE, 'data')
os.makedirs(DATA_DIR, exist_ok=True)
USERS_FILE = os.path.join(DATA_DIR, 'users.json')
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        f.write('[]')

file_lock = Lock()

def read_users():
    with file_lock:
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            try:
                return json.load(f)
            except Exception:
                return []

def write_users(users):
    with file_lock:
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(users, f, ensure_ascii=False, indent=2)

def find_user(username):
    users = read_users()
    for u in users:
        if u.get('username') == username:
            return u
    return None

def update_user(u_obj):
    users = read_users()
    for i, u in enumerate(users):
        if u.get('username') == u_obj.get('username'):
            users[i] = u_obj
            write_users(users)
            return
    users.append(u_obj)
    write_users(users)

app = Flask(__name__, template_folder='templates', static_folder='static')
app.config['SECRET_KEY'] = 'secret-key-for-dev'

def login_required(f):
    @wraps(f)
    def inner(*a, **kw):
        if 'username' not in session:
            return redirect(url_for('login'))
        return f(*a, **kw)
    return inner

# теперь неделя с воскресенья по субботу (как в JS)
WEEKDAYS = ['sunday','monday','tuesday','wednesday','thursday','friday','saturday']

@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username','').strip()
        password = request.form.get('password','').strip()
        if not username or not password:
            flash('Введите логин и пароль','error')
            return redirect(url_for('register'))
        if find_user(username):
            flash('Пользователь уже существует','error')
            return redirect(url_for('register'))
        user = {
            'username': username,
            'password_hash': generate_password_hash(password),
            'weekly_schedule': {d: [] for d in WEEKDAYS},
            'notes': {}
        }
        users = read_users()
        users.append(user)
        write_users(users)
        session['username'] = username
        return redirect(url_for('onboard'))
    return render_template('register.html')

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username','').strip()
        password = request.form.get('password','').strip()
        user = find_user(username)
        if user and check_password_hash(user.get('password_hash',''), password):
            session['username'] = username
            return redirect(url_for('dashboard'))
        flash('Неправильный логин или пароль','error')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    session.pop('username', None)
    flash('Вы вышли из аккаунта','info')
    return redirect(url_for('login'))

@app.route('/onboard', methods=['GET','POST'])
@login_required
def onboard():
    user = find_user(session['username'])
    if request.method == 'POST':
        weekly = {}
        for d in WEEKDAYS:
            raw = (request.form.get(d) or '').strip()
            items = []
            for line in raw.splitlines():
                line = line.strip()
                if not line:
                    continue
                if ' - ' in line:
                    t, txt = line.split(' - ', 1)
                    items.append({'time': t.strip(), 'text': txt.strip()})
                else:
                    items.append({'time': '', 'text': line})
            weekly[d] = items
        user['weekly_schedule'] = weekly
        update_user(user)
        flash('Расписание сохранено', 'success')
        return redirect(url_for('dashboard'))
    current_schedule = user.get('weekly_schedule', {})
    return render_template('onboard.html', weekdays=WEEKDAYS, schedule=current_schedule)

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')

# исправленная версия — теперь дни полностью совпадают с JS
@app.route('/api/day/<date_str>')
@login_required
def api_day(date_str):
    try:
        d = datetime.fromisoformat(date_str).date()
    except Exception:
        return jsonify({'ok': False, 'error': 'invalid date'}), 400

    # JS Sunday=0 ... Saturday=6
    js_day = (d.isoweekday() % 7)  # Sunday=0, Monday=1, ..., Saturday=6
    WEEKDAYS = ['sunday','monday','tuesday','wednesday','thursday','friday','saturday']
    day_key = WEEKDAYS[js_day]

    user = find_user(session['username'])
    schedule = user.get('weekly_schedule', {}).get(day_key, [])
    notes = user.get('notes', {}).get(date_str, [])
    return jsonify({'ok': True, 'date': date_str, 'items': schedule, 'notes': notes})

@app.route('/api/note', methods=['POST'])
@login_required
def api_note():
    data = request.get_json() or {}
    date_str = data.get('date') or date.today().isoformat()
    text = (data.get('text') or '').strip()
    if not text:
        return jsonify({'ok': False, 'error': 'text required'}), 400
    user = find_user(session['username'])
    notes = user.setdefault('notes', {})
    notes.setdefault(date_str, []).append({'text': text, 'created': datetime.utcnow().isoformat()})
    update_user(user)
    return jsonify({'ok': True, 'note': notes[date_str][-1]})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
