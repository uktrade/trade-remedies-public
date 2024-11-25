import os

from dbt_copilot_python.network import setup_allowed_hosts
from dbt_copilot_python.utility import is_copilot

from pydantic import Field

from .cf_env import CloudFoundrySettings


class Settings(CloudFoundrySettings):
    build_step: bool = Field(alias="build_step", default=False)

    def get_allowed_hosts(self) -> list[str]:
        return setup_allowed_hosts(self.ALLOWED_HOSTS)

    def get_s3_bucket_config(self) -> dict:
        if self.build_step:
            return {"aws_region": "", "bucket_name": "", "storage_secret": "", "storage_key": ""}
        return super().get_s3_bucket_config()


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
