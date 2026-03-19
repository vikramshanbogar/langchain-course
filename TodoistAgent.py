import os
from datetime import date
from dotenv import load_dotenv
from google import genai
from google.genai import types
from todoist_api_python.api import TodoistAPI

load_dotenv()

# 1. Configuration
GEMINI_API_KEY = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")
TODOIST_TOKEN = os.environ.get("TODOIST_API_TOKEN")

if not GEMINI_API_KEY or not TODOIST_TOKEN:
    print("Error: GOOGLE_API_KEY (or GEMINI_API_KEY) and TODOIST_API_TOKEN must be set in environment variables.")
    exit(1)

client = genai.Client(api_key=GEMINI_API_KEY)
todoist = TodoistAPI(TODOIST_TOKEN)

# 2. Define the Todoist Tool
def get_raw_tasks() -> str:
    """
    Fetches all tasks from Todoist with minimal formatting so the LLM can 
    categorize them itself.
    """
    try:
        projects = {p.id: p.name for page in todoist.get_projects() for p in page}
        
        tasks = []
        for page in todoist.get_tasks():
            for t in page:
                p_name = projects.get(t.project_id, "Unknown")
                tasks.append(f"Task: {t.content} | Project: {p_name} | Priority: {t.priority} | Due: {t.due.date if t.due else 'None'}")
        
        if not tasks:
            return "No tasks found."
            
        return "\n".join(tasks)

    except Exception as e:
        return f"API Error: {str(e)}"

# 3. Create the Agent Logic
model_id = "gemini-2.5-flash-lite" 

config = types.GenerateContentConfig(
    system_instruction="""You are an expert productivity organizer. 
    Your goal is to take a raw list of tasks and categorize them into logical, easy-to-read sections.
    Use categories like 'Coding Tasks', 'Personal/Lifestyle', 'Administrative/Finance', 'Learning/Research', etc.
    
    Format the output beautifully:
    ## [Category Name]
    - [Task Content] (Priority: X, Due: Y)
    
    After the list, give a brief 1-2 sentence recommendation on which category to tackle first based on priorities.""",
    tools=[get_raw_tasks],
    automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=False)
)

# 4. Execute
print("Categorizing your tasks using AI...")
response = client.models.generate_content(
    model=model_id,
    contents="Please fetch all my tasks and categorize them into logical sections like Coding, Personal, etc. for a clean look.",
    config=config
)

print(f"\n--- Your AI-Categorized Task List ---\n")
print(response.text)
