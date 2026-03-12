"""Global configuration and settings for the Agent Orchestrator."""

import os
from dataclasses import dataclass, field
from dotenv import load_dotenv

load_dotenv()


@dataclass
class Settings:
    """Application settings loaded from environment variables."""

    github_token: str = field(default_factory=lambda: os.getenv("GITHUB_TOKEN", ""))
    model_name: str = field(default_factory=lambda: os.getenv("MODEL_NAME", "gpt-4o"))
    api_base_url: str = field(
        default_factory=lambda: os.getenv("API_BASE_URL", "https://models.inference.ai.azure.com")
    )
    max_tokens: int = field(default_factory=lambda: int(os.getenv("MAX_TOKENS", "4096")))
    temperature: float = field(default_factory=lambda: float(os.getenv("TEMPERATURE", "0.3")))
    verbose: bool = field(
        default_factory=lambda: os.getenv("VERBOSE", "false").lower() == "true"
    )

    def validate(self) -> None:
        """Validate that required settings are configured."""
        if not self.github_token:
            raise ValueError(
                "GITHUB_TOKEN is required. Set it in your .env file or as an environment variable. "
                "Get a token at: https://github.com/settings/tokens"
            )

    def get_llm_kwargs(self) -> dict:
        """Return kwargs for initializing the LangChain ChatOpenAI model."""
        return {
            "model": self.model_name,
            "api_key": self.github_token,
            "base_url": self.api_base_url,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
        }


# Global singleton
settings = Settings()
