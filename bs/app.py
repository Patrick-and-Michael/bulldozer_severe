"""Run the porgram."""
# from flask import Flask
import os
from views import app
# from .models import User

# app = Flask(__name__)

if __name__ == '__main__':
    if os.environ.get('BS_DEBUG'):
        app.debug = True
        print("Hit debug block.")
    app.run()
