"""OpenAI GPT-4o async client wrapper."""

from openai import AsyncOpenAI

from app.config import settings

gpt_client = AsyncOpenAI(api_key=settings.openai_api_key)
