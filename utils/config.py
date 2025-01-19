from dataclasses import dataclass
from typing import Optional
import os
from dotenv import load_dotenv


class ConfigError(Exception):
    """Raised when there's an error with the configuration."""
    pass

@dataclass
class Config:
    """Configuration class for the bot."""
    discord_token: str
    channel_id: int
    role_id: int
    prefix: str
    success_color: int
    error_color: int

    @classmethod
    def load_from_env(cls) -> 'Config':
        """
        Loads configuration from environment variables.
        Raises ConfigError if required variables are missing.
        """
        load_dotenv()

        def get_env(key: str, required: bool = True) -> Optional[str]:
            value = os.getenv(key)
            if required and not value:
                raise ConfigError(f"Missing required environment variable: {key}")
            return value

        try:
            discord_token = get_env('DISCORD_TOKEN')
            channel_id = int(get_env('CHANNEL_ID'))
            role_id = int(get_env('ROLE_ID'))
        except ValueError as e:
            raise ConfigError(f"Invalid environment variable value: {str(e)}")

        prefix = get_env('PREFIX', required=False) or "!"
        success = get_env('SUCCESS_COLOR', required=False) or 0x2B2D31
        error = get_env('ERROR_COLOR', required=False) or 15224897

        return cls(
            discord_token=discord_token,
            channel_id=channel_id,
            role_id=role_id,
            prefix=prefix,
            success_color=success,
            error_color=error,
        )

    def validate(self) -> None:
        """
        Performs additional validation on the configuration.
        Raises ConfigError if validation fails.
        """
        if len(self.prefix) > 3:
            raise ConfigError("Prefix must be 3 characters or less")

    @classmethod
    def load(cls) -> 'Config':
        """
        Load and validate configuration.
        Returns a validated Config instance.
        """
        config = cls.load_from_env()
        config.validate()
        return config