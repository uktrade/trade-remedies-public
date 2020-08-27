#!/bin/bash -xe
# Used as the docker container's start script.
# This script accepts an action as a single argument to determine which service to start


ARG1=${1-web}

if [ $ARG1 != 'test' ] && [ $ARG1 != 'code' ]
then
    python trade_remedies_public/manage.py migrate --noinput
fi

if [ $ARG1 = 'web' ]
then
    python trade_remedies_public/manage.py runserver_plus 0.0.0.0:8002
elif [ $ARG1 = 'cli' ]
then
    cd trade_remedies_public && /bin/bash
elif [ $ARG1 = 'test' ]
then
    pip install coverage
    cd trade_remedies_public && coverage run manage.py test && coverage xml && coverage report
elif [ $ARG1 = 'code' ]
then
    black trade_remedies_public --check # || flake8
fi
