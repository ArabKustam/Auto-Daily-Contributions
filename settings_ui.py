import tkinter as tk
from tkinter import messagebox
import json
import os
import sys
import subprocess

CONFIG_FILE = "config.json"
REPO_PATH = os.path.dirname(os.path.abspath(__file__))
TASK_NAME = "AutoDailyContributions"

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

def toggle_autostart():
    startup_file = get_startup_path()
    if var_autostart.get():
        try:
            bat_content = f'@echo off\ncd /d "{REPO_PATH}"\nstart "" pythonw activity_bot.py\n'
            with open(startup_file, "w", encoding="utf-8") as f:
                f.write(bat_content)
            print(f"Created startup file: {startup_file}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to enable autostart:\n{e}")
            var_autostart.set(False)
    else:
        if os.path.exists(startup_file):
            try:
                os.remove(startup_file)
                print("Removed startup file")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to disable autostart:\n{e}")
                var_autostart.set(True)

def is_scheduler_enabled():
    try:
        res = subprocess.run(["schtasks", "/query", "/tn", TASK_NAME], capture_output=True, text=True)
        return res.returncode == 0
    except Exception:
        return False

def toggle_scheduler():
    if var_scheduler.get():
        try:
            ps_cmd = (
                f'$action = New-ScheduledTaskAction -Execute "pythonw.exe" '
                f'-Argument "\`"{REPO_PATH}\\activity_bot.py\`"" -WorkingDirectory "{REPO_PATH}"; '
                f'$trigger = New-ScheduledTaskTrigger -Daily -At "12:00"; '
                f'$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries; '
                f'Register-ScheduledTask -TaskName "{TASK_NAME}" -Action $action -Trigger $trigger -Settings $settings -Description "Daily GitHub contributions automation bot"'
            )
            res = subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, text=True)
            if res.returncode == 0:
                messagebox.showinfo("Success", "Daily Task Scheduler task created (runs at 12:00 daily)!")
            else:
                messagebox.showerror("Error", f"Failed to register task:\n{res.stderr}")
                var_scheduler.set(False)
        except Exception as e:
            messagebox.showerror("Error", f"Error setting scheduler:\n{e}")
            var_scheduler.set(False)
    else:
        try:
            subprocess.run(["schtasks", "/delete", "/tn", TASK_NAME, "/f"], capture_output=True, text=True)
            messagebox.showinfo("Success", "Scheduled task removed.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to remove task:\n{e}")
            var_scheduler.set(True)

def load_config():
    config_path = os.path.join(REPO_PATH, CONFIG_FILE)
    if not os.path.exists(config_path):
        return {"min_commits": 1, "max_commits": 5}
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"min_commits": 1, "max_commits": 5}

def save_config():
    try:
        min_c = int(entry_min.get())
        max_c = int(entry_max.get())
        
        if min_c < 1:
            messagebox.showerror("Error", "Minimum commits must be at least 1")
            return
        if max_c < min_c:
            messagebox.showerror("Error", "Maximum commits cannot be less than Minimum commits")
            return
            
        config = {"min_commits": min_c, "max_commits": max_c}
        with open(os.path.join(REPO_PATH, CONFIG_FILE), "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4)
            
        messagebox.showinfo("Success", "Settings saved successfully!")
    except ValueError:
        messagebox.showerror("Error", "Please enter valid numbers")

def run_bot_now():
    try:
        res = subprocess.run([sys.executable, os.path.join(REPO_PATH, "activity_bot.py"), "--force"],
                             cwd=REPO_PATH, capture_output=True, text=True)
        if res.returncode == 0:
            messagebox.showinfo("Success", f"Bot finished successfully!\n\nOutput:\n{res.stdout}")
        else:
            messagebox.showerror("Error", f"Bot encountered an error:\n{res.stderr or res.stdout}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to run bot:\n{e}")

def open_log():
    log_path = os.path.join(REPO_PATH, "activity.log")
    if os.path.exists(log_path):
        os.startfile(log_path)
    else:
        messagebox.showinfo("Info", "Log file does not exist yet. Run the bot first.")

# UI Setup
root = tk.Tk()
root.title("Auto Contributions Settings")
root.geometry("400x370")
root.resizable(False, False)

font_style = ("Segoe UI", 10)
bg_color = "#f4f6f9"
root.configure(bg=bg_color)

# Header
tk.Label(root, text="Auto Daily Contributions", font=("Segoe UI", 14, "bold"), bg=bg_color).pack(pady=(12, 5))

# Input Frame
frame = tk.Frame(root, bg=bg_color)
frame.pack(pady=5)

tk.Label(frame, text="Min Commits / day:", font=font_style, bg=bg_color).grid(row=0, column=0, padx=5, pady=4, sticky="e")
entry_min = tk.Entry(frame, width=8, font=font_style)
entry_min.grid(row=0, column=1, padx=5, pady=4)

tk.Label(frame, text="Max Commits / day:", font=font_style, bg=bg_color).grid(row=1, column=0, padx=5, pady=4, sticky="e")
entry_max = tk.Entry(frame, width=8, font=font_style)
entry_max.grid(row=1, column=1, padx=5, pady=4)

current_config = load_config()
entry_min.insert(0, str(current_config.get("min_commits", 1)))
entry_max.insert(0, str(current_config.get("max_commits", 5)))

# Options Frame
opt_frame = tk.Frame(root, bg=bg_color)
opt_frame.pack(pady=5)

var_scheduler = tk.BooleanVar(value=is_scheduler_enabled())
chk_sched = tk.Checkbutton(opt_frame, text="Windows Task Scheduler (Daily 12:00)", 
                           variable=var_scheduler, command=toggle_scheduler,
                           bg=bg_color, font=font_style)
chk_sched.pack(anchor="w", pady=2)

var_autostart = tk.BooleanVar(value=is_autostart_enabled())
chk_autostart = tk.Checkbutton(opt_frame, text="Windows Startup (at login)", 
                               variable=var_autostart, command=toggle_autostart,
                               bg=bg_color, font=font_style)
chk_autostart.pack(anchor="w", pady=2)

# Action Buttons Frame
btn_frame = tk.Frame(root, bg=bg_color)
btn_frame.pack(pady=10)

tk.Button(btn_frame, text="Save Settings", command=save_config, font=font_style, bg="#2ea44f", fg="white", width=14, relief="flat").grid(row=0, column=0, padx=5, pady=5)
tk.Button(btn_frame, text="Run Bot Now", command=run_bot_now, font=font_style, bg="#0969da", fg="white", width=14, relief="flat").grid(row=0, column=1, padx=5, pady=5)
tk.Button(btn_frame, text="View Logs", command=open_log, font=font_style, bg="#6e7781", fg="white", width=14, relief="flat").grid(row=1, column=0, columnspan=2, padx=5, pady=5)

root.mainloop()
