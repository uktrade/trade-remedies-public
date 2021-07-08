import os

import gunicorn


gunicorn.SERVER_SOFTWARE = "server signature redacted"

accesslog = os.environ.get("GUNICORN_ACCESSLOG", "-")
access_log_format = os.environ.get(
    "GUNICORN_ACCESS_LOG_FORMAT",
    '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %({X-Forwarded-For}i)s',
)
worker_class = "gevent"
worker_connections = os.environ.get("GUNICORN_WORKER_CONNECTIONS", "50")
workers = os.environ.get("GUNICORN_WORKERS", "1")
