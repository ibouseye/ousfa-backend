import pytest
from app import create_app, db as _db
import app.models # Ensure all models are loaded

@pytest.fixture(scope='session')
def app():
    """Create and configure a new app instance for the entire test session."""
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "WTF_CSRF_ENABLED": False,
        "LOGIN_DISABLED": True, # This must be True
    })
    return app

@pytest.fixture(scope='function')
def test_client(app, db):
    """A test client for the app."""
    return app.test_client()

@pytest.fixture(scope='function')
def db(app):
    """
    Setup our database, this only gets executed once per function.
    """
    with app.app_context():
        _db.create_all()
        yield _db
        _db.session.remove()
        _db.drop_all()