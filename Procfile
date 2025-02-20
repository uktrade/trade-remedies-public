web: cd trade_remedies_public && python ./manage.py migrate && python ./manage.py compilescss  && gunicorn config.wsgi --bind 0.0.0.0:8080 --capture-output --config config/gunicorn.py
