import os
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy_utils import EncryptedType
from sqlalchemy_utils.types.encrypted.encrypted_type import FernetEngine
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from .config import Config
from . import db  # <-- THIS IS THE CORRECTED LINE

# Remove: db = SQLAlchemy()
# Remove: field_key = Config.FIELD_ENCRYPTION_KEY.encode()
# The key is now defined in the User/Patient models directly

class User(UserMixin, db.Model):
    id       = db.Column(db.Integer, primary_key=True)
    email    = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(128), nullable=False)
    role     = db.Column(db.String(20), default='staff')

    def set_password(self, pwd):
        self.password = generate_password_hash(pwd)

    def check_password(self, pwd):
        return check_password_hash(self.password, pwd)

class Patient(db.Model):
    id              = db.Column(db.Integer, primary_key=True)
    name            = db.Column(db.String(100), nullable=False)
    date_of_birth   = db.Column(db.Date, nullable=False)
    medical_history = db.Column(
                        EncryptedType(db.Text, Config.FIELD_ENCRYPTION_KEY.encode(), FernetEngine),
                        nullable=True
                      )
    symptoms        = db.Column(
                        EncryptedType(db.Text, Config.FIELD_ENCRYPTION_KEY.encode(), FernetEngine),
                        nullable=True
                      )
    image_filename  = db.Column(db.String(200), nullable=True)
    dr_result       = db.Column(db.String(50),  nullable=True)
    dr_confidence   = db.Column(db.Float,      nullable=True)
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)
    
    user_id         = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    user            = db.relationship('User', backref=db.backref('patients', lazy=True))