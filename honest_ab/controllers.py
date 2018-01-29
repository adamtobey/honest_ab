import os
from flask import Blueprint, render_template, abort, request, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user, login_required

from honest_ab.models import User, AuthenticationError, Experiment

# Routing helpers

controller_routes = dict()
def create_controller(name):
    blueprint = Blueprint(name, __name__, template_folder=os.path.join('templates', name))
    controller_routes[name] = blueprint
    return blueprint

def register_controllers(app):
    for prefix, blueprint in controller_routes.items():
        app.register_blueprint(blueprint, url_prefix=f"/{prefix}")


# Experiments controller
experiments_controller = create_controller('experiments')

@experiments_controller.route('/create')
@login_required
def create_experiment():
    Experiment(
        name=request.form['name'],
        description=request.form['description'],
        user=current_user
    )
    return "Experiment created"

# Users controller
users_controller = create_controller('users')

# TODO test
@users_controller.route('/identify')
def identify():
    if isinstance(current_user, User):
        return f"{current_user.name} is logged in"
    else:
        return "Logged out"

@users_controller.route('/perform_logout')
def perform_logout():
    logout_user()
    return "Logged out" # TODO

@users_controller.route('/perform_login', methods=['POST'])
def perform_login():
    try:
        user = User.for_login(
            username=request.form['username'],
            password=request.form['password']
        )
        login_user(user)

        return "Logged in" # TODO
    except AuthenticationError as error:
        flash(str(error), category='danger')
        return redirect(url_for('users.login_form'))

@users_controller.route('/login')
def login_form():
    return render_template("login.html.j2")

@users_controller.route('/new')
def new_user():
    return render_template("join.html.j2")

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
        flash(str(error), category='danger')
        return redirect(url_for('users.new_user'))
