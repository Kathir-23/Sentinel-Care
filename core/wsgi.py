"""
WSGI config for core project.
"""

import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# On Vercel the DB lives in /tmp and is empty on every cold start.
# Auto-migrate so tables exist before the first request hits.
if os.environ.get('VERCEL'):
    import django
    django.setup()
    from django.core.management import call_command
    try:
        call_command('migrate', '--run-syncdb', verbosity=0)
        # Seed demo data (doctors + beds) so dashboard isn't empty
        from main.views import initialize_demo_data
        initialize_demo_data()
    except Exception as e:
        print(f"[WSGI startup] migrate/seed error: {e}")

application = get_wsgi_application()

# Vercel requires the WSGI callable to be named 'app'
app = application
