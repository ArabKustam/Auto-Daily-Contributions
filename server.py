import http.server
import socketserver
import json
import os
import sys
import subprocess
import urllib.parse
import webbrowser
import datetime
import random

PORT = 5050
REPO_PATH = os.path.dirname(os.path.abspath(__file__))
WEB_DIR = os.path.join(REPO_PATH, "web")
CONFIG_FILE = os.path.join(REPO_PATH, "config.json")
STATE_FILE = os.path.join(REPO_PATH, "bot_state.json")
HISTORY_FILE = os.path.join(REPO_PATH, "activity_history.json")
LOG_FILE = os.path.join(REPO_PATH, "activity.log")
TASK_NAME = "AutoDailyContributions"

def get_pythonw_path():
    py_dir = os.path.dirname(sys.executable)
    pyw = os.path.join(py_dir, "pythonw.exe")
    if os.path.exists(pyw):
        return pyw
    return "pythonw.exe"

def get_startup_path():
    appdata = os.environ.get("APPDATA")
    if not appdata:
        appdata = os.path.join(os.path.expanduser("~"), "AppData", "Roaming")
    return os.path.join(
        appdata,
        "Microsoft", "Windows", "Start Menu", "Programs", "Startup",
        "AutoDailyContributions.bat"
    )

def is_autostart_enabled():
    return os.path.exists(get_startup_path())

def is_scheduler_enabled():
    try:
        res = subprocess.run(["schtasks", "/query", "/tn", TASK_NAME], capture_output=True, text=True)
        return res.returncode == 0
    except Exception:
        return False

def load_json(path, default=None):
    if default is None:
        default = {}
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return default

def save_json(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        return True
    except Exception as e:
        print("Save error:", e)
        return False

class DashboardHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/status":
            self.send_json(self.get_status_data())
        elif path == "/api/analytics":
            self.send_json(self.get_analytics_data())
        elif path == "/api/logs":
            self.send_json(self.get_logs_data())
        elif path == "/api/config":
            self.send_json(load_json(CONFIG_FILE, {}))
        else:
            if path == "/":
                self.path = "/index.html"
            super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        try:
            payload = json.loads(body)
        except Exception:
            payload = {}

        if path == "/api/run-now":
            self.handle_run_now()
        elif path == "/api/config":
            self.handle_save_config(payload)
        elif path == "/api/start-marathon":
            self.handle_start_marathon(payload)
        elif path == "/api/toggle-scheduler":
            self.handle_toggle_scheduler(payload)
        elif path == "/api/toggle-autostart":
            self.handle_toggle_autostart(payload)
        elif path == "/api/open-repos":
            self.handle_open_repos()
        else:
            self.send_error(404, "Endpoint not found")

    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def get_status_data(self):
        state = load_json(STATE_FILE, {})
        config = load_json(CONFIG_FILE, {})
        history = load_json(HISTORY_FILE, [])

        repos = [r for r in config.get("repositories", []) if os.path.exists(r)]
        if not repos:
            repos = [REPO_PATH]

        # Calculate per-repo stats
        repo_stats = []
        for r_path in repos:
            r_name = os.path.basename(r_path)
            r_history = [h for h in history if h.get("repo") == r_name]
            files_touched = set(h.get("file") for h in r_history if h.get("file"))
            last_commit = r_history[-1].get("timestamp") if r_history else "Никогда"

            # Check branch
            branch = "main"
            try:
                res = subprocess.run(["git", "-C", r_path, "branch", "--show-current"], capture_output=True, text=True)
                if res.returncode == 0 and res.stdout.strip():
                    branch = res.stdout.strip()
            except Exception:
                pass

            repo_stats.append({
                "name": r_name,
                "path": r_path,
                "branch": branch,
                "commits_count": len(r_history),
                "files_count": len(files_touched),
                "last_commit_time": last_commit
            })

        return {
            "today_target_commits": state.get("today_target_commits", 0),
            "today_completed_commits": state.get("today_completed_commits", 0),
            "today_status": state.get("today_status", "none"),
            "today_day_type": state.get("today_day_type", "Normal Day"),
            "marathon": state.get("marathon", {}),
            "total_commits": len(history),
            "repositories": repos,
            "repositories_stats": repo_stats,
            "scheduler_enabled": is_scheduler_enabled(),
            "autostart_enabled": is_autostart_enabled(),
            "last_run_date": state.get("last_run_date", "")
        }

    def get_analytics_data(self):
        history = load_json(HISTORY_FILE, [])

        # 1. Files breakdown
        file_counts = {}
        for h in history:
            repo = h.get("repo", "unknown")
            f = h.get("file", "unknown")
            key = f"{repo}|{f}"
            if key not in file_counts:
                file_counts[key] = {
                    "repo": repo,
                    "file": f,
                    "count": 0,
                    "edit_type": "Комментарий / Whitespace",
                    "last_modified": h.get("timestamp", "")
                }
            file_counts[key]["count"] += 1
            file_counts[key]["last_modified"] = h.get("timestamp", file_counts[key]["last_modified"])

        files_analytics = list(file_counts.values())
        files_analytics.sort(key=lambda x: x["count"], reverse=True)

        # 2. Heatmap data for last 28 days
        today = datetime.date.today()
        heatmap = []
        commits_by_date = {}
        for h in history:
            d = h.get("date")
            if d:
                commits_by_date[d] = commits_by_date.get(d, 0) + 1

        for i in range(27, -1, -1):
            day = today - datetime.timedelta(days=i)
            day_str = day.strftime("%Y-%m-%d")
            heatmap.append({
                "date": day_str,
                "count": commits_by_date.get(day_str, 0)
            })

        # 3. Categories breakdown
        categories = {
            "fix": 0,
            "refactor": 0,
            "update": 0,
            "docs": 0,
            "style": 0,
            "other": 0
        }
        for h in history:
            msg = h.get("message", "").lower()
            if "fix" in msg:
                categories["fix"] += 1
            elif "refactor" in msg:
                categories["refactor"] += 1
            elif "update" in msg:
                categories["update"] += 1
            elif "doc" in msg:
                categories["docs"] += 1
            elif "style" in msg:
                categories["style"] += 1
            else:
                categories["other"] += 1

        return {
            "files_analytics": files_analytics,
            "heatmap_data": heatmap,
            "categories": categories
        }

    def get_logs_data(self):
        history = load_json(HISTORY_FILE, [])
        raw_log = ""
        if os.path.exists(LOG_FILE):
            try:
                with open(LOG_FILE, "r", encoding="utf-8", errors="ignore") as f:
                    raw_log = f.read()[-4000:]
            except Exception:
                pass
        return {
            "history": history,
            "raw_log": raw_log
        }

    def handle_run_now(self):
        try:
            res = subprocess.run(
                [sys.executable, os.path.join(REPO_PATH, "activity_bot.py"), "--force"],
                cwd=REPO_PATH,
                capture_output=True,
                text=True
            )
            output = res.stdout if res.returncode == 0 else f"{res.stdout}\n{res.stderr}"
            self.send_json({"success": res.returncode == 0, "output": output})
        except Exception as e:
            self.send_json({"success": False, "output": str(e)}, status=500)

    def handle_save_config(self, payload):
        cfg = load_json(CONFIG_FILE, {})
        if "normal_day" in payload:
            cfg["normal_day"] = payload["normal_day"]
        if "special_day" in payload:
            cfg["special_day"]["min_commits"] = payload["special_day"].get("min_commits", 12)
            cfg["special_day"]["max_commits"] = payload["special_day"].get("max_commits", 48)
        if "marathons" in payload:
            cfg["marathons"] = payload["marathons"]

        ok = save_json(CONFIG_FILE, cfg)
        self.send_json({"success": ok})

    def handle_start_marathon(self, payload):
        days = payload.get("days", 3)
        state = load_json(STATE_FILE, {})
        cfg = load_json(CONFIG_FILE, {})

        if days == 0:
            # Cancel marathon
            state["marathon"] = {
                "active": False,
                "type": None,
                "days_left": 0,
                "total_days": 0,
                "assigned_repos": []
            }
            save_json(STATE_FILE, state)
            self.send_json({"success": True, "message": "Марафон остановлен. Бот вернулся в обычный режим."})
            return

        repos = [r for r in cfg.get("repositories", []) if os.path.exists(r)]
        if not repos:
            repos = [REPO_PATH]
        assigned = random.sample(repos, min(2, len(repos)))

        state["marathon"] = {
            "active": True,
            "type": f"{days}-дневный спринт",
            "days_left": days,
            "total_days": days,
            "target_range": [10, 59],
            "assigned_repos": assigned
        }
        state["today_status"] = "in_progress"
        save_json(STATE_FILE, state)
        names = ", ".join([os.path.basename(r) for r in assigned])
        self.send_json({"success": True, "message": f"Марафон на {days} дней активирован! Репозитории: {names}"})

    def handle_toggle_scheduler(self, payload):
        enabled = payload.get("enabled", True)
        if enabled:
            pyw = get_pythonw_path()
            ps_cmd = (
                f'$action = New-ScheduledTaskAction -Execute "{pyw}" '
                f'-Argument "\`"{REPO_PATH}\\activity_bot.py\`"" -WorkingDirectory "{REPO_PATH}"; '
                f'$trigger = New-ScheduledTaskTrigger -Daily -At "12:00"; '
                f'$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries; '
                f'Register-ScheduledTask -TaskName "{TASK_NAME}" -Action $action -Trigger $trigger -Settings $settings -Description "Daily GitHub contributions automation bot" -Force'
            )
            res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True)
            if res.returncode == 0:
                self.send_json({"success": True, "message": "Планировщик заданий Windows успешно активирован!"})
            else:
                self.send_json({"success": False, "message": res.stderr}, status=500)
        else:
            res = subprocess.run(["schtasks", "/delete", "/tn", TASK_NAME, "/f"], capture_output=True, text=True)
            self.send_json({"success": True, "message": "Планировщик заданий Windows отключен."})

    def handle_toggle_autostart(self, payload):
        enabled = payload.get("enabled", True)
        startup_file = get_startup_path()
        if enabled:
            try:
                pyw = get_pythonw_path()
                bat_content = f'@echo off\ncd /d "{REPO_PATH}"\nstart "" "{pyw}" activity_bot.py\n'
                with open(startup_file, "w", encoding="utf-8") as f:
                    f.write(bat_content)
                self.send_json({"success": True, "message": "Автозагрузка Windows активирована!"})
            except Exception as e:
                self.send_json({"success": False, "message": str(e)}, status=500)
        else:
            if os.path.exists(startup_file):
                try:
                    os.remove(startup_file)
                except Exception:
                    pass
            self.send_json({"success": True, "message": "Автозагрузка Windows отключена."})

    def handle_open_repos(self):
        repos_dir = os.path.join(REPO_PATH, "repos")
        if not os.path.exists(repos_dir):
            os.makedirs(repos_dir, exist_ok=True)
        try:
            os.startfile(repos_dir)
            self.send_json({"success": True})
        except Exception as e:
            self.send_json({"success": False, "error": str(e)}, status=500)

def run_server():
    server = socketserver.TCPServer(("127.0.0.1", PORT), DashboardHandler)
    url = f"http://127.0.0.1:{PORT}"
    print(f"=== AutoCommit Pro Web Dashboard ===")
    print(f"Server running at: {url}")
    print("Opening browser...")
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        server.server_close()

if __name__ == "__main__":
    run_server()

# todo: review edge cases
