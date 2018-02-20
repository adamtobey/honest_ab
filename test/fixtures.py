import pytest
from flask import _request_ctx_stack, has_request_context
from flask_login import AnonymousUserMixin

from honest_ab.factory import create_app
from honest_ab.database import db, flush
from honest_ab.schema import Schema
from honest_ab.experiment_state import SerializedExperimentState
from honest_ab.models import User, Experiment

class MockLogin(object):

    def __init__(self):
        self.anonymous_user = AnonymousUserMixin()
        self._logged_in_user = self.anonymous_user

    def sync_request_context(self):
        if has_request_context():
            _request_ctx_stack.top.user = self._logged_in_user

    # Mocks flask_login's user lookup, bypassing acessing the session
    # and always returning the provided user. This effectively mocks out
    # flask_login's session management so that current_user will always
    # be the one we set.
    def __call__(self):
        return self.sync_request_context()

    def login(self, user):
        self._logged_in_user = user
        self.sync_request_context()

    def logout(self):
        self._logged_in_user = self.anonymous_user
        self.sync_request_context()

auth_instance = MockLogin()
app_instance = create_app(test_db = True, login_mock=auth_instance)

@pytest.fixture
def auth():
    auth_instance.logout()
    yield auth_instance
    auth_instance.logout()

def make_experiment(user, schema):
    exp = Experiment(
        name="Test Experiment",
        user=user
    )
    exp.flush()
    eid = exp.get_pk().hex
    Schema(eid, schema).save()
    SerializedExperimentState.initialize(eid)
    return exp

def make_user(username="test", password="password"):
    user = User.create(
        username=username,
        password_1=password,
        password_2=password
    )
    flush()
    return user

@pytest.fixture
def app():
    with app_instance.app_context():
        yield app_instance

@pytest.fixture
def client(app):
    return app.test_client()
