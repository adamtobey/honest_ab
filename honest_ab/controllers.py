import os
import re
from flask import Blueprint, render_template, abort, request, redirect, url_for, flash
from honest_ab.login import login_user, logout_user, current_user, login_required
from .distributed_regression import store_experiment_schema, validate_schema

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
        schema_names = dict()
        schema_types = dict()
        for form_key, value in request.form.items():
            m = re.match("^schema_field_(\d+)_(name|type)", form_key)
            if m:
                schema_id, field_type = m.group(1, 2)
                if field_type == "name":
                    schema_names[schema_id] = value
                else:
                    schema_types[schema_id] = value

        schema = {
            schema_names[s_id]: schema_types[s_id]
            for s_id in schema_names.keys()
        }
        if not validate_schema(schema):
            raise ValueError("Invalid Schema")

        experiment = Experiment(
            name=request.form['name'],
            description=request.form['description'],
            user=current_user()
        )

        store_experiment_schema(experiment.get_pk(), schema)
        return "Experiment created"
    except ValueError as error:
        if "Experiment.name" in str(error):
            flash("Experiment must have a name", category="danger")
            return redirect(url_for('experiments.new_experiment'))
        elif "Invalid Schema" in str(error):
            flash("Invalid schema", category="danger") #TODO unhelpful
            return redirect(url_for('experiments.new_experiment'))
        else:
            raise error
    # TODO pony.orm.core.TransactionIntegrityError: Object Experiment[UUID('04a65b3c-1ee1-486d-a027-93861e1e386e'
    # )] cannot be stored in the database. IntegrityError: duplicate key value violates unique constraint "u
    # nq_experiment__name_user"
    # DETAIL:  Key (name, "user")=(New Experiment, 3) already exists.
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

@users_controller.route('/application_key')
@login_required
def user_application_key():
    app_key = current_user().application_key()
    return render_template("app_key.html.j2", application_key=app_key)
