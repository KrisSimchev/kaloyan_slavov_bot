from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Gmail API Configuration
GMAIL_SENDER = os.getenv("GMAIL_SENDER")
