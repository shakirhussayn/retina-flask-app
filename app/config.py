import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'change_me')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///patients.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # FALLBACK to your known Fernet key if the ENV var isn't set
    FIELD_ENCRYPTION_KEY = os.getenv(
        'FIELD_ENCRYPTION_KEY',
        'pTd0wSQTm3Vwor9yrAXw0ByFZTTi_qtlrkQHMUEkibM='
    )
