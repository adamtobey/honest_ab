import pytest
from honest_ab.factory import create_app
from honest_ab.database import db, flush

from honest_ab.models import User

app_instance = create_app(test_db = True)

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
