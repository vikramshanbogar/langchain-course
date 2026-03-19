import os
import json
import re
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

# 2. Logic to Fetch Tasks with IDs
def get_all_tasks_data():
    try:
        projects = {p.id: p.name for page in todoist.get_projects() for p in page}
        tasks = []
        for page in todoist.get_tasks():
            for t in page:
                tasks.append({
                    "id": t.id,
                    "content": t.content,
                    "project_id": t.project_id,
                    "project_name": projects.get(t.project_id, "Unknown")
                })
        return tasks
    except Exception as e:
        print(f"Error fetching tasks: {e}")
        return []

# 3. Logic to Apply Changes in Todoist
def organize_todoist(categorization_map):
    """
    categorization_map: dict of {task_id: category_name}
    """
    try:
        # Cache sections to avoid redundant API calls
        # project_id -> {section_name: section_id}
        project_sections_cache = {}

        tasks_list = get_all_tasks_data()
        task_lookup = {t["id"]: t for t in tasks_list}

        for task_id, category in categorization_map.items():
            if task_id not in task_lookup:
                continue
            
            task = task_lookup[task_id]
            project_id = task["project_id"]

            # Ensure sections for this project are cached
            if project_id not in project_sections_cache:
                current_sections_pages = todoist.get_sections(project_id=project_id)
                project_sections_cache[project_id] = {}
                for page in current_sections_pages:
                    for s in page:
                        project_sections_cache[project_id][s.name] = s.id

            # Create section if it doesn't exist
            if category not in project_sections_cache[project_id]:
                print(f"Creating section '{category}' in project '{task['project_name']}'...")
                new_section = todoist.add_section(project_id=project_id, name=category)
                project_sections_cache[project_id][category] = new_section.id

            section_id = project_sections_cache[project_id][category]
            
            # Move task to section
            print(f"Moving task '{task['content']}' to '{category}'...")
            todoist.move_task(task_id=task_id, section_id=section_id)

        print("\nOrganization complete!")

    except Exception as e:
        print(f"Error organizing Todoist: {e}")

# 4. Main Execution Flow
def run_agent():
    print("Step 1: Fetching tasks from Todoist...")
    tasks = get_all_tasks_data()
    if not tasks:
        print("No tasks found.")
        return

    # Prepare data for LLM
    task_strings = [f"ID: {t['id']} | Content: {t['content']} | Project: {t['project_name']}" for t in tasks]
    raw_tasks_text = "\n".join(task_strings)

    print("Step 2: AI is categorizing tasks (this may take a moment)...")
    llm = ChatOllama(model="qwen2.5-coder:3b", temperature=0)
    
    prompt = f"""
    You are an expert productivity organizer. 
    Analyze these tasks and categorize them into logical sections like:
    - Coding Tasks
    - Personal/Lifestyle
    - Administrative/Finance
    - Learning/Research
    
    Tasks:
    {raw_tasks_text}
    
    Return ONLY a JSON object where the keys are Task IDs and the values are the category names.
    Example:
    {{
      "12345": "Coding Tasks",
      "67890": "Personal"
    }}
    """
    
    response = llm.invoke(prompt)
    
    # Extract JSON from response
    try:
        # Use regex to find JSON if there's prose
        json_match = re.search(r'\{.*\}', response.content, re.DOTALL)
        if json_match:
            categorization_map = json.loads(json_match.group())
        else:
            print("Failed to parse AI response as JSON.")
            return
    except Exception as e:
        print(f"Error parsing JSON: {e}")
        print("Raw response:", response.content)
        return

    print(f"Step 3: AI identified {len(categorization_map)} tasks to organize.")
    
    # Ask for confirmation before modifying Todoist
    confirm = input("Do you want to apply these changes to your Todoist account? (y/n): ")
    if confirm.lower() == 'y':
        organize_todoist(categorization_map)
    else:
        print("Organization cancelled.")

if __name__ == "__main__":
    run_agent()
