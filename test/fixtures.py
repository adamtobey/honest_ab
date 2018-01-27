import pytest
from honest_ab.factory import create_app
from honest_ab.database import db

app_instance = create_app(test_db = True)

@pytest.fixture
def app():
    with app_instance.app_context():
        yield app_instance

@pytest.fixture
def client(app):
    return app.test_client()
