import os

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'change_me')
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///instance/patients.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    FIELD_ENCRYPTION_KEY = os.getenv(
        'FIELD_ENCRYPTION_KEY',
        'pTd0wSQTm3Vwor9yrAXw0ByFZTTi_qtlrkQHMUEkibM='
    )
    
    # --- ADD THIS CELERY CONFIGURATION ---
    CELERY_BROKER_URL = 'redis://localhost:6379/0'
    CELERY_RESULT_BACKEND = 'redis://localhost:6379/0'