# trade-remedies-public-ui
<!-- ALL-CONTRIBUTORS-BADGE:START - Do not remove or modify this section -->
[![All Contributors](https://img.shields.io/badge/all_contributors-9-orange.svg?style=flat-square)](#contributors-)
<!-- ALL-CONTRIBUTORS-BADGE:END -->
Public-facing UI for the Trade Remedies system

## Code Style

Live Services Team use [Black](https://black.readthedocs.io/en/stable/index.html) for python code formatting and
[flake8](https://flake8.pycqa.org/en/latest/) for code analysis. 

## Development

#### Set up

Firstly, you should copy local.env.example to local.env and add the necessary environment variables for a local development environment.  local.env is in .gitignore and should not be committed to the repo.

Populate the following environment variables in the local.env file:

| Variable name | Required | Description |
| ------------- | ------------- | ------------- |
| `S3_BUCKET_NAME` | Yes | S3 bucket name of bucket used for local dev |
| `S3_STORAGE_KEY`  | Yes | AWS access key ID |
| `S3_STORAGE_SECRET`  | Yes | AWS secret access key | |
| `AWS_REGION`  | Yes | Change if different from "eu-west-2" |

If you are not sure what to use for one of the values above, ask a colleague or contact the SRE team.

#### Running the project

This project should be run using the Trade Remedies orchestration project available at: https://github.com/uktrade/trade-remedies-docker

## Compiling requirements

We use pip-compile from https://github.com/jazzband/pip-tools to manage pip dependencies. This runs from the make file when generating requirements:

Run `make all-requirements`

This needs to be run from the host machine as it does not run in a container.

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