
from flask import Flask, render_template, redirect, url_for, flash, request, jsonify
from config import Config
from models import init_db, User
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy import select
from forms import LoginForm, SignupForm, CreateUserForm, ChangePasswordForm
from utils import admin_required, validate_password_policy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash
import os

app = Flask(__name__)
app.config.from_object(Config)
engine = init_db(app.config['SQLALCHEMY_DATABASE_URI'])
SessionLocal = scoped_session(sessionmaker(bind=engine, expire_on_commit=False))

login_manager = LoginManager(app)
login_manager.login_view = 'login'

# Flask-Login user wrapper
class LoginUser(UserMixin):
    def __init__(self, user):
        self.id = user.id
        self.email = user.email
        self.name = user.name
        self.role = user.role

    def get_id(self):
        return str(self.id)

@login_manager.user_loader
def load_user(user_id):
    db = SessionLocal()
    user = db.get(User, int(user_id))
    db.close()
    if user:
        return LoginUser(user)
    return None

# seed admin if none
def seed_admin():
    db = SessionLocal()
    q = db.query(User).filter_by(role='admin').first()
    if not q:
        admin = User(email='admin@idento.com', name='Idento Admin', role='admin')
        admin.set_password('Admin@123')  # strong default; change after first login
        db.add(admin)
        db.commit()
    db.close()

seed_admin()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signup', methods=['GET','POST'])
def signup():
    form = SignupForm()
    if form.validate_on_submit():
        db = SessionLocal()
        exists = db.query(User).filter_by(email=form.email.data.lower()).first()
        if exists:
            flash('Email already registered. Please login or use another email.', 'warning')
            db.close()
            return redirect(url_for('signup'))
        ok, msg = validate_password_policy(form.password.data)
        if not ok:
            flash(msg, 'danger')
            db.close()
            return redirect(url_for('signup'))
        new = User(email=form.email.data.lower(), name=form.name.data, role='student')
        new.set_password(form.password.data)
        db.add(new)
        db.commit()
        db.close()
        flash('Registered successfully. Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html', form=form)

@app.route('/login', methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        db = SessionLocal()
        user = db.query(User).filter_by(email=form.email.data.lower()).first()
        if not user or not user.check_password(form.password.data):
            flash('Invalid credentials', 'danger')
            db.close()
            return redirect(url_for('login'))
        if not user.is_active:
            flash('Account inactive', 'warning')
            db.close()
            return redirect(url_for('login'))
        login_user(LoginUser(user))
        db.close()
        flash('Logged in successfully', 'success')
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('student_welcome'))
    return render_template('login.html', form=form)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out', 'info')
    return redirect(url_for('index'))

@app.route('/student')
@login_required
def student_welcome():
    if current_user.role != 'student':
        flash('Students only area', 'danger')
        return redirect(url_for('index'))
    return render_template('student_welcome.html')

# Admin routes
@app.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    return render_template('admin_dashboard.html')

@app.route('/admin/users')
@login_required
@admin_required
def users_list():
    db = SessionLocal()
    users = db.query(User).all()
    db.close()
    return render_template('users_list.html', users=users)

@app.route('/admin/create', methods=['GET','POST'])
@login_required
@admin_required
def create_user():
    form = CreateUserForm()
    if form.validate_on_submit():
        db = SessionLocal()
        exists = db.query(User).filter_by(email=form.email.data.lower()).first()
        if exists:
            flash('Email already registered.', 'warning')
            db.close()
            return redirect(url_for('create_user'))
        ok, msg = validate_password_policy(form.password.data)
        if not ok:
            flash(msg, 'danger')
            db.close()
            return redirect(url_for('create_user'))
        new = User(email=form.email.data.lower(), name=form.name.data, role=form.role.data)
        new.set_password(form.password.data)
        db.add(new)
        db.commit()
        db.close()
        flash('User created', 'success')
        return redirect(url_for('users_list'))
    return render_template('create_user.html', form=form)

@app.route('/admin/delete/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def delete_user(user_id):
    db = SessionLocal()
    user = db.get(User, user_id)
    if not user:
        flash('User not found', 'warning')
        db.close()
        return redirect(url_for('users_list'))
    if user.role == 'admin':
        flash('Cannot delete admin via UI', 'danger')
        db.close()
        return redirect(url_for('users_list'))
    db.delete(user)
    db.commit()
    db.close()
    flash('User deleted', 'success')
    return redirect(url_for('users_list'))

@app.route('/change_password', methods=['GET','POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        db = SessionLocal()
        user = db.get(User, int(current_user.id))
        if not user or not user.check_password(form.old_password.data):
            flash('Old password incorrect', 'danger')
            db.close()
            return redirect(url_for('change_password'))
        ok, msg = validate_password_policy(form.new_password.data)
        if not ok:
            flash(msg, 'danger')
            db.close()
            return redirect(url_for('change_password'))
        user.set_password(form.new_password.data)
        db.add(user)
        db.commit()
        db.close()
        flash('Password updated', 'success')
        return redirect(url_for('index'))
    return render_template('change_password.html', form=form)

# Portfolio page
@app.route('/portfolio')
def portfolio():
    return render_template('portfolio.html')

# Chatbot endpoint (simple rule-based)
@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json() or {}
    text = (data.get('message') or "").strip().lower()
    # simple rules
    if not text:
        return jsonify({"reply":"Please type something so I can help!"})
    if 'hi' in text or 'hello' in text or 'hii' in text:
        return jsonify({"reply":"Hi! I'm Idento — your friendly assistant. How can I help you today?"})
    if 'help' in text or 'assist' in text:
        return jsonify({"reply":"Tell me what you need: account help, portfolio, login issues, or admin info."})
    if 'contact' in text or 'support' in text or 'customer' in text:
        return jsonify({"reply":"You can call customer care at +91 8502946105 or email bhumi01062005@gmail.com."})
    if 'admin' in text:
        return jsonify({"reply":"Admin features are available under the Admin Dashboard (login required). Only admins can create or delete users."})
    if 'portfolio' in text:
        return jsonify({"reply":"Visit /portfolio to see your portfolio. I can help you add info soon!"})
    # fallback echo
    return jsonify({"reply": f"Sorry, I don't fully understand yet — you said: '{text}'. Try asking for 'help' or 'contact'."})

# API to get current user info (for frontend)
@app.route('/api/me')
def api_me():
    if current_user.is_authenticated:
        return jsonify({"email":current_user.email,"name":current_user.name,"role":current_user.role})
    return jsonify({"email":None})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)

