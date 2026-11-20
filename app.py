from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'aztu_serbest_is_gizli_acar'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///budget.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- VERİLƏNLƏR BAZASI MODELLƏRİ (CƏDVƏLLƏR) ---
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    expenses = db.relationship('Expense', backref='owner', lazy=True)

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(150), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

with app.app_context():
    db.create_all()

# --- MARŞRUTLAR (ROUTES) ---
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            flash('Bu istifadəçi adı artıq mövcuddur!', 'danger')
            return redirect(url_for('register'))
        
        hashed_pw = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_pw)
        db.session.add(new_user)
        db.session.commit()
        flash('Qeydiyyat uğurla tamamlandı! Daxil ola bilərsiniz.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            return redirect(url_for('dashboard'))
        flash('İstifadəçi adı və ya şifrə yanlışdır!', 'danger')
    return render_template('login.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']

    # Yeni xərc əlavə etmək (INSERT)
    if request.method == 'POST':
        title = request.form['title'].strip()
        amount = float(request.form['amount'])
        category = request.form['category']
        new_expense = Expense(user_id=user_id, title=title, amount=amount, category=category)
        db.session.add(new_expense)
        db.session.commit()
        return redirect(url_for('dashboard'))

    # Kateqoriya üzrə filtr və axtarış (SELECT + WHERE)
    cat_filter = request.args.get('category', 'Hamısı')
    query = Expense.query.filter_by(user_id=user_id)
    if cat_filter != 'Hamısı':
        query = query.filter_by(category=cat_filter)
    
    expenses = query.order_by(Expense.created_at.desc()).all()
    total_spent = sum(item.amount for item in expenses)

    return render_template('dashboard.html', expenses=expenses, total=total_spent, current_cat=cat_filter)

@app.route('/delete/<int:id>')
def delete_expense(id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    expense = Expense.query.get_or_404(id)
    if expense.user_id == session['user_id']:
        db.session.delete(expense)
        db.session.commit()
    return redirect(url_for('dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)