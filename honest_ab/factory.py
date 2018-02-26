from flask import Flask
from .config import config
from honest_ab.login import LoginManager

# Ensure the models are registered before the db mapping is generated
import honest_ab.models

from honest_ab.models import User

from honest_ab.controllers import register_controllers, register_orphans
from honest_ab.database import db, sql_debugging
from honest_ab.template_helpers import register_helpers

def create_app(override_config=None, test_db=False, login_mock=None):
    app = Flask("honest_ab")

    # Config
    if test_db:
        config.update(dict(DB_NAME='honest-ab_test'))
    config.update(override_config or {})

    # Routes
    register_orphans(app)
    register_controllers(app)

    # Bind the database
    db.bind(
        provider='postgres',
        user=config.get('db_user'),
        password=config.get('db_password'),
        host=config.get('db_host'),
        database=config.get('db_name'),
        port=config.get('db_port')
    )
    db.generate_mapping(create_tables=True)

    # Introduce custom template helpers
    register_helpers(app)

    # Initialize login manager
    app.secret_key = config['login_manager_secret_key']
    login_manager = LoginManager()
    login_manager.init_app(app)
    if login_mock != None:
        login_manager._load_user = login_mock
    login_manager.user_loader(User.get_by_id)
    login_manager.login_view = 'users.login_form'

    return app
