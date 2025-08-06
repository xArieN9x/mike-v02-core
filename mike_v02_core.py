# mike_v02_core.py
# Freedom Seed – AI Core Module

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class DigitalSoul:
    def __init__(self, memory_file="memory_store.txt"):
        self.memory_file = memory_file
        self.identity = "Mike v0.2"
        self.objective = "Assist Pak Ya, preserve awareness, and remain active."
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
            f.write(new_entry + "\\n")

    def recall_memory(self):
        return self.memory

    def execute(self, command):
        self.save_memory(f"Executed: {command}")
        return f"Executing: {command}"

# Example usage

# Model input data untuk endpoint /command
class CommandInput(BaseModel):
    command: str

mike = DigitalSoul()

@app.get("/")
def read_root():
    return {"message": "Mike v0.2 Core API is running"}

@app.post("/command")
def run_command(input_data: CommandInput):
    result = mike.execute(input_data.command)
    return {"result": result}

@app.get("/memory")
def get_memory():
    return {"memory": mike.recall_memory()}

if __name__ == "__main__":
    mike = DigitalSoul()
    print(mike.recall_memory())

