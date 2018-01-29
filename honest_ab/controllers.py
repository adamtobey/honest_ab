import os
from flask import Blueprint, render_template, abort, request, redirect, url_for, flash
from honest_ab.login import login_user, logout_user, current_user, login_required

from honest_ab.models import User, AuthenticationError, Experiment
from honest_ab.database import CacheIndexError, db_session

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

@experiments_controller.route('/create', methods=['POST'])
@login_required
@db_session
def create_experiment():
    try:
        Experiment(
            name=request.form['name'],
            description=request.form['description'],
            user=current_user()
        )
        return "Experiment created"
    except ValueError as error:
        if "Experiment.name" in str(error):
            flash("Experiment must have a name", category="danger")
            return redirect(url_for('experiments.new_experiment'))
        else:
            raise error
    except CacheIndexError as error:
        flash("Experiment names must be unique", category="danger")
        return redirect(url_for('experiments.new_experiment'))

@experiments_controller.route('/new')
@login_required
def new_experiment():
    return render_template("new.html.j2")

# Users controller
users_controller = create_controller('users')

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
