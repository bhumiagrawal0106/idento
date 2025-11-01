
import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('IDENTO_SECRET') or 'dev-secret-idento-change-me'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'idento.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

