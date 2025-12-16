# 🟩 GitHub Activity Bot

<div align="center">

![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![GitHub Actions](https://img.shields.io/badge/github%20actions-%232671E5.svg?style=for-the-badge&logo=githubactions&logoColor=white)
![License](https://img.shields.io/badge/license-MIT-green?style=for-the-badge)
![Year](https://img.shields.io/badge/Year-2025-blue?style=for-the-badge)

**Automated Contribution & Activity Manager**  
*Developed by [ArabKustam](https://github.com/ArabKustam)*

</div>

---

## 📝 Overview

**GitHub Activity Bot** is a lightweight, automated tool designed to keep your GitHub profile active. It performs daily scheduled commits to ensure your contribution graph remains green and healthy, solving the issue of gaps in your activity history.

Built for simplicity and reliability, this tool leverages **GitHub Actions** to run completely in the cloud—no local server required.

## ✨ Features

- **🚀 Fully Automated**: runs on a scheduled cron job (every day at 02:30 UTC).
- **☁️ Cloud Native**: utilizes GitHub Actions for 24/7 uptime without local resources.
- **⚡ Lightweight**: Written in pure Python with zero external dependencies.
- **🔒 Secure & Private**: All activity data is contained within the repository.
- **📅 consistent**: Ensures a minimum of one commit per day.

## 🛠️ Requirements

To run this project, you only need:

*   **GitHub Account**
*   **Git** (for initial setup)

*Note: No `pip install` required as the script uses standard Python libraries.*

## 🚀 Installation & Setup

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/ArabKustam/your-repo-name.git
    cd your-repo-name
    ```

2.  **Enable Actions**
    *   Go to your repository **Settings** > **Actions** > **General**.
    *   Under **Workflow permissions**, select **Read and write permissions**.
    *   Click **Save**.

3.  **Push to GitHub**
    ```bash
    git add .
    git commit -m "Initial setup by ArabKustam"
    git push origin main
    ```

## 💻 Manual Usage

You can also run the bot locally if needed:

**Windows**:
Double-click `run_bot.bat`

**Terminal**:
```bash
python activity_bot.py
```

## ⚙️ Configuration

The automation schedule is defined in `.github/workflows/daily_contribution.yml`.
To change the time, edit the cron schedule:

```yaml
on:
  schedule:
    - cron: '30 2 * * *' # Formatted as: Minute Hour Day Month DayOfWeek
```

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---
<div align="center">
    <b>© 2025 ArabKustam. All rights reserved.</b>
</div>
