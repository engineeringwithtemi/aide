from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AIDESettings(BaseSettings):
    "Settings for AIDE Backend."

    gemini_api_key: str
    environment: str = Field(
        "development",
        description="The environment the application is currently running.",
    )
    debug: bool = Field(
        False,
        description="Debug variable that toggles if the application is in debug state.",
    )
    project_name: str = Field("aide", description="Project name.")
    version: str = Field("0.1.0", description="Current version of the project.")
    log_level: str = Field("INFO", description="The current log level.")
    log_to_file: bool = Field(True, description="Should logs be to file or stdout.")
    log_file_path: str = Field(
        "logs/aide.log", description="The name of the file to use."
    )
    log_json: bool = Field(True, description="The current log level")

    database_url: str = Field(description="The database connection url.")
    judge0_url: str = Field(
        "http://localhost:2358", description="The database connection url."
    )
    supabase_url: str = Field(description="Supabase connection url.")
    supabase_key: str = Field(description="Supabase connection key.")

    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")


settings = AIDESettings()  # ty: ignore[missing-argument]
