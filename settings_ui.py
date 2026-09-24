import tkinter as tk
from tkinter import messagebox, ttk
import json
import os
import sys
import subprocess
import random

REPO_PATH = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(REPO_PATH, "config.json")
STATE_FILE = os.path.join(REPO_PATH, "bot_state.json")
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

def toggle_autostart():
    startup_file = get_startup_path()
    if var_autostart.get():
        try:
            pyw = get_pythonw_path()
            bat_content = f'@echo off\ncd /d "{REPO_PATH}"\nstart "" "{pyw}" activity_bot.py\n'
            with open(startup_file, "w", encoding="utf-8") as f:
                f.write(bat_content)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to enable autostart:\n{e}")
            var_autostart.set(False)
    else:
        if os.path.exists(startup_file):
            try:
                os.remove(startup_file)
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
                messagebox.showinfo("Успех", "Задача создана в Планировщике (ежедневно в 12:00, тихо в фоне)!")
            else:
                messagebox.showerror("Ошибка", f"Не удалось создать задачу:\n{res.stderr}")
                var_scheduler.set(False)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка: {e}")
            var_scheduler.set(False)
    else:
        try:
            subprocess.run(["schtasks", "/delete", "/tn", TASK_NAME, "/f"], capture_output=True, text=True)
            messagebox.showinfo("Успех", "Задача удалена из Планировщика.")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось удалить задачу:\n{e}")
            var_scheduler.set(True)

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_state(state):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=4)
    except Exception as e:
        print("Save state error:", e)

def save_config():
    try:
        cfg = load_config()
        cfg["normal_day"]["min_commits"] = int(entry_norm_min.get())
        cfg["normal_day"]["max_commits"] = int(entry_norm_max.get())
        cfg["special_day"]["min_commits"] = int(entry_spec_min.get())
        cfg["special_day"]["max_commits"] = int(entry_spec_max.get())
        cfg["marathons"]["trio_3_days"]["min_commits"] = int(entry_mar_min.get())
        cfg["marathons"]["trio_3_days"]["max_commits"] = int(entry_mar_max.get())
        cfg["marathons"]["week_7_days"]["min_commits"] = int(entry_mar_min.get())
        cfg["marathons"]["week_7_days"]["max_commits"] = int(entry_mar_max.get())

        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4)
            
        messagebox.showinfo("Успех", "Настройки успешно сохранены!")
    except ValueError:
        messagebox.showerror("Ошибка", "Пожалуйста, введите корректные числа.")

def run_bot_now():
    btn_run.config(state="disabled", text="Выполняется...")
    root.update()
    try:
        res = subprocess.run([sys.executable, os.path.join(REPO_PATH, "activity_bot.py"), "--force"],
                             cwd=REPO_PATH, capture_output=True, text=True)
        refresh_status()
        if res.returncode == 0:
            messagebox.showinfo("Успешно!", f"Бот завершил работу!\n\nЛог:\n{res.stdout[-600:]}")
        else:
            messagebox.showerror("Ошибка", f"Ошибка при запуске бота:\n{res.stderr or res.stdout}")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось запустить бота:\n{e}")
    finally:
        btn_run.config(state="normal", text="▶ Запустить бота сейчас (--force)")

def start_manual_marathon(days):
    cfg = load_config()
    repos = [r for r in cfg.get("repositories", []) if os.path.exists(r)]
    if not repos:
        repos = [REPO_PATH]
    assigned = random.sample(repos, min(2, len(repos)))
    
    state = load_state()
    state["marathon"] = {
        "active": True,
        "type": f"{days}-day sprint",
        "days_left": days,
        "total_days": days,
        "target_range": [10, 59],
        "assigned_repos": assigned
    }
    # Reset today state so it executes with marathon today
    state["today_status"] = "in_progress"
    save_state(state)
    refresh_status()
    names = ", ".join([os.path.basename(r) for r in assigned])
    messagebox.showinfo("Марафон запущен!", f"Спринт на {days} дней активирован!\nФокус на репозиториях: {names}\nДиапазон: 10-59 пушей/день.")

def open_log():
    if os.path.exists(LOG_FILE):
        os.startfile(LOG_FILE)
    else:
        messagebox.showinfo("Инфо", "Файл лога еще не создан.")

def open_repos_folder():
    rf = os.path.join(REPO_PATH, "repos")
    if not os.path.exists(rf):
        os.makedirs(rf, exist_ok=True)
    os.startfile(rf)

def refresh_status():
    st = load_state()
    done = st.get("today_completed_commits", 0)
    target = st.get("today_target_commits", 0)
    status = st.get("today_status", "none")
    day_type = st.get("today_day_type", "Обычный")
    date = st.get("last_run_date", "-")

    m = st.get("marathon", {})
    if m.get("active") and m.get("days_left", 0) > 0:
        repos_str = ", ".join([os.path.basename(r) for r in m.get("assigned_repos", [])])
        m_text = f"🔥 Активен: {m.get('type')} (осталось дней: {m.get('days_left')})\nРепозитории: {repos_str}"
        lbl_marathon_info.config(text=m_text, fg="#cf222e")
    else:
        lbl_marathon_info.config(text="Марафон не активен (обычный режим)", fg="#57606a")

    status_str = f"Дата: {date} | Статус: {status}\nРежим: {day_type}\nСделано сегодня: {done} / {target} коммитов"
    lbl_today_status.config(text=status_str)

# UI Setup
root = tk.Tk()
root.title("Auto Daily Contributions v2.0 - Dashboard")
root.geometry("490x650")
root.resizable(False, False)

font_main = ("Segoe UI", 9)
font_bold = ("Segoe UI", 9, "bold")
font_title = ("Segoe UI", 12, "bold")
bg_color = "#f6f8fa"
root.configure(bg=bg_color)

# Header
tk.Label(root, text="⚡ Auto Daily Contributions", font=font_title, bg=bg_color).pack(pady=(10, 4))

# Status Box
box_status = tk.LabelFrame(root, text=" Текущий статус бота ", font=font_bold, bg=bg_color, padx=10, pady=8)
box_status.pack(fill="x", padx=15, pady=5)

lbl_today_status = tk.Label(box_status, text="", font=font_main, bg=bg_color, justify="left")
lbl_today_status.pack(anchor="w")

lbl_marathon_info = tk.Label(box_status, text="", font=font_bold, bg=bg_color, justify="left")
lbl_marathon_info.pack(anchor="w", pady=(4, 0))

# Config Box
box_cfg = tk.LabelFrame(root, text=" Настройки количества пушей / коммитов ", font=font_bold, bg=bg_color, padx=10, pady=8)
box_cfg.pack(fill="x", padx=15, pady=5)

cfg = load_config()

# Normal days
f_norm = tk.Frame(box_cfg, bg=bg_color)
f_norm.pack(fill="x", pady=2)
tk.Label(f_norm, text="Обычный день:", width=18, anchor="w", font=font_main, bg=bg_color).pack(side="left")
entry_norm_min = tk.Entry(f_norm, width=5, font=font_main)
entry_norm_min.pack(side="left", padx=2)
tk.Label(f_norm, text="—", bg=bg_color).pack(side="left")
entry_norm_max = tk.Entry(f_norm, width=5, font=font_main)
entry_norm_max.pack(side="left", padx=2)
tk.Label(f_norm, text="коммитов", bg=bg_color, font=font_main).pack(side="left", padx=4)

# Special day
f_spec = tk.Frame(box_cfg, bg=bg_color)
f_spec.pack(fill="x", pady=2)
tk.Label(f_spec, text="Особый день (Spike):", width=18, anchor="w", font=font_main, bg=bg_color).pack(side="left")
entry_spec_min = tk.Entry(f_spec, width=5, font=font_main)
entry_spec_min.pack(side="left", padx=2)
tk.Label(f_spec, text="—", bg=bg_color).pack(side="left")
entry_spec_max = tk.Entry(f_spec, width=5, font=font_main)
entry_spec_max.pack(side="left", padx=2)
tk.Label(f_spec, text="коммитов (15% шанс)", bg=bg_color, font=font_main).pack(side="left", padx=4)

# Marathon
f_mar = tk.Frame(box_cfg, bg=bg_color)
f_mar.pack(fill="x", pady=2)
tk.Label(f_mar, text="Марафон (3 или 7 дней):", width=18, anchor="w", font=font_main, bg=bg_color).pack(side="left")
entry_mar_min = tk.Entry(f_mar, width=5, font=font_main)
entry_mar_min.pack(side="left", padx=2)
tk.Label(f_mar, text="—", bg=bg_color).pack(side="left")
entry_mar_max = tk.Entry(f_mar, width=5, font=font_main)
entry_mar_max.pack(side="left", padx=2)
tk.Label(f_mar, text="коммитов/день", bg=bg_color, font=font_main).pack(side="left", padx=4)

entry_norm_min.insert(0, str(cfg.get("normal_day", {}).get("min_commits", 1)))
entry_norm_max.insert(0, str(cfg.get("normal_day", {}).get("max_commits", 6)))
entry_spec_min.insert(0, str(cfg.get("special_day", {}).get("min_commits", 12)))
entry_spec_max.insert(0, str(cfg.get("special_day", {}).get("max_commits", 48)))
entry_mar_min.insert(0, str(cfg.get("marathons", {}).get("trio_3_days", {}).get("min_commits", 10)))
entry_mar_max.insert(0, str(cfg.get("marathons", {}).get("trio_3_days", {}).get("max_commits", 59)))

tk.Button(box_cfg, text="💾 Сохранить настройки", command=save_config, font=font_main, bg="#2ea44f", fg="white", relief="flat").pack(pady=(6, 2))

# Schedule Box
box_sched = tk.LabelFrame(root, text=" Автозапуск (Защита от перезагрузок активна) ", font=font_bold, bg=bg_color, padx=10, pady=6)
box_sched.pack(fill="x", padx=15, pady=5)

var_scheduler = tk.BooleanVar(value=is_scheduler_enabled())
chk_sched = tk.Checkbutton(box_sched, text="Планировщик Windows (ежедневно в 12:00 в фоне)", 
                           variable=var_scheduler, command=toggle_scheduler,
                           bg=bg_color, font=font_main)
chk_sched.pack(anchor="w")

var_autostart = tk.BooleanVar(value=is_autostart_enabled())
chk_autostart = tk.Checkbutton(box_sched, text="Автозагрузка при старте ПК (Startup)", 
                               variable=var_autostart, command=toggle_autostart,
                               bg=bg_color, font=font_main)
chk_autostart.pack(anchor="w")

# Actions Box
box_actions = tk.LabelFrame(root, text=" Управление и марафоны ", font=font_bold, bg=bg_color, padx=10, pady=8)
box_actions.pack(fill="x", padx=15, pady=5)

btn_run = tk.Button(box_actions, text="▶ Запустить бота сейчас (--force)", command=run_bot_now, font=font_bold, bg="#0969da", fg="white", relief="flat", height=1)
btn_run.pack(fill="x", pady=3)

f_sprints = tk.Frame(box_actions, bg=bg_color)
f_sprints.pack(fill="x", pady=3)
tk.Button(f_sprints, text="🔥 Троица дней (3 дня)", command=lambda: start_manual_marathon(3), font=font_main, bg="#bf8700", fg="white", relief="flat").pack(side="left", expand=True, fill="x", padx=2)
tk.Button(f_sprints, text="🚀 Особая неделя (7 дней)", command=lambda: start_manual_marathon(7), font=font_main, bg="#8250df", fg="white", relief="flat").pack(side="left", expand=True, fill="x", padx=2)

f_aux = tk.Frame(box_actions, bg=bg_color)
f_aux.pack(fill="x", pady=3)
tk.Button(f_aux, text="📁 Папка с репозиториями", command=open_repos_folder, font=font_main, bg="#eaeef2", fg="#24292f", relief="flat").pack(side="left", expand=True, fill="x", padx=2)
tk.Button(f_aux, text="📋 Открыть лог", command=open_log, font=font_main, bg="#eaeef2", fg="#24292f", relief="flat").pack(side="left", expand=True, fill="x", padx=2)

refresh_status()
root.mainloop()
