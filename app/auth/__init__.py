from flask import Blueprint

# This creates the blueprint object that the routes will use
bp = Blueprint('auth', __name__)

# This import is at the bottom to avoid circular dependencies
from app.auth import routes