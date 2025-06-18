from flask import render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from app import db
from app.auth import bp  # Import the blueprint object 'bp'
from app.models import User
from app.forms import LoginForm, RegisterForm

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RegisterForm()
    if form.validate_on_submit():
        u = User(email=form.email.data, role='staff')
        u.set_password(form.password.data)
        db.session.add(u)
        db.session.commit()
        flash('Account created—please log in', 'success')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form, title='Register')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        u = User.query.filter_by(email=form.email.data).first()
        if u and u.check_password(form.password.data):
            login_user(u)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.home'))
        flash('Invalid credentials', 'danger')
    return render_template('auth/login.html', form=form, title='Login')

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('auth.login'))