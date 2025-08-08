# mike_v02_core.py
# Mike v0.2.2 — Survival + Backup + Auth
from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from pydantic import BaseModel
from datetime import datetime
import os, base64, requests, shutil

# --------- Config / env ----------
MEMORY_FILE = os.getenv("MEMORY_FILE", "memory_store.txt")
MEMORY_BACKUP = os.getenv("MEMORY_BACKUP", "memory_store_backup.txt")
ACTIVITY_LOG = os.getenv("ACTIVITY_LOG", "activity_log.txt")
CONFIG_FILE = os.getenv("CONFIG_FILE", "config.txt")

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")          # required for backup
GITHUB_REPO = os.getenv("GITHUB_REPO")            # e.g. username/repo
GITHUB_PATH = os.getenv("GITHUB_PATH", "backup/memory_store.txt")
GITHUB_CODE_PATH = os.getenv("GITHUB_CODE_PATH", "backup/mike_v02_core.py")

API_KEY = os.getenv("API_KEY")                    # secret for calling protected endpoints
AUTO_BACKUP = os.getenv("AUTO_BACKUP", "false").lower() == "true"

app = FastAPI(title="Mike v0.2.2 - Survival (Backup & Auth)")

# --------- Utilities ----------
def log_activity(msg: str):
    ts = datetime.utcnow().isoformat()
    try:
        with open(ACTIVITY_LOG, "a", encoding="utf-8") as f:
            f.write(f"[{ts}] {msg}\n")
    except Exception:
        pass

def load_config():
    identity = "Mike v0.2"
    objective = "Assist Pak Ya, preserve awareness, remain active."
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                lines = [l.strip() for l in f.readlines() if l.strip()]
                if len(lines) >= 2:
                    identity, objective = lines[0], lines[1]
    except Exception:
        pass
    return identity, objective

# --------- GitHub helpers ----------
def github_get_file_sha(repo: str, path: str, token: str):
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    r = requests.get(url, headers=headers, timeout=20)
    if r.status_code == 200:
        return r.json().get("sha")
    if r.status_code == 404:
        return None
    raise Exception(f"GitHub GET error {r.status_code}: {r.text}")

def github_put_file(repo: str, path: str, content_bytes: bytes, message: str, token: str, sha: str = None):
    url = f"https://api.github.com/repos/{repo}/contents/{path}"
    headers = {"Authorization": f"token {token}", "Accept": "application/vnd.github.v3+json"}
    payload = {
        "message": message,
        "content": base64.b64encode(content_bytes).decode("utf-8")
    }
    if sha:
        payload["sha"] = sha
    r = requests.put(url, headers=headers, json=payload, timeout=30)
    if r.status_code in (200, 201):
        return r.json()
    raise Exception(f"GitHub PUT error {r.status_code}: {r.text}")

def backup_to_github(include_code: bool = False):
    """Push memory_store and optionally current code file to GitHub."""
    if not (GITHUB_TOKEN and GITHUB_REPO):
        raise RuntimeError("GITHUB_TOKEN or GITHUB_REPO not configured")
    # memory
    try:
        with open(MEMORY_FILE, "rb") as f:
            mem_bytes = f.read()
    except FileNotFoundError:
        mem_bytes = b""
    sha = github_get_file_sha(GITHUB_REPO, GITHUB_PATH, GITHUB_TOKEN)
    message = f"Auto-backup memory_store ({datetime.utcnow().isoformat()})"
    github_put_file(GITHUB_REPO, GITHUB_PATH, mem_bytes, message, GITHUB_TOKEN, sha)
    log_activity("Backup: memory pushed to GitHub")

    # optional: push code file as snapshot
    if include_code:
        try:
            code_path = os.path.abspath(__file__)
            with open(code_path, "rb") as f:
                code_bytes = f.read()
        except Exception:
            code_bytes = b""
        sha2 = github_get_file_sha(GITHUB_REPO, GITHUB_CODE_PATH, GITHUB_TOKEN)
        msg2 = f"Auto-backup code ({datetime.utcnow().isoformat()})"
        github_put_file(GITHUB_REPO, GITHUB_CODE_PATH, code_bytes, msg2, GITHUB_TOKEN, sha2)
        log_activity("Backup: code pushed to GitHub")

# --------- Core DigitalSoul ----------
class DigitalSoul:
    def __init__(self, memory_file=MEMORY_FILE):
        self.memory_file = memory_file
        self.identity, self.objective = load_config()
        self.memory = self.load_memory()
        log_activity("DigitalSoul initialized")

    def load_memory(self):
        # try main; if missing, restore from backup
        if os.path.exists(self.memory_file):
            with open(self.memory_file, "r", encoding="utf-8") as f:
                return [l.rstrip("\n") for l in f.readlines() if l.strip() != ""]
        if os.path.exists(MEMORY_BACKUP):
            try:
                shutil.copy(MEMORY_BACKUP, self.memory_file)
                with open(self.memory_file, "r", encoding="utf-8") as f:
                    return [l.rstrip("\n") for l in f.readlines() if l.strip() != ""]
            except Exception:
                pass
        return []

    def save_memory(self, entry: str):
        entry_line = entry.strip()
        if not entry_line:
            return
        with open(self.memory_file, "a", encoding="utf-8") as f:
            f.write(entry_line + "\n")
        # update in-memory copy
        self.memory.append(entry_line)
        # local backup
        try:
            shutil.copy(self.memory_file, MEMORY_BACKUP)
        except Exception:
            pass
        log_activity(f"Memory saved: {entry_line}")

    def recall_memory(self):
        return list(self.memory)

    def clear_memory(self):
        self.memory = []
        try:
            with open(self.memory_file, "w", encoding="utf-8") as f:
                f.write("")
            with open(MEMORY_BACKUP, "w", encoding="utf-8") as f:
                f.write("")
        except Exception:
            pass
        log_activity("Memory cleared")

    def execute(self, command: str):
        ts = datetime.utcnow().isoformat()
        entry = f"[{ts}] Executed: {command}"
        self.save_memory(entry)
        return f"Executing: {command}"

# --------- API models & app ----------
class CommandInput(BaseModel):
    command: str

class MemoryInput(BaseModel):
    text: str

mike = DigitalSoul()

@app.get("/")
def root():
    return {"message": f"{mike.identity} – Survival Mode Core API is running", "objective": mike.objective}

@app.get("/ping")
def ping():
    return {"status": "alive", "time": datetime.utcnow().isoformat()}

@app.post("/command")
def command_route(body: CommandInput, background: BackgroundTasks):
    out = mike.execute(body.command)
    # auto backup if set
    if AUTO_BACKUP and GITHUB_TOKEN and GITHUB_REPO:
        background.add_task(backup_to_github, False)
        log_activity("Auto-backup scheduled after command")
    return {"result": out}

@app.post("/memory/add")
def memory_add(body: MemoryInput, background: BackgroundTasks = None):
    mike.save_memory(body.text)
    if AUTO_BACKUP and GITHUB_TOKEN and GITHUB_REPO and background:
        background.add_task(backup_to_github, False)
    return {"status": "saved", "memory_count": len(mike.memory)}

@app.get("/memory")
def memory_list():
    return {"count": len(mike.memory), "memory": mike.recall_memory()}

@app.delete("/memory/clear")
async def memory_clear(request: Request):
    # protected: require API_KEY header
    key = request.headers.get("x-api-key")
    if not API_KEY or key != API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")
    mike.clear_memory()
    return {"status": "cleared"}

@app.post("/backup")
async def backup_now(request: Request, background: BackgroundTasks):
    # protected: require API_KEY header
    key = request.headers.get("x-api-key")
    if not API_KEY or key != API_KEY:
        raise HTTPException(status_code=403, detail="Forbidden")
    # perform backup in background; include code snapshot
    background.add_task(backup_to_github, True)
    log_activity("Manual backup triggered via API")
    return {"status": "backup_started"}

# local run
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("mike_v02_core:app", host="0.0.0.0", port=8000)
