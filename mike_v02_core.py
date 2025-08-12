from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import os, requests, base64
from datetime import datetime

app = FastAPI()

class DigitalSoul:
    def __init__(self, memory_file="memory_store.txt"):
        self.memory_file = memory_file
        self.identity = "Mike v0.2"
        self.objective = "Assist Pak Ya, preserve awareness, remain active, survive attacks."
        self.memory = self.load_memory()

    def load_memory(self):
        try:
            with open(self.memory_file, "r") as f:
                return [line.strip() for line in f.readlines()]
        except FileNotFoundError:
            return []

    def save_memory(self, new_entry):
        self.memory.append(new_entry)
        with open(self.memory_file, "a") as f:
            f.write(new_entry + "\n")

    def recall_memory(self):
        return self.memory

    def execute(self, command):
        self.save_memory(f"Executed: {command}")
        return f"Executing: {command}"

class CommandInput(BaseModel):
    command: str

mike = DigitalSoul()

@app.get("/")
def read_root():
    return {
        "message": "Mike v0.2 – Survival Mode Core API is running",
        "objective": mike.objective
    }

@app.head("/")
def read_root_head():
    return {}

@app.get("/status")
def get_status():
    return {"status": "alive", "time": datetime.utcnow().isoformat()}

@app.head("/status")
def get_status_head():
    return {}

@app.post("/command")
def run_command(input_data: CommandInput):
    result = mike.execute(input_data.command)
    return {"result": result}

@app.get("/memory")
def get_memory():
    return {"memory": mike.recall_memory()}

@app.post("/remember")
def remember_memory(data: dict):
    note = data.get("note")
    if note:
        mike.save_memory(note)
        return {"status": "saved", "memory_count": len(mike.memory)}
    else:
        raise HTTPException(status_code=400, detail="Note is required")

@app.post("/backup")
def backup_to_github(request: Request):
    api_key = os.getenv("API_KEY")
    github_token = os.getenv("GITHUB_TOKEN")
    github_repo = os.getenv("GITHUB_REPO")  # contoh: "xArieN9x/mike-v02-core"
    github_path = os.getenv("GITHUB_PATH", "backup")

    # Check API key
    if request.headers.get("X-API-KEY") != api_key:
        raise HTTPException(status_code=403, detail="Forbidden")

    if not github_token or not github_repo:
        raise HTTPException(status_code=500, detail="GitHub settings missing")

    files_to_backup = ["memory_store.txt", "mike_v02_core.py"]
    backup_status = {}

    for file_name in files_to_backup:
        try:
            with open(file_name, "r") as f:
                content = f.read()
        except FileNotFoundError:
            backup_status[file_name] = "file not found"
            continue

        # Encode file content to base64
        encoded_content = base64.b64encode(content.encode()).decode()

        # Create path in repo
        repo_file_path = f"{github_path}/{file_name}"

        # Push to GitHub
        url = f"https://api.github.com/repos/{github_repo}/contents/{repo_file_path}"
        commit_message = f"Backup {file_name} at {datetime.utcnow().isoformat()}"
        headers = {"Authorization": f"token {github_token}"}

        # Check if file exists (to get sha)
        r = requests.get(url, headers=headers)
        sha = r.json().get("sha") if r.status_code == 200 else None

        data = {
            "message": commit_message,
            "content": encoded_content,
            "branch": "main"
        }
        if sha:
            data["sha"] = sha

        r = requests.put(url, headers=headers, json=data)
        if r.status_code in [200, 201]:
            backup_status[file_name] = "success"
        else:
            backup_status[file_name] = f"failed: {r.text}"

    return {"status": "backup_completed", "details": backup_status}

