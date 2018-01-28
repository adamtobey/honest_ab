import os
from flask import Blueprint, render_template, abort, request
from flask_login import login_user, current_user

from honest_ab.models import User, AuthenticationError

# Routing helpers

controller_routes = dict()
def create_controller(name):
    blueprint = Blueprint(name, __name__, template_folder=os.path.join('templates', name))
    controller_routes[name] = blueprint
    return blueprint

def register_controllers(app):
    for prefix, blueprint in controller_routes.items():
        app.register_blueprint(blueprint, url_prefix=f"/{prefix}")


# Users controller
users_controller = create_controller('users')

@users_controller.route('/create', methods=['POST'])
def create_user():
    try:
        user = User.create(
            username=request.form['name'],
            password_1=request.form['password_1'],
            password_2=request.form['password_2']
        )
        login_user(user)

        return "Your account was created" #TODO
    except (AuthenticationError, ValueError) as error:
        return str(error) #TODO
