import os
import re
import json
from uuid import UUID
from functools import wraps
from flask import Blueprint, render_template, abort, request, redirect, url_for, flash

from honest_ab.login import login_user, logout_user, current_user, login_required
from .writeahead import write_data_point_json
from .schema import Schema, InvalidSchemaError, SchemaViolationError, InvalidTestSpecError
from .experiment_state import SerializedExperimentState
from honest_ab.models import User, AuthenticationError, Experiment
from honest_ab.database import *
from .facades import ExperimentResults
from .demo import Demo, DemoResults

# Routing helpers

def default_page():
    return url_for('experiments.list_experiments')

controller_routes = dict()
def create_controller(name):
    blueprint = Blueprint(name, __name__, template_folder=os.path.join('templates', name))
    controller_routes[name] = blueprint
    return blueprint

def create_api_controller(name):
    return create_controller(f"api/v1/{name}")

def register_controllers(app):
    for prefix, blueprint in controller_routes.items():
        app.register_blueprint(blueprint, url_prefix=f"/{prefix}")

orphan_routes = []
def register_orphans(app):
    for args, kwargs, handler in orphan_routes:
        app.route(*args, **kwargs)(handler)

def orphan_route(*route_args, **route_kwargs):
    def orphan_decorator(fun):
        orphan_routes.append((route_args, route_kwargs, fun))
        return fun
    return orphan_decorator

# ==== API ====
api_experiments_controller = create_api_controller('experiments')

# Authentication helpers
APP_KEY_URL_PARAM = "app_key"
def authenticate_api(fun):
    @wraps(fun)
    def handle_request(*args, **kwargs):
        if APP_KEY_URL_PARAM in request.args:
            user = User.from_app_key_hex(request.args[APP_KEY_URL_PARAM])
            if user:
                kwargs['api_user'] = user
                return fun(*args, **kwargs)
            else:
                # CRITICAL: Don't let people explore the app_key space!
                return abort(404)
        else:
            return abort(403) # TODO API-friendly json response

    return handle_request

def abort_wrong_user():
    # CRITICAL: Don't let the user know this app key is in use
    return abort(404)

# Orphan routes

@orphan_route('/')
def home():
    return render_template('home.html.j2')

@orphan_route('/documentation')
def docs():
    return render_template('docs.html.j2')

# Experiments controller

# TODO this needs documentation
@api_experiments_controller.route('/<experiment_uuid>/<variant>/<result>', methods=['POST'])
@db_session
@authenticate_api
def post_experiment_result(experiment_uuid, variant, result, api_user):
    # TODO to avoid leaking experiment UUID's that are in use,
    # could select by uuid and user, but probably overkill.
    experiment = Experiment[experiment_uuid]
    if experiment == None:
        return abort(404) # TODO API-friendly json response
    elif experiment.user.get_pk() != api_user.get_pk():
        return abort_wrong_user()
    else:
        # TODO if it doesn't exist?
        schema = Schema.for_experiment(experiment_uuid)
        try:
            input_point = schema.encode_input_point(request.form, variant, result)
        except SchemaViolationError as e:
            return abort(400) # TODO include error message
        try:
            write_data_point_json(experiment_uuid, json.dumps(input_point))
        except InvalidTestSpecError as e:
            return abort(400)

        return "Success"


# ==== Web UI ====

# Demo Controller
demo_controller = create_controller("demo")

@demo_controller.route("/create", methods=['POST'])
def create_demo():
    try:
        demo = Demo.initialize_from_form(request.form)
        results_id = demo.run()
        return redirect(url_for('demo.show_demo', demo_results_id=results_id))
    except InvalidSchemaError as e:
        flash(str(e), category="danger")
        return redirect(url_for('demo.new_demo'))

@demo_controller.route("/show/<demo_results_id>")
def show_demo(demo_results_id):
    demo_results = DemoResults.find_by_id(demo_results_id)
    return render_template('demo/show.html.j2', results=demo_results, experiment=demo_results.experiment_facade())

@demo_controller.route("/")
def new_demo():
    return render_template("demo/new.html.j2")


# Experiments controller
experiments_controller = create_controller('experiments')

@experiments_controller.route("/all")
@login_required
@db_session
def list_experiments():
    user = current_user()
    experiments = user.experiments
    return render_template("experiments/list.html.j2", experiments=experiments)

@experiments_controller.route('/<experiment_uuid_hex>/show')
@login_required
@db_session
def show_experiment(experiment_uuid_hex):
    experiment_facade = ExperimentResults(experiment_uuid_hex)
    if experiment_facade.experiment.user != current_user():
        return abort(404)
    else:
        return render_template('experiments/show.html.j2', experiment=experiment_facade)

@experiments_controller.route('/create', methods=['POST'])
@login_required
@db_session
def create_experiment():
    try:
        exp = Experiment( # Raises ValueError
            name=request.form['name'],
            description=request.form['description'],
            user=current_user(),
        )
        exp.flush()
        eid = exp.get_pk().hex

        Schema.initialize_from_form(eid, request.form) # Raises InvalidSchemaError
        SerializedExperimentState.initialize(eid)

        flash('Experiment created', category='success')
        return redirect(url_for('experiments.show_experiment', experiment_uuid_hex=exp.get_pk().hex))
    except InvalidSchemaError as e:
        flash(str(e), category="danger")
        return redirect(url_for('experiments.new_experiment'))
    except ValueError as e:
        flash(str(e), category="danger")
        return redirect(url_for('experiments.new_experiment'))

@experiments_controller.route('/new')
@login_required
def new_experiment():
    return render_template("experiments/new.html.j2")

# Users controller
users_controller = create_controller('users')

@users_controller.route('/perform_logout')
def perform_logout():
    logout_user()
    flash('Logged out', category='success')
    return redirect(url_for('users.login_form'))

@users_controller.route('/perform_login', methods=['POST'])
@db_session
def perform_login():
    try:
        user = User.for_login(
            username=request.form['username'],
            password=request.form['password']
        )
        login_user(user)

        flash('Logged in', category='success')
        return redirect(default_page())
    except AuthenticationError as error:
        flash(str(error), category='danger')
        return redirect(url_for('users.login_form'))

@users_controller.route('/login')
def login_form():
    return render_template("users/login.html.j2")

@users_controller.route('/new')
def new_user():
    return render_template("users/join.html.j2")

@users_controller.route('/create', methods=['POST'])
@db_session
def create_user():
    try:
        user = User.create(
            username=request.form['name'],
            password_1=request.form['password_1'],
            password_2=request.form['password_2']
        )
        login_user(user)

        flash("Your account was created", category='success')
        return redirect(default_page())
    except (AuthenticationError, ValueError) as error:
        flash(str(error), category='danger')
        return redirect(url_for('users.new_user'))

# TODO nav
@users_controller.route('/application_key')
@login_required
def user_application_key():
    app_key = current_user().application_key()
    return render_template("users/app_key.html.j2", application_key=app_key)
