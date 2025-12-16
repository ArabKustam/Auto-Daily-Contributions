import os
import subprocess
import datetime
import random

# Configuration
# Path to the repository (current directory where this script runs)
REPO_PATH = os.path.dirname(os.path.abspath(__file__))
FILE_NAME = "daily_activity.txt"

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

def main():
    print(f"Running activity bot in: {REPO_PATH}")
    
    # 1. Update the file
    file_path = os.path.join(REPO_PATH, FILE_NAME)
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Randomly decide how many times to commit today (1 to 3 times) to look natural
    # Or just once. Let's stick to once for simplicity unless requested otherwise.
    
    with open(file_path, "a") as f:
        f.write(f"Activity logged at: {current_time}\n")
    
    print(f"Updated {FILE_NAME}")

    # 2. Git add
    if not run_git_command(["git", "add", FILE_NAME]):
        return

    # 3. Git commit
    commit_message = f"Daily update: {current_time}"
    if not run_git_command(["git", "commit", "-m", commit_message]):
        return

    # 4. Git push
    # Note: This assumes 'origin' and 'main' (or 'master'). 
    # It might fail if no remote is configured yet.
    if run_git_command(["git", "push"]):
        print("Successfully pushed to remote.")
    else:
        print("Push failed. Make sure you have configured a remote 'origin'.")

if __name__ == "__main__":
    # Optional: Random delay to not run exactly at the same second if scheduled
    # time.sleep(random.randint(1, 60)) 
    main()
