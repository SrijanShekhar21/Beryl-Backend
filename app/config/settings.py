import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")