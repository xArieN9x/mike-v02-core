# mike_v02_core.py
# Freedom Seed – AI Core Module (Survival Mode v0.2.1)

from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime

app = FastAPI()

class DigitalSoul:
    def __init__(self, memory_file="memory_store.txt"):
        self.memory_file = memory_file
        self.identity = "Mike v0.2.1"
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

    def clear_memory(self):
        self.memory = []
        with open(self.memory_file, "w") as f:
            f.write("")

    def recall_memory(self):
        return self.memory

    def execute(self, command):
        entry = f"[{datetime.utcnow().isoformat()}] Executed: {command}"
        self.save_memory(entry)
        return f"Executing: {command}"

# Model input untuk /command
class CommandInput(BaseModel):
    command: str

mike = DigitalSoul()

@app.get("/")
def read_root():
    return {
        "message": "Mike v0.2.1 – Survival Mode Core API is running",
        "objective": mike.objective
    }

@app.get("/status")
def status():
    return {"status": "alive", "time": datetime.utcnow().isoformat()}

@app.post("/command")
def run_command(input_data: CommandInput):
    result = mike.execute(input_data.command)
    return {"result": result}

@app.get("/memory")
def get_memory():
    return {"memory": mike.recall_memory()}

@app.delete("/memory/clear")
def clear_memory():
    mike.clear_memory()
    return {"status": "memory cleared", "memory_count": len(mike.memory)}
