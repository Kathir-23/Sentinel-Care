"""
WSGI config for core project.
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# On Vercel the DB is in /tmp and is empty on every cold start.
# Run migrate + collectstatic BEFORE get_wsgi_application() so that:
#   - All DB tables exist before the first request
#   - Static files are in STATIC_ROOT (/tmp/staticfiles) before Whitenoise starts
if os.environ.get('VERCEL'):
    django.setup()
    from django.core.management import call_command
    try:
        call_command('migrate', '--run-syncdb', verbosity=0)
        call_command('collectstatic', '--noinput', verbosity=0)
        # Seed demo doctors + beds so dashboard isn't empty
        from main.views import initialize_demo_data
        initialize_demo_data()
    except Exception as e:
        print(f"[WSGI startup] error: {e}")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# Vercel requires the WSGI callable to be named 'app'
app = application
