import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./clarity.db")
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
TOKEN_HOURS = int(os.getenv("TOKEN_HOURS", "12"))
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@clarity.local")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
AI_MODEL = os.getenv("AI_MODEL", "claude-sonnet-4-6")
CATEGORIES = ["electricity", "fuel", "transport", "waste", "other"]
