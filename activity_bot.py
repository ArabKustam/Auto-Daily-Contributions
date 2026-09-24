import os
import subprocess
import datetime
import random
import json
import time
import sys

# Configuration
REPO_PATH = os.path.dirname(os.path.abspath(__file__))
FILE_NAME = "daily_activity.txt"
CONFIG_FILE = "config.json"
LOG_FILE = "activity.log"

def log(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {message}"
    print(formatted)
    try:
        log_path = os.path.join(REPO_PATH, LOG_FILE)
        with open(log_path, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")
    except Exception:
        pass

def load_config():
    config_path = os.path.join(REPO_PATH, CONFIG_FILE)
    if not os.path.exists(config_path):
        return {"min_commits": 1, "max_commits": 5}
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log(f"Warning: could not read config.json ({e}), using default values.")
        return {"min_commits": 1, "max_commits": 5}

def run_git_command(command):
    try:
        result = subprocess.run(
            command,
            cwd=REPO_PATH,
            capture_output=True,
            text=True,
            check=True
        )
        log(f"Success: {' '.join(command)}")
        return True
    except subprocess.CalledProcessError as e:
        log(f"Error running command: {' '.join(command)}")
        if e.stdout:
            log(f"stdout: {e.stdout.strip()}")
        if e.stderr:
            log(f"stderr: {e.stderr.strip()}")
        return False

def already_committed_today():
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    try:
        result = subprocess.run(
            ["git", "log", "-1", f"--since={today_str} 00:00:00", "--format=%cd", "--date=short"],
            cwd=REPO_PATH,
            capture_output=True,
            text=True,
            check=True
        )
        if result.stdout.strip() == today_str:
            return True
    except Exception:
        pass
    return False

def make_commit(index, total):
    file_path = os.path.join(REPO_PATH, FILE_NAME)
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(file_path, "a", encoding="utf-8") as f:
        f.write(f"Activity logged at: {current_time} (Commit {index}/{total})\n")
    
    log(f"Updated {FILE_NAME}")

    if not run_git_command(["git", "add", FILE_NAME]):
        return False

    commit_message = f"Daily update: {current_time} - {index}/{total}"
    if not run_git_command(["git", "commit", "-m", commit_message]):
        return False
        
    return True

def main():
    force = "--force" in sys.argv
    log(f"=== Activity bot started (force={force}) ===")

    # 1. Pull latest changes first
    log("Pulling latest changes from remote...")
    run_git_command(["git", "pull", "--rebase", "--autostash"])

    # 2. Check if already committed today
    if not force and already_committed_today():
        today_str = datetime.date.today().strftime("%Y-%m-%d")
        log(f"Already committed today ({today_str}). Skipping execution. Use --force to override.")
        log("=== Activity bot finished ===")
        return

    # 3. Read configuration
    config = load_config()
    min_commits = config.get("min_commits", 1)
    max_commits = config.get("max_commits", 5)
    
    if max_commits < min_commits:
        max_commits = min_commits
        
    num_commits = random.randint(min_commits, max_commits)
    log(f"Scheduled to perform {num_commits} commits today (Range: {min_commits}-{max_commits})")
    
    commits_made = 0
    for i in range(1, num_commits + 1):
        log(f"--- Processing Commit {i}/{num_commits} ---")
        if make_commit(i, num_commits):
            commits_made += 1
            time.sleep(1) 
        else:
            log("Failed to commit. Stopping.")
            break

    if commits_made == 0:
        log("No commits were made. Stopping.")
        return

    # 4. Pull and push to remote
    log("--- Pushing changes to remote ---")
    run_git_command(["git", "pull", "--rebase", "--autostash"])
    
    if run_git_command(["git", "push", "origin", "main"]) or run_git_command(["git", "push"]):
        log("Successfully pushed to remote repository.")
    else:
        log("Push failed! Please check git credentials and remote origin.")
        sys.exit(1)

    log("=== Activity bot completed successfully ===")

if __name__ == "__main__":
    main()
