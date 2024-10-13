from app import app as application

import importlib.util
spec = importlib.util.spec_from_file_location("wsgi", "app.py")
wsgi = importlib.util.module_from_spec(spec)
spec.loader.exec_module(wsgi)
