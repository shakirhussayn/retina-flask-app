import os
import cv2
import numpy as np
import tensorflow as tf
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager
from .config import Config

# --- Initialize Extensions ---
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message_category = 'info'

# --- Load ML Models ---
dr_model = tf.keras.models.load_model(
    os.path.join('models', 'densenet121_224_clahe.keras')
)
detector = tf.keras.models.load_model(
    os.path.join('models', 'retina_detector.h5')
)
CLASS_LABELS = ['Mild', 'Moderate', 'No_DR', 'Proliferate_DR', 'Severe']
IMG_SIZE = (224, 224)
DET_SIZE = (128, 128)
THRESHOLD = 0.5

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # --- Configure Uploads ---
    UPLOAD_FOLDER = os.path.join(app.root_path, 'static', 'uploads')
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    # --- Initialize Extensions with App ---
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)

    # --- THIS IS THE FIX ---
    # This function tells Flask-Login how to find a specific user from the ID
    # that is stored in their session cookie.
    from .models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    # ----------------------

    # --- Register Blueprints ---
    from app.auth import bp as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    from app.main import bp as main_blueprint
    app.register_blueprint(main_blueprint)
    
    # You may not need this line if you are using migrations
    # with app.app_context():
    #     db.create_all()

    return app