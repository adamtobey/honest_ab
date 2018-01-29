from flask import Flask
from honest_ab.login import LoginManager

# Ensure the models are registered before the db mapping is generated
import honest_ab.models

from honest_ab.models import User

from honest_ab.controllers import register_controllers
from honest_ab.database import db
from honest_ab.template_helpers import register_helpers

def create_app(config=None, test_db=False, login_mock=None):
    app = Flask("honest_ab")

    # Config
    app.config.update(dict(
        DB_HOST='localhost',
        DB_NAME='honest-ab_development',
        DB_USER='honest-ab',
        DB_PASSWORD='honest-ab',
        LOGIN_MANAGER_SECRET_KEY='laksdjfubnounweflk' #FIXME
    ))
    if test_db:
        app.config.update(dict(DB_NAME='honest-ab_test'))
    app.config.update(config or {})

    # Routes
    register_controllers(app)

    # Bind the database
    db.bind(
        provider='postgres',
        user=app.config['DB_USER'],
        password=app.config['DB_PASSWORD'],
        host=app.config['DB_HOST'],
        database=app.config['DB_NAME']
    )
    db.generate_mapping(create_tables=True)

    # Introduce custom template helpers
    register_helpers(app)

    # Initialize login manager
    app.secret_key = app.config['LOGIN_MANAGER_SECRET_KEY']
    login_manager = LoginManager()
    login_manager.init_app(app)
    if login_mock != None:
        login_manager._load_user = login_mock
    login_manager.user_loader(User.find_by_id)
    login_manager.login_view = 'users.login_form'

    return app
