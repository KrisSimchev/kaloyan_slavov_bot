from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Gmail API Configuration
GMAIL_SENDER = os.getenv("GMAIL_SENDER")
WC_API_BASE_URL = "https://kaloyanslavov.com/wp-json/wc/v3"
CONSUMER_KEY = os.getenv("CONSUMER_KEY")
CONSUMER_SECRET = os.getenv("CONSUMER_SECRET")
