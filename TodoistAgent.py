import os

from dotenv import load_dotenv
from google import genai
from google.genai import types
from todoist_api_python.api import TodoistAPI
load_dotenv()
# 1. Configuration
# Replace with your actual tokens or set them in your environment variables
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
TODOIST_TOKEN = os.environ.get("TODOIST_API_TOKEN")

client = genai.Client(api_key=GEMINI_API_KEY)
todoist = TodoistAPI(TODOIST_TOKEN)

# 2. Define the Todoist Tool
from datetime import date

def get_today_tasks() -> str:
    try:
        today = date.today()  # keep as date object, not isoformat()
        tasks = []

        for page in todoist.get_tasks():
            for t in page:
                if t.due:
                    # due.date may be a date object or string depending on version
                    due = t.due.date
                    if isinstance(due, str):
                        due = date.fromisoformat(due)
                    if due <= today:
                        tasks.append(t)

        if not tasks:
            return "No tasks found for today."

        results = []
        for t in tasks:
            results.append(f"Task: {t.content} | Priority: {t.priority} | Due: {t.due.date}")

        return "\n".join(results)

    except Exception as e:
        print(f"[DEBUG] Raw error: {repr(e)}")
        return f"API Error: {str(e)}"
# 3. Create the Agent Logic
# We pass the function itself into the tools list
model_id = "gemini-2.5-flash-lite"

# System instructions help the model act as a productivity coach
config = types.GenerateContentConfig(
    system_instruction="""You are a high-performance productivity assistant. 
    Your job is to fetch the user's Todoist tasks, analyze their importance 
    (Priority 4 is highest), and recommend exactly the top 3 tasks they 
    should focus on today to be most effective.""",
    tools=[get_today_tasks],
    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=False)
)

# 4. Execute
response = client.models.generate_content(
    model=model_id,
    contents="Get my tasks and give me my top 3 priorities.",
    config=config
)

print(f"\n--- Your Top 3 for Today ---\n")
print(response.text)