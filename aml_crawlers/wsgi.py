"""
WSGI config for aml_crawlers project.
"""

import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'aml_crawlers.settings')

application = get_wsgi_application()
