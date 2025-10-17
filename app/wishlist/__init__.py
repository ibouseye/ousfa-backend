from flask import Blueprint

wishlist = Blueprint('wishlist', __name__)

from . import routes