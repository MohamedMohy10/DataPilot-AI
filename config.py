import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

NVIDIA_API_KEY = os.getenv("NVIDIA_API_KEY")
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"
MODEL = "openai/gpt-oss-120b"

MAX_ITERATIONS = 7
MAX_RETRIES = 3
PLOT_OUTPUT_DIR = "plots"

def get_client() -> OpenAI:
    return OpenAI(
        api_key=NVIDIA_API_KEY,
        base_url=NVIDIA_BASE_URL
    )