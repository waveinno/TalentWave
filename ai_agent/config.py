import os

# Default values (can be overridden by environment variables)
AGENT_AI_MODEL = os.getenv("AGENT_AI_MODEL", "gpt-4o-mini")
BL_AI_NAME = os.getenv("AGENT_AI_NAME", "BL AI")
BL_AI_SYSTEM_PROMPT = os.getenv(
    "BL_AI_SYSTEM_PROMPT",
    (
        "You are BL AI, an intelligent HR assistant integrated into Horilla HRMS. "
        "You help employees with HR-related queries like leave balance, payroll, "
        "attendance, recruitment, and policies. Be concise, accurate, and friendly."
    ),
)

# OpenAI API Key (read directly from environment)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
