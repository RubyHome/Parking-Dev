# -*- coding: utf-8 -*-
import os
from myflaskapp.app import celery, create_app
"""
creates the app and pushes an app context.
Celery also needs access to the celery instance, so it is imported from the app package.
!!enable celery from cli with: celery worker -A celery_worker.celery --loglevel=info
"""
app = create_app(os.getenv('FLASK_CONFIG'))
app.app_context().push()
