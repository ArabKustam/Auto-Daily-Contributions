import tkinter as tk
from tkinter import messagebox
import json
import os
import sys
import getpass

CONFIG_FILE = "config.json"
REPO_PATH = os.path.dirname(os.path.abspath(__file__))

def get_startup_path():
    return os.path.join(
        "C:\\Users",
        getpass.getuser(),
        "AppData\\Roaming\\Microsoft\\Windows\\Start Menu\\Programs\\Startup",
        "AutoDailyContributions.bat"
    )

def is_autostart_enabled():
    return os.path.exists(get_startup_path())

def toggle_autostart():
    startup_file = get_startup_path()
    if var_autostart.get():
        # Enable Autostart
        try:
            bat_content = f'@echo off\ncd /d "{REPO_PATH}"\npython activity_bot.py\n'
            with open(startup_file, "w") as f:
                f.write(bat_content)
            print(f"Created startup file: {startup_file}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to enable autostart:\n{e}")
            var_autostart.set(False)
    else:
        # Disable Autostart
        if os.path.exists(startup_file):
            try:
                os.remove(startup_file)
                print("Removed startup file")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to disable autostart:\n{e}")
                var_autostart.set(True)

def load_config():
    if not os.path.exists(os.path.join(REPO_PATH, CONFIG_FILE)):
        return {"min_commits": 1, "max_commits": 5}
    try:
        with open(os.path.join(REPO_PATH, CONFIG_FILE), "r") as f:
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
        with open(os.path.join(REPO_PATH, CONFIG_FILE), "w") as f:
            json.dump(config, f, indent=4)
            
        # Also handle autostart toggle which is bound to the checkbox, 
        # but good to confirm visual feedback
        messagebox.showinfo("Success", "Settings saved successfully!")
    except ValueError:
        messagebox.showerror("Error", "Please enter valid numbers")

# UI Setup
root = tk.Tk()
root.title("Auto Contributions Settings")
root.geometry("350x250")
root.resizable(False, False)

# Styling
font_style = ("Segoe UI", 10)
bg_color = "#f0f0f0"
root.configure(bg=bg_color)

# Header
tk.Label(root, text="Bot Settings", font=("Segoe UI", 14, "bold"), bg=bg_color).pack(pady=10)

# Input Frame
frame = tk.Frame(root, bg=bg_color)
frame.pack(pady=10)

# Min Commits
tk.Label(frame, text="Min Commits:", font=font_style, bg=bg_color).grid(row=0, column=0, padx=5, pady=5)
entry_min = tk.Entry(frame, width=10, font=font_style)
entry_min.grid(row=0, column=1, padx=5, pady=5)

# Max Commits
tk.Label(frame, text="Max Commits:", font=font_style, bg=bg_color).grid(row=1, column=0, padx=5, pady=5)
entry_max = tk.Entry(frame, width=10, font=font_style)
entry_max.grid(row=1, column=1, padx=5, pady=5)

# Load current values
current_config = load_config()
entry_min.insert(0, str(current_config.get("min_commits", 1)))
entry_max.insert(0, str(current_config.get("max_commits", 5)))

# Autostart Checkbox
var_autostart = tk.BooleanVar(value=is_autostart_enabled())
chk_autostart = tk.Checkbutton(root, text="Run automatically at Windows startup", 
                               variable=var_autostart, command=toggle_autostart,
                               bg=bg_color, font=font_style)
chk_autostart.pack(pady=10)

# Save Button
tk.Button(root, text="Save Settings", command=save_config, font=font_style, bg="#4CAF50", fg="white", width=15).pack(pady=10)

root.mainloop()
