import os
import subprocess
import datetime
import random
import json
import time

# Configuration
# Path to the repository (current directory where this script runs)
REPO_PATH = os.path.dirname(os.path.abspath(__file__))
FILE_NAME = "daily_activity.txt"
CONFIG_FILE = "config.json"

def load_config():
    config_path = os.path.join(REPO_PATH, CONFIG_FILE)
    if not os.path.exists(config_path):
        return {"min_commits": 1, "max_commits": 5}
    try:
        with open(config_path, "r") as f:
            return json.load(f)
    except:
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
        print(f"Success: {' '.join(command)}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {' '.join(command)}")
        print(f"Output: {e.stdout}")
        print(f"Error: {e.stderr}")
        return False

def make_commit(index, total):
    # 1. Update the file
    file_path = os.path.join(REPO_PATH, FILE_NAME)
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    with open(file_path, "a") as f:
        f.write(f"Activity logged at: {current_time} (Commit {index}/{total})\n")
    
    print(f"Updated {FILE_NAME}")

    # 2. Git add
    if not run_git_command(["git", "add", FILE_NAME]):
        return False

    # 3. Git commit
    commit_message = f"Daily update: {current_time} - {index}/{total}"
    if not run_git_command(["git", "commit", "-m", commit_message]):
        return False
        
    return True

def main():
    print(f"Running activity bot in: {REPO_PATH}")
    
    config = load_config()
    min_commits = config.get("min_commits", 1)
    max_commits = config.get("max_commits", 5)
    
    # Ensure valid range
    if max_commits < min_commits:
        max_commits = min_commits
        
    num_commits = random.randint(min_commits, max_commits)
    print(f"Scheduled to perform {num_commits} commits today (Range: {min_commits}-{max_commits})")
    
    for i in range(1, num_commits + 1):
        print(f"--- Processing Commit {i}/{num_commits} ---")
        if make_commit(i, num_commits):
            # Wait a bit between commits to distinct timestamps if needed, 
            # though script execution time might be enough.
            time.sleep(1) 
        else:
            print("Failed to commit. Stopping.")
            break

    # 4. Git push
    # Push all commits at once at the end
    print("--- Pushing changes to remote ---")
    
    # Try to pull first to avoid conflicts
    print("Pulling latest changes...")
    run_git_command(["git", "pull", "--rebase", "--autostash"])
    
    if run_git_command(["git", "push"]):
        print("Successfully pushed to remote.")
    else:
        print("Push failed. Make sure you have configured a remote 'origin'.")

if __name__ == "__main__":
    main()
