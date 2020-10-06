# trade-remedies-public-ui
<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
[![All Contributors](https://img.shields.io/badge/all_contributors-9-orange.svg?style=flat-square)](#contributors-)
<!-- ALL-CONTRIBUTORS-BADGE:END -->
Public-facing UI for the Trade Remedies system


### Running standalone

It's possible to run the environment as a standalone local app, using virtualenv.
This assumes you have virtualenvwrapper installed, and a virtual env is created (either
via `mkvirtualenv trade-remedies-public` for example).
Use Python 3.6+ as your interpretor.

```
workon trade-remedies-public
./manage.py runserver
```

### Running via Docker

Firstly, you should copy example.env to local.env and add the necessary
environment variables for a local development environment.  local.env is in
.gitignore and should not be committed to the repo.

The public app can be brought up using docker-compose.  The API is similarly
available via Docker and should already be running.

```
make docker-cli
```

This will drop you into a terminal session within the container where you can
run the usual commands eg

```
# Run the development web server
python manage.py runserver_plus 0.0.0.0:8002
# Use the python / django shell
python manage.py shell_plus
# Run the unit tests
python manage.py test
```

Any changes made to source files on your local computer will be reflected in
the container.

### Full Dockerised environment

The repository at https://github.com/uktrade/trade-remedies-docker contains
a fully dockerised environment containerised and integrated together.
To use it, clone the repository at the same level of the api, caseworker and public
repositories and run `docker-compose-up` to bring it up.
More information is within the repository.

#### Unit tests
The unit tests can also be executed in an isolated docker environment.

```
make docker-test
```

## Deployment

Trade Remedies Public UI configuration is performed via the following environment variables:


| Variable name | Required | Description |
| ------------- | ------------- | ------------- |
| `ALLOWED_HOSTS` | Yes | Comma-separated list of hostnames at which the app is accessible |
| `DEBUG`  | Yes | Whether Django's debug mode should be enabled. |
| `DJANGO_SECRET_KEY` | Yes | |
| `DJANGO_SETTINGS_MODULE`  | Yes | |
| `API_BASE_URL`  | Yes | The root url for the API |
| `HEALTH_CHECK_TOKEN` | Yes |  Security auth token for the healthcheck user |
| `VCAP_SERVICES` | Yes | [CloudFoundry-compatible ](https://docs.run.pivotal.io/devguide/deploy-apps/environment-variable.html#VCAP-SERVICES)/[GDS PaaS-compatible](https://docs.cloud.service.gov.uk/deploying_apps.html#system-provided-environment-variables) configuration. The connection string at `redis[0].credentials.uri` is used to connect to Redis, which must include the password if required. It should _not_ end a forward slash. |
| `REDIS_DATABASE_NUMBER` | Yes | The database number in the Redis instance connected to by the details in `VCAP_SERVICES`. |


## Cloud Foundry

The following steps will deploy the API to Cloud Foundry.
Make sure to peform the `cf login` or `cf target` to select the org and space.

```
# cf login -a API-HERE -u YOUR-USER-HERE  # Select the org and space
cf set-env traderemediespublic DISABLE_COLLECTSTATIC 1  # Temporary
cf set-env traderemediespublic DJANGO_SECRET_KEY 'changeme'
cf push
```

## Front end
Make changes to the files in trade_remedies_public/templates/static

In the orchestration report run 
```
make front-end 
```

## Contributors ✨

Thanks goes to these wonderful people ([emoji key](https://allcontributors.org/docs/en/emoji-key)):

<!-- ALL-CONTRIBUTORS-LIST:START - Do not remove or modify this section -->
<!-- prettier-ignore-start -->
<!-- markdownlint-disable -->
<table>
  <tr>
    <td align="center"><a href="http://www.harelmalka.com/"><img src="https://avatars3.githubusercontent.com/u/985978?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Harel Malka</b></sub></a><br /><a href="https://github.com/uktrade/trade-remedies-public/commits?author=harel" title="Code">💻</a></td>
    <td align="center"><a href="https://github.com/bobmeredith"><img src="https://avatars2.githubusercontent.com/u/11422209?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Robert Meredith</b></sub></a><br /><a href="https://github.com/uktrade/trade-remedies-public/commits?author=bobmeredith" title="Code">💻</a> <a href="#design-bobmeredith" title="Design">🎨</a></td>
    <td align="center"><a href="https://github.com/Luisella21"><img src="https://avatars1.githubusercontent.com/u/36708790?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Luisella Strona</b></sub></a><br /><a href="https://github.com/uktrade/trade-remedies-public/pulls?q=is%3Apr+reviewed-by%3ALuisella21" title="Reviewed Pull Requests">👀</a></td>
    <td align="center"><a href="https://github.com/markhigham"><img src="https://avatars1.githubusercontent.com/u/2064710?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Mark Higham</b></sub></a><br /><a href="https://github.com/uktrade/trade-remedies-public/commits?author=markhigham" title="Code">💻</a> <a href="https://github.com/uktrade/trade-remedies-public/commits?author=markhigham" title="Documentation">📖</a></td>
    <td align="center"><a href="https://github.com/nao360"><img src="https://avatars3.githubusercontent.com/u/6898065?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Nao Yoshino</b></sub></a><br /><a href="https://github.com/uktrade/trade-remedies-public/commits?author=nao360" title="Code">💻</a></td>
    <td align="center"><a href="https://github.com/ulcooney"><img src="https://avatars0.githubusercontent.com/u/1695475?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Paul Cooney</b></sub></a><br /><a href="https://github.com/uktrade/trade-remedies-public/commits?author=ulcooney" title="Code">💻</a></td>
    <td align="center"><a href="http://charemza.name/"><img src="https://avatars1.githubusercontent.com/u/13877?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Michal Charemza</b></sub></a><br /><a href="https://github.com/uktrade/trade-remedies-public/commits?author=michalc" title="Code">💻</a> <a href="https://github.com/uktrade/trade-remedies-public/pulls?q=is%3Apr+reviewed-by%3Amichalc" title="Reviewed Pull Requests">👀</a></td>
  </tr>
  <tr>
    <td align="center"><a href="https://github.com/krishnawhite"><img src="https://avatars1.githubusercontent.com/u/5566533?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Krishna White</b></sub></a><br /><a href="https://github.com/uktrade/trade-remedies-public/commits?author=krishnawhite" title="Code">💻</a></td>
    <td align="center"><a href="http://blog.clueful.com.au/"><img src="https://avatars0.githubusercontent.com/u/309976?v=4?s=100" width="100px;" alt=""/><br /><sub><b>Brendan Quinn</b></sub></a><br /><a href="https://github.com/uktrade/trade-remedies-public/commits?author=bquinn" title="Code">💻</a></td>
  </tr>
</table>



<!-- markdownlint-restore -->
<!-- prettier-ignore-end -->
<!-- ALL-CONTRIBUTORS-LIST:END -->

This project follows the [all-contributors](https://github.com/all-contributors/all-contributors) specification. Contributions of any kind welcome!