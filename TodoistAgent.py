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
def get_today_tasks() -> list:
    """
    Fetches all active tasks from Todoist due today or overdue.
    Returns a list of dictionaries containing task content and priority.
    """
    try:
        # Todoist priority: 1 (Natural) to 4 (Urgent)
        tasks = todoist.get_tasks(filter="today | overdue")
        return [
            {
                "task": t.content,
                "priority_level": t.priority,
                "due": t.due.date if t.due else "Today"
            }
            for t in tasks
        ]
    except Exception as e:
        return [f"Error fetching tasks: {str(e)}"]

# 3. Create the Agent Logic
# We pass the function itself into the tools list
model_id = "gemini-2.5-flash"

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