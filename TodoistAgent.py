import os
from datetime import date
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from todoist_api_python.api import TodoistAPI

load_dotenv()

# 1. Configuration
TODOIST_TOKEN = os.environ.get("TODOIST_API_TOKEN")

if not TODOIST_TOKEN:
    print("Error: TODOIST_API_TOKEN must be set in environment variables.")
    exit(1)

todoist = TodoistAPI(TODOIST_TOKEN)

# 2. Define the Todoist Fetch Logic
def get_all_tasks_raw() -> str:
    """
    Fetches all tasks from Todoist. Returns a raw list for the agent to categorize.
    """
    try:
        # Fetch projects for context
        projects = {p.id: p.name for page in todoist.get_projects() for p in page}
        
        tasks = []
        for page in todoist.get_tasks():
            for t in page:
                p_name = projects.get(t.project_id, "Unknown")
                tasks.append(f"Task: {t.content} | Project: {p_name} | Priority: {t.priority} | Due: {t.due.date if t.due else 'None'}")
        
        if not tasks:
            return "No tasks found in Todoist."
            
        return "\n".join(tasks)

    except Exception as e:
        return f"API Error: {str(e)}"

# 3. Execution Flow
def run_agent():
    print("Fetching tasks from Todoist...")
    raw_tasks = get_all_tasks_raw()
    
    if "API Error" in raw_tasks:
        print(raw_tasks)
        return

    print("Categorizing tasks using local AI (Ollama/Qwen)...")
    
    # Using a smaller qwen model for stability
    llm = ChatOllama(model="qwen2.5-coder:3b", temperature=0)
    
    prompt = f"""
    You are an expert productivity organizer. 
    Take the following raw list of tasks and categorize them into logical, easy-to-read sections.
    Use categories like 'Coding Tasks', 'Personal/Lifestyle', 'Administrative/Finance', 'Learning/Research', etc.
    
    Raw Task List:
    {raw_tasks}
    
    Format the output beautifully:
    ## [Category Name]
    - [Task Content] (Project: [Project Name], Priority: X, Due: Y)
    
    After the list, give a brief 1-2 sentence recommendation on which category to tackle first based on priorities.
    """
    
    response = llm.invoke(prompt)
    
    print(f"\n--- Your Local AI-Categorized Task List ---\n")
    print(response.content)

if __name__ == "__main__":
    run_agent()
