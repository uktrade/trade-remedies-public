import os

import dj_database_url
from dbt_copilot_python.database import database_url_from_env
from dbt_copilot_python.network import setup_allowed_hosts
from dbt_copilot_python.utility import is_copilot

from pydantic import Field

from .cf_env import CloudFoundrySettings


class Settings(CloudFoundrySettings):
    build_step: bool = Field(alias="build_step", default=False)

    def get_allowed_hosts(self) -> list[str]:
        return setup_allowed_hosts(self.ALLOWED_HOSTS)

    def get_database_config(self) -> dict:
        if self.build_step:
            # raise Error(f"get_database_config: in build step according to {self.build_step}", file=sys.stderr)
            return {"default": {}}

        # raise Error(f"get_database_config: NOT in build step according to {self.build_step}", file=sys.stderr)
        return {
            "default": dj_database_url.parse(database_url_from_env("DATABASE_CREDENTIALS")),
        }

    def get_s3_bucket_config(self) -> dict:
        """Return s3 bucket config that matches keys used in CF"""

        if self.build_step:
            return {"aws_region": "", "bucket_name": ""}

        return {"aws_region": self.AWS_REGION, "bucket_name": self.AWS_STORAGE_BUCKET_NAME}


class CircleCIEnvironment(CloudFoundrySettings):
    pass


if is_copilot():
    if "BUILD_STEP" in os.environ:
        # When building use the fake settings in .env.circleci
        env: Settings | CloudFoundrySettings = Settings(
            _env_file=".env.circleci", _env_file_encoding="utf-8"
        )  # type: ignore[call-arg]

    else:
        # when deployed read values from the environment variables
        env = Settings()  # type: ignore[call-arg]

elif "CIRCLECI" in os.environ:
    env = CircleCIEnvironment()  # type: ignore[call-arg]

else:
    # Cloud Foundry environment
    env = CloudFoundrySettings()  # type: ignore[call-arg]
