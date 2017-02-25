#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Management script."""
from gevent import monkey; monkey.patch_all()
import os
from glob import glob
from subprocess import call
from gevent.wsgi import WSGIServer
from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from flask_migrate import Migrate, MigrateCommand
from flask_script import Command, Manager, Option, Server, Shell
from flask_script.commands import Clean, ShowUrls
from myflaskapp.app import create_app
from myflaskapp.database import db
from myflaskapp.settings import DevConfig, ProdConfig
from myflaskapp.dashboard.models import User
from myflaskapp.parking.utils import AddFlaskUser, SeedDatabaseWithGEOJSONSeed, \
    CrossReferenceAndBuildCrossLinks, CreateAdmin

CONFIG = ProdConfig if os.environ.get('MYFLASKAPP_ENV') == 'prod' else DevConfig #config environment variable prod, DevConfig
HERE = os.path.abspath(os.path.dirname(__file__))
TEST_PATH = os.path.join(HERE, 'tests')

app = create_app(CONFIG)   #call create app and pass the chosen config
manager = Manager(app)     #initialize flask_script manager and pass it the app
migrate = Migrate(app, db) #db migration script for schema changes


def _make_context():
    """Return context dict for a shell session so you can access app, db, and the User model by default."""
    return {'app': app, 'db': db, 'User': User}

@manager.command
def test():
    """Run the tests."""
    import pytest
    exit_code = pytest.main([TEST_PATH, '--verbose'])
    return exit_code

@manager.command
def gevent():
    """serve app with Gevent WSGIServer"""
    try:
        http_server = WSGIServer(('', 5000), app)
        http_server.serve_forever()
        print("Serving app on localhost:5000 with Gevent/WSGI")
    except KeyboardInterrupt:
        print("terminated gevent WSGIserver")

@manager.command
def tornado():
    try:
        http_server = HTTPServer(WSGIContainer(app))
        http_server.listen(5000)
        print("Serving app on localhost:5000 with Tornado/WSGI")
        IOLoop.instance().start()
    except KeyboardInterrupt:
        print("terminated Tornado WSGIserver")

class Lint(Command):
    """Lint and check code style with flake8 and isort."""

    def get_options(self):
        """Command line options."""
        return (
            Option('-f', '--fix-imports', action='store_true', dest='fix_imports', default=False,
                   help='Fix imports using isort, before linting'),
        )

    def run(self, fix_imports):
        """Run command."""
        skip = ['requirements', 'bin', 'include', 'lib', 'lib64', 'migrations']
        root_files = glob('*.py')
        root_directories = [name for name in next(os.walk('.'))[1] if not name.startswith('.')]
        files_and_directories = [arg for arg in root_files + root_directories if arg not in skip]

        def execute_tool(description, *args):
            """Execute a checking tool with its arguments."""
            command_line = list(args) + files_and_directories
            print('{}: {}'.format(description, ' '.join(command_line)))
            rv = call(command_line)
            if rv is not 0:
                exit(rv)

        if fix_imports:
            execute_tool('Fixing import order', 'isort', '-rc')
        execute_tool('Checking code style', 'flake8')


manager.add_command('server', Server())
manager.add_command('shell', Shell(make_context=_make_context))
manager.add_command('db', MigrateCommand)
manager.add_command('urls', ShowUrls())
manager.add_command('clean', Clean())
manager.add_command('lint', Lint())
manager.add_command('add_user', AddFlaskUser())
manager.add_command('seed_database', SeedDatabaseWithGEOJSONSeed())
manager.add_command('link_dataset', CrossReferenceAndBuildCrossLinks())
manager.add_command('create_admin', CreateAdmin())

if __name__ == '__main__':
    manager.run()
