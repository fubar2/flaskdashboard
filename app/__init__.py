import dash
from flask import Flask, render_template_string
from flask_sqlalchemy import SQLAlchemy
from flask_user import login_required, UserManager, UserMixin
from flask.helpers import get_root_path
from flask_login import login_required
import logging

from config import BaseConfig


def create_app():
    server = Flask(__name__)
    server.config.from_object(BaseConfig)
    logging.basicConfig(
             format='%(asctime)s %(levelname)-8s %(message)s',
             level=logging.INFO,
             datefmt='%Y-%m-%d %H:%M:%S')
    handler = logging.FileHandler('rossdash.log')
    server.logger.addHandler(handler)
    server.logger.info('server starting')
    from app.extensions import db
    db.init_app(server)


    # Initialize Flask-SQLAlchemy
    db = SQLAlchemy(server)

    # Define the User data-model.
    # NB: Make sure to add flask_user UserMixin !!!
    class User(db.Model, UserMixin):
        __tablename__ = 'user'
        id = db.Column(db.Integer, primary_key=True)
        active = db.Column('is_active', db.Boolean(), nullable=False, server_default='1')

        # User authentication information. The collation='NOCASE' is required
        # to search case insensitively when USER_IFIND_MODE is 'nocase_collation'.
        username = db.Column(db.String(100, collation='NOCASE'), nullable=False, unique=True)
        password = db.Column(db.String(255), nullable=False, server_default='')
        password_hash = db.Column(db.String(255), nullable=False, server_default='')
        email_confirmed_at = db.Column(db.DateTime())

        # User information
        first_name = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='')
        last_name = db.Column(db.String(100, collation='NOCASE'), nullable=False, server_default='')

    # Create all database tables
    db.create_all()

    # Setup Flask-User and specify the User data-model
    user_manager = UserManager(server, db, User)

    from app.loadcells.layout import layout as layout1
    from app.loadcells.callbacks import register_callbacks as register_callbacks1
    register_dashapp(server, 'Loadcell plots', 'loadcellplotter', layout1, register_callbacks1)

    from app.rossdashboard.layout import layout as layout2
    from app.rossdashboard.callbacks import register_callbacks as register_callbacks2
    register_dashapp(server, 'Ross dashboard', 'rossdashboard', layout2, register_callbacks2)

    register_extensions(server)
    register_blueprints(server)

    return server


def register_dashapp(app, title, base_pathname, layout, register_callbacks_fun):
    # Meta tags for viewport responsiveness
    meta_viewport = {"name": "viewport", "content": "width=device-width, initial-scale=1, shrink-to-fit=no"}

    my_dashapp = dash.Dash(__name__,
                           server=app,
                           url_base_pathname=f'/{base_pathname}/',
                           assets_folder=get_root_path(__name__) + f'/{base_pathname}/assets/',
                           meta_tags=[meta_viewport])

    my_dashapp.title = title
    my_dashapp.url_base_pathname = f'/{base_pathname}/'
    my_dashapp.layout = layout
    register_callbacks_fun(my_dashapp)
    _protect_dashviews(my_dashapp)


def _protect_dashviews(dashapp):
    for view_func in dashapp.server.view_functions:
        if view_func.startswith(dashapp.url_base_pathname):
            dashapp.server.view_functions[view_func] = login_required(dashapp.server.view_functions[view_func])


def register_extensions(server):
    from app.extensions import db
    from app.extensions import login
    from app.extensions import migrate

    with server.test_request_context():
        login.init_app(server)
        login.login_view = 'main.login'
        migrate.init_app(server, db)


def register_blueprints(server):
    from app.webapp import server_bp

    server.register_blueprint(server_bp)
