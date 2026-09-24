import os
import subprocess
import datetime
import random
import json
import time
import sys
import glob

# Paths
REPO_PATH = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(REPO_PATH, "config.json")
STATE_FILE = os.path.join(REPO_PATH, "bot_state.json")
LOG_FILE = os.path.join(REPO_PATH, "activity.log")

# Bot comment markers for natural, harmless code changes
BOT_COMMENT_TEMPLATES = [
    "refactor: optimize internal handler",
    "note: verified compatibility check",
    "sync: update state checkpoint",
    "cleanup: minor code tweak",
    "perf: small loop optimization",
    "debug: validation checkpoint",
    "todo: review edge cases"
]

EXCLUDE_DIRS = {
    ".git", "node_modules", "venv", ".venv", "target", "build", "dist",
    "__pycache__", ".idea", ".vscode", "bin", "obj", "repos"
}

EXCLUDE_FILES = {
    "daily_activity.txt", "config.json", "bot_state.json", "activity.log",
    "settings_ui.py", "activity_bot.py", "run_bot.bat", "run_silent.vbs",
    "package-lock.json", "Cargo.lock"
}

ALLOWED_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".html", ".css", ".scss",
    ".c", ".cpp", ".h", ".hpp", ".rs", ".go", ".java", ".cs", ".sh",
    ".yml", ".yaml", ".md", ".txt"
}

def log(message):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] {message}"
    print(formatted)
    try:
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(formatted + "\n")
    except Exception:
        pass

def load_config():
    default_config = {
        "repositories": [REPO_PATH],
        "normal_day": {"min_commits": 1, "max_commits": 6},
        "special_day": {"chance": 0.15, "min_commits": 12, "max_commits": 48},
        "marathons": {
            "trio_3_days": {"chance": 0.10, "min_commits": 10, "max_commits": 59},
            "week_7_days": {"chance": 0.05, "min_commits": 10, "max_commits": 59}
        },
        "commit_messages": [
            "fix: minor bug fixes", "update dependencies", "refactor: clean up code",
            "chore: maintenance", "fix typo", "docs: update documentation",
            "style: formatting", "update config", "minor improvements",
            "refactor: optimize internal logic", "fix: edge case handling",
            "perf: small optimizations", "sync changes", "cleanup unused code", "wip: self review"
        ]
    }
    if not os.path.exists(CONFIG_FILE):
        return default_config
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log(f"Warning: could not read config.json ({e}), using defaults.")
        return default_config

def load_state():
    default_state = {
        "last_run_date": "",
        "today_status": "none",
        "today_target_commits": 0,
        "today_completed_commits": 0,
        "today_day_type": "normal",
        "marathon": {
            "active": False,
            "type": None,
            "days_left": 0,
            "total_days": 0,
            "assigned_repos": []
        }
    }
    if not os.path.exists(STATE_FILE):
        return default_state
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default_state

def save_state(state):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=4)
    except Exception as e:
        log(f"Error saving state: {e}")

def run_git(repo_dir, args):
    cmd = ["git"] + args
    try:
        res = subprocess.run(
            cmd, cwd=repo_dir, capture_output=True, text=True, check=True
        )
        return True, res.stdout.strip()
    except subprocess.CalledProcessError as e:
        err = e.stderr.strip() if e.stderr else e.stdout.strip()
        log(f"Git error in {os.path.basename(repo_dir)}: {' '.join(cmd)} -> {err}")
        return False, err

def find_candidate_files(repo_dir):
    candidates = []
    for root, dirs, files in os.walk(repo_dir):
        # Filter directories in-place
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith(".")]
        for f in files:
            if f in EXCLUDE_FILES:
                continue
            _, ext = os.path.splitext(f.lower())
            if ext in ALLOWED_EXTENSIONS:
                candidates.append(os.path.join(root, f))
    return candidates

def format_comment(ext, text):
    if ext in {".py", ".sh", ".yml", ".yaml"}:
        return f"# {text}"
    elif ext in {".js", ".jsx", ".ts", ".tsx", ".c", ".cpp", ".h", ".hpp", ".rs", ".go", ".java", ".cs"}:
        return f"// {text}"
    elif ext in {".html", ".md"}:
        return f"<!-- {text} -->"
    elif ext in {".css", ".scss"}:
        return f"/* {text} */"
    return None

def modify_file_safely(repo_dir):
    """
    Subtly modifies a file:
    1. Removes an existing bot comment, OR
    2. Modifies trailing whitespaces/newlines, OR
    3. Adds a harmless comment matching file language.
    Ensures zero syntax breaking and clean git diff.
    """
    candidates = find_candidate_files(repo_dir)
    if not candidates:
        # Fallback to daily_activity.txt if no code files exist
        act_file = os.path.join(repo_dir, "daily_activity.txt")
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(act_file, "a", encoding="utf-8") as f:
            f.write(f"Sync check at {ts}\n")
        return act_file

    file_path = random.choice(candidates)
    _, ext = os.path.splitext(file_path.lower())

    try:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
    except Exception as e:
        log(f"Could not read {file_path}: {e}")
        return None

    # Check if file has existing bot comment
    found_idx = -1
    for i, line in enumerate(lines):
        if any(marker in line for marker in BOT_COMMENT_TEMPLATES):
            found_idx = i
            break

    modified = False
    # If found, 50% chance remove it, 50% chance update it
    if found_idx != -1:
        if random.random() < 0.5:
            # Remove existing bot comment
            lines.pop(found_idx)
            modified = True
        else:
            # Update existing comment
            new_text = random.choice(BOT_COMMENT_TEMPLATES)
            comm = format_comment(ext, new_text)
            if comm:
                lines[found_idx] = comm + "\n"
                modified = True

    if not modified:
        # Strategy: Add a harmless comment or modify trailing newline
        comm_text = random.choice(BOT_COMMENT_TEMPLATES)
        comm = format_comment(ext, comm_text)

        action = random.choice(["add_comment", "toggle_newline", "whitespace"])
        if action == "add_comment" and comm:
            if lines and not lines[-1].endswith("\n"):
                lines[-1] += "\n"
            lines.append(comm + "\n")
            modified = True
        elif action == "toggle_newline":
            if lines and lines[-1] == "\n":
                lines.pop()
            else:
                lines.append("\n")
            modified = True
        else:
            # Subtle trailing space toggle on a blank line or last line
            if lines:
                last_line = lines[-1]
                if last_line.endswith(" \n"):
                    lines[-1] = last_line[:-2] + "\n"
                elif last_line.endswith("\n"):
                    lines[-1] = last_line[:-1] + " \n"
                else:
                    lines[-1] = last_line + "\n"
                modified = True

    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        return file_path
    except Exception as e:
        log(f"Could not write {file_path}: {e}")
        return None

def sync_and_commit(repo_dir, commit_msg):
    repo_name = os.path.basename(repo_dir)

    # 1. Pull latest changes
    run_git(repo_dir, ["pull", "--rebase", "--autostash"])

    # 2. Modify a file safely
    changed_file = modify_file_safely(repo_dir)

    # 3. Check diff
    has_diff = False
    ok, diff_out = run_git(repo_dir, ["status", "--porcelain"])
    if ok and diff_out:
        has_diff = True

    if has_diff and changed_file:
        run_git(repo_dir, ["add", os.path.relpath(changed_file, repo_dir)])
        ok, _ = run_git(repo_dir, ["commit", "-m", commit_msg])
    else:
        # If diff is empty, make an empty commit
        ok, _ = run_git(repo_dir, ["commit", "--allow-empty", "-m", commit_msg])

    if not ok:
        log(f"Failed to commit in {repo_name}")
        return False

    # 4. Push
    run_git(repo_dir, ["pull", "--rebase", "--autostash"])
    ok, _ = run_git(repo_dir, ["push"])
    if not ok:
        # Try pushing current HEAD to origin
        ok, _ = run_git(repo_dir, ["push", "origin", "HEAD"])
    
    if ok:
        log(f"Pushed commit '{commit_msg}' to {repo_name}")
        rel_file = os.path.relpath(changed_file, repo_dir) if changed_file else "empty_commit"
        record_history(repo_name, rel_file, commit_msg)
        return True
    else:
        log(f"Push failed in {repo_name}")
        return False

def record_history(repo_name, changed_file, commit_msg):
    hist_file = os.path.join(REPO_PATH, "activity_history.json")
    history = []
    if os.path.exists(hist_file):
        try:
            with open(hist_file, "r", encoding="utf-8") as f:
                history = json.load(f)
        except Exception:
            history = []
    state = load_state()
    entry = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "date": datetime.date.today().strftime("%Y-%m-%d"),
        "repo": repo_name,
        "file": changed_file,
        "message": commit_msg,
        "day_type": state.get("today_day_type", "Normal Day"),
        "status": "success"
    }
    history.append(entry)
    try:
        with open(hist_file, "w", encoding="utf-8") as f:
            json.dump(history, f, indent=2, ensure_ascii=False)
    except Exception as e:
        log(f"Error saving history: {e}")

def determine_today_plan(config, state):
    """
    Determines commits target and assigned repos based on marathon and special days.
    """
    all_repos = [r for r in config.get("repositories", []) if os.path.exists(r)]
    if not all_repos:
        all_repos = [REPO_PATH]

    marathon = state.get("marathon", {})

    # 1. Continue ongoing marathon
    if marathon.get("active") and marathon.get("days_left", 0) > 0:
        marathon["days_left"] -= 1
        m_type = marathon.get("type", "trio")
        t_range = marathon.get("target_range", [10, 59])
        target_commits = random.randint(t_range[0], t_range[1])
        assigned = [r for r in marathon.get("assigned_repos", []) if os.path.exists(r)]
        if not assigned:
            assigned = random.sample(all_repos, min(2, len(all_repos)))
            marathon["assigned_repos"] = assigned

        if marathon["days_left"] == 0:
            marathon["active"] = False

        state["marathon"] = marathon
        return target_commits, assigned, f"Marathon ({m_type}, {marathon['days_left']} days remaining)"

    # 2. Roll for new marathon or special day
    roll = random.random()
    m_cfg = config.get("marathons", {})
    trio_cfg = m_cfg.get("trio_3_days", {"chance": 0.10, "min_commits": 10, "max_commits": 59})
    week_cfg = m_cfg.get("week_7_days", {"chance": 0.05, "min_commits": 10, "max_commits": 59})
    spec_cfg = config.get("special_day", {"chance": 0.15, "min_commits": 12, "max_commits": 48})
    norm_cfg = config.get("normal_day", {"min_commits": 1, "max_commits": 6})

    p_week = week_cfg.get("chance", 0.05)
    p_trio = trio_cfg.get("chance", 0.10)
    p_spec = spec_cfg.get("chance", 0.15)

    if roll < p_week:
        # Start 7-day marathon
        days = 7
        target = random.randint(week_cfg.get("min_commits", 10), week_cfg.get("max_commits", 59))
        assigned = random.sample(all_repos, min(2, len(all_repos)))
        state["marathon"] = {
            "active": True,
            "type": "7-day sprint",
            "days_left": days - 1,
            "total_days": days,
            "target_range": [week_cfg.get("min_commits", 10), week_cfg.get("max_commits", 59)],
            "assigned_repos": assigned
        }
        return target, assigned, "Marathon (7-day sprint started! Day 1/7)"

    elif roll < (p_week + p_trio):
        # Start 3-day marathon
        days = 3
        target = random.randint(trio_cfg.get("min_commits", 10), trio_cfg.get("max_commits", 59))
        assigned = random.sample(all_repos, min(2, len(all_repos)))
        state["marathon"] = {
            "active": True,
            "type": "3-day sprint",
            "days_left": days - 1,
            "total_days": days,
            "target_range": [trio_cfg.get("min_commits", 10), trio_cfg.get("max_commits", 59)],
            "assigned_repos": assigned
        }
        return target, assigned, "Marathon (3-day sprint started! Day 1/3)"

    elif roll < (p_week + p_trio + p_spec):
        # Special 1-day spike
        target = random.randint(spec_cfg.get("min_commits", 12), spec_cfg.get("max_commits", 48))
        assigned = random.sample(all_repos, min(2, len(all_repos)))
        return target, assigned, "Special Day (1-day high activity spike!)"

    else:
        # Normal day
        target = random.randint(norm_cfg.get("min_commits", 1), norm_cfg.get("max_commits", 6))
        assigned = [random.choice(all_repos)]
        return target, assigned, "Normal Day"

def main():
    force = "--force" in sys.argv
    today_str = datetime.date.today().strftime("%Y-%m-%d")
    log(f"=== Activity Bot Started (force={force}, date={today_str}) ===")

    config = load_config()
    state = load_state()

    # --- REBOOT PROTECTION ---
    if not force:
        if state.get("last_run_date") == today_str and state.get("today_status") == "completed":
            done = state.get("today_completed_commits", 0)
            target = state.get("today_target_commits", 0)
            dtype = state.get("today_day_type", "normal")
            log(f"Reboot protection active: Today's quota already completed ({done}/{target} commits in '{dtype}' mode).")
            log("=== Activity Bot Finished (Skipped) ===")
            return

    # Check if new day or resuming
    if state.get("last_run_date") != today_str or force:
        target_commits, assigned_repos, day_type = determine_today_plan(config, state)
        state["last_run_date"] = today_str
        state["today_status"] = "in_progress"
        state["today_target_commits"] = target_commits
        state["today_completed_commits"] = 0
        state["today_day_type"] = day_type
        save_state(state)
        log(f"Plan for today: {day_type}")
        log(f"Target commits: {target_commits}")
        log(f"Assigned repositories: {[os.path.basename(r) for r in assigned_repos]}")
    else:
        target_commits = state.get("today_target_commits", 1)
        day_type = state.get("today_day_type", "normal")
        assigned_repos = [r for r in state.get("marathon", {}).get("assigned_repos", []) if os.path.exists(r)]
        if not assigned_repos:
            all_r = [r for r in config.get("repositories", []) if os.path.exists(r)]
            assigned_repos = [random.choice(all_r)] if all_r else [REPO_PATH]

    messages = config.get("commit_messages", ["update"])
    completed = state.get("today_completed_commits", 0)

    for i in range(completed + 1, target_commits + 1):
        target_repo = random.choice(assigned_repos)
        commit_msg = random.choice(messages)
        log(f"[{i}/{target_commits}] Processing commit for '{os.path.basename(target_repo)}'...")

        success = sync_and_commit(target_repo, commit_msg)
        if success:
            state["today_completed_commits"] = i
            save_state(state)
            # Small random sleep between pushes
            time.sleep(random.uniform(1.0, 2.5))
        else:
            log(f"Commit {i} encountered an issue. Continuing...")

    state["today_status"] = "completed"
    save_state(state)
    log(f"Successfully finished daily run: completed {state['today_completed_commits']} commits.")
    log("=== Activity Bot Completed ===")

if __name__ == "__main__":
    main()
