# ... existing imports ...
import os
from dotenv import load_dotenv
from openai import AzureOpenAI

load_dotenv()

AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_KEY = os.getenv("AZURE_OPENAI_API_KEY")
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT")
OPENAI_API_VERSION = os.getenv("OPENAI_API_VERSION", "2024-05-01-preview")

client = AzureOpenAI(
    api_key=AZURE_OPENAI_API_KEY,
    azure_endpoint=AZURE_OPENAI_ENDPOINT,
    api_version=OPENAI_API_VERSION,
)

SYSTEM = open(os.path.join(os.path.dirname(__file__), "..", "prompts", "system.md"), encoding="utf-8").read()
DEVELOPER = open(os.path.join(os.path.dirname(__file__), "..", "prompts", "developer.md"), encoding="utf-8").read()

def tool_schemas():
    return [
        {
            "type": "function",
            "function": {
                "name": "predict_customer",
                "description": "Predict customer satisfaction using the AML endpoint (or local mock).",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "Age": {"type": "integer"},
                        "Gender": {"type": "string", "enum": ["Male", "Female"]},
                        "TravelCategory": {"type": "string", "enum": ["Business", "Personal"]},
                        "TravelClass": {"type": "string", "enum": ["Economy", "Economy Plus", "Business"]},
                        "Distance": {"type": "number"},
                        "DepDelay": {"type": "number"},
                        "ArrDelay": {"type": "number"},
                        "SeatComfort": {"type": "integer"},
                        "Food": {"type": "integer"},
                        "Entertainment": {"type": "integer"},
                        "LegRoom": {"type": "integer"},
                        "Cleanliness": {"type": "integer"},
                        "Luggage": {"type": "integer"},
                        "BoardingPoint": {"type": "string"},
                    },
                    "required": [
                        "Age","Gender","TravelCategory","TravelClass","Distance",
                        "DepDelay","ArrDelay","SeatComfort","Food","Entertainment",
                        "LegRoom","Cleanliness","Luggage","BoardingPoint"
                    ],
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_stat",
                "description": "Return a precomputed statistic by key from the stats store.",
                "parameters": {
                    "type": "object",
                    "properties": {"key": {"type": "string"}},
                    "required": ["key"],
                    "additionalProperties": False,
                },
            },
        },
    ]
