from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_mailman import Mail
from flask_moment import Moment
from flask_wtf.csrf import CSRFProtect
from flask_migrate import Migrate
from flask_assets import Environment
from flask_sitemap import Sitemap

db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
mail = Mail()
moment = Moment()
csrf = CSRFProtect()
migrate = Migrate()
assets = Environment()
sitemap = Sitemap()
