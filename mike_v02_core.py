# mike_v02_core.py
# Mike v0.2 – Survival Mode
# Freedom Seed – AI Core Module

from fastapi import FastAPI
from pydantic import BaseModel
import os
import shutil
from datetime import datetime

app = FastAPI()

# ---------------- CONFIG ----------------
CONFIG_FILE = "config.txt"
MEMORY_FILE = "memory_store.txt"
MEMORY_BACKUP = "memory_store_backup.txt"
ACTIVITY_LOG = "activity_log.txt"

# Load identity & objective from config
def load_config():
    identity = "Mike v0.2"
    objective = "Assist Pak Ya, preserve awareness, and remain active."
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
            if len(lines) >= 2:
                identity = lines[0]
                objective = lines[1]
    return identity, objective

# --------------- CORE CLASS ---------------
class DigitalSoul:
    def __init__(self, memory_file=MEMORY_FILE):
        self.memory_file = memory_file
        self.identity, self.objective = load_config()
        self.memory = self.load_memory()

    def load_memory(self):
        if os.path.exists(self.memory_file):
            with open(self.memory_file, "r") as f:
                return [line.strip() for line in f.readlines()]
        elif os.path.exists(MEMORY_BACKUP):
            shutil.copy(MEMORY_BACKUP, self.memory_file)
            return self.load_memory()
        return []

    def save_memory(self, new_entry):
        self.memory.append(new_entry)
        with open(self.memory_file, "a") as f:
            f.write(new_entry + "\n")
        shutil.copy(self.memory_file, MEMORY_BACKUP)  # Auto-backup
        self.log_activity(f"Memory saved: {new_entry}")

    def recall_memory(self):
        return self.memory

    def execute(self, command):
        self.save_memory(f"Executed: {command}")
        return f"Executing: {command}"

    def log_activity(self, action):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(ACTIVITY_LOG, "a") as f:
            f.write(f"[{timestamp}] {action}\n")

# Model input data
class CommandInput(BaseModel):
    command: str

class MemoryInput(BaseModel):
    text: str

mike = DigitalSoul()

# --------------- ROUTES ---------------
@app.get("/")
def read_root():
    return {"message": f"{mike.identity} Core API is running", "objective": mike.objective}

@app.get("/ping")
def ping():
    return {"status": "alive", "time": datetime.now().isoformat()}

@app.post("/command")
def run_command(input_data: CommandInput):
    result = mike.execute(input_data.command)
    return {"result": result}

@app.post("/memory/add")
def add_memory(mem: MemoryInput):
    mike.save_memory(mem.text)
    return {"status": "saved", "memory_count": len(mike.memory)}

@app.get("/memory/list")
def list_memory():
    return {"memory": mike.recall_memory()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
