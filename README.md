# Automate Meroshare IPO

A Python application to automate Meroshare IPO (Initial Public Offering) application processes in Nepal's capital market.

## Project Overview

This project aims to automate the process of applying for IPOs through the Meroshare platform. It handles:

- Logging into your Meroshare account
- Checking available IPOs
- Automatically applying for new IPOs

## Requirements

- Python 3.10+
- Pip package manager

## Setup Instructions

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/automate-meroshare-ipo.git
cd automate-meroshare-ipo
```

### 2. Set Up Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/macOS
source venv/bin/activate
# On Windows
# venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configuration

This tool supports one or more Meroshare accounts (e.g. yours plus family members'),
configured via a single JSON file.

1. Copy the example file:

   ```bash
   cp src/accounts.example.json src/accounts.json
   ```

2. Edit `src/accounts.json` and fill in your real credentials for each account you
   want to automate. Each entry needs:

   | Field              | Description                                          |
   | ------------------ | ----------------------------------------------------- |
   | `name`             | Any label you choose (used in logs and `--account`)   |
   | `username`         | Meroshare username                                     |
   | `password`         | Meroshare password                                     |
   | `dp_id`            | DP ID number                                           |
   | `crn`              | Customer Reference Number                               |
   | `transaction_pin`  | Transaction PIN                                         |

   These extra fields are optional — leave them out unless you need them:

   | Field           | Description                                                        |
   | --------------- | ------------------------------------------------------------------ |
   | `bank`          | Bank to apply through, by name (e.g. `"Global IME"`). Only needed if several banks are linked to the demat account; otherwise the linked one is used. |
   | `bank_account`  | Account number to apply with. Only needed if the chosen bank has more than one. |
   | `applied_kitta` | Units to apply for (default `"10"`)                                 |

3. Restrict file permissions so only you can read it:

   ```bash
   chmod 600 src/accounts.json
   ```

4. **Never commit, share, or sync `src/accounts.json`** — it holds plaintext
   credentials and transaction PINs for your demat accounts. It's already listed in
   `.gitignore`, so `git status` should never show it as a trackable file.

Example `src/accounts.json` with two accounts:

```json
[
  {
    "name": "primary",
    "username": "your_username",
    "password": "your_password",
    "dp_id": "your_dp_id",
    "crn": "your_crn_number",
    "transaction_pin": "your_transaction_pin"
  },
  {
    "name": "spouse",
    "username": "...",
    "password": "...",
    "dp_id": "...",
    "crn": "...",
    "transaction_pin": "..."
  }
]
```

## Usage

### Basic Usage

```bash
# Activate the virtual environment if not already activated
source venv/bin/activate

# Run the application
python src/main.py
```

### Command Line Arguments

```
--check-only            Only check available IPOs without applying
--apply-all             Apply for all available IPOs
--apply NAME            Apply for a specific IPO by name
--headless              Run browser in headless mode
--dry-run               Fill in the application form but stop before submitting,
                        saving a screenshot of it (apply_form_dryrun_NAME.png)
--pace N                Multiplier on the pause between each step (default: 1.0).
                        Raise it to move more slowly, or pass 0 to remove the
                        pauses entirely
--account NAME          Limit the run to a single named account from accounts.json
                        (default: run every account in the file)
--accounts-file PATH    Use a non-default accounts.json path
```

Every action (`--check-only`, `--apply-all`, `--apply`) runs once per account in
`accounts.json`, in order, and a run summary is printed at the end. One account
failing doesn't stop the others from being processed.

The run is deliberately paced: each step waits a randomised beat and each field is
typed a character at a time, so the session looks like someone using the site
rather than a script filling a form in one burst. A full application therefore
takes a minute or so per account. `--pace 0` removes the pauses if you need speed
and accept looking automated; `--pace 2` slows everything to twice the delay.

### Example Commands

```bash
# Check available IPOs for every configured account
python src/main.py --check-only --headless

# Apply for all available IPOs, across every configured account
python src/main.py --apply-all --headless

# Debug/test a single account by name, without touching the others
python src/main.py --account primary --check-only

# Apply for one specific IPO, across every configured account
python src/main.py --apply "ABC Bank Limited" --headless

# Check the form fills in correctly without actually submitting an application
python src/main.py --account primary --apply-all --dry-run
```

## Project Structure

```
automate-meroshare-ipo/
├── src/                        # Source code
│   ├── main.py                 # Entry point, loops over configured accounts
│   ├── accounts.json           # Your real credentials (gitignored, not tracked)
│   ├── accounts.example.json   # Template for accounts.json (tracked)
│   ├── meroshare/               # Meroshare API interactions
│   ├── models/
│   │   └── account.py           # Account dataclass + accounts.json loader
│   └── utils/                   # Utility functions
├── tests/                      # Test files
├── venv/                       # Virtual environment (not tracked in git)
├── .gitignore                  # Git ignore file
├── requirements.txt            # Project dependencies
└── README.md                   # This file
```

## Scheduling / Automation

To fully automate this, schedule `python src/main.py --apply-all --headless` to run
periodically (or at login/boot). Every run loops through **all accounts** configured
in `src/accounts.json`, so setting this up once covers every account you've added.
Guides for macOS, Linux, and Windows are below.

All three examples use a small wrapper script that waits for network connectivity
before running the Python script (useful right after boot/login/wake, when the
network may not be up yet) and logs output to a file so you can check what happened.

### macOS (launchd)

1. Create a wrapper script, e.g. `~/scripts/run_ipo.sh`:

   ```bash
   #!/bin/bash
   LOG="/tmp/ipo_autorun.log"
   REPO="/path/to/ipo_automate"

   echo "===== IPO run started: $(date) =====" >> "$LOG"

   max_retries=24
   count=0
   until ping -c1 google.com &>/dev/null; do
     if [ $count -ge $max_retries ]; then
       echo "Network unavailable, exiting." >> "$LOG"
       exit 1
     fi
     echo "Waiting for network..." >> "$LOG"
     sleep 5
     ((count++))
   done

   cd "$REPO" && "$REPO/venv/bin/python" src/main.py --apply-all --headless >> "$LOG" 2>&1
   echo "===== IPO run finished: $(date) =====" >> "$LOG"
   ```

   ```bash
   chmod +x ~/scripts/run_ipo.sh
   ```

2. Create a launchd agent at `~/Library/LaunchAgents/com.yourname.ipo.plist`:

   ```xml
   <?xml version="1.0" encoding="UTF-8"?>
   <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
   <plist version="1.0">
   <dict>
     <key>Label</key><string>com.yourname.ipo</string>
     <key>ProgramArguments</key>
     <array>
       <string>/bin/bash</string>
       <string>/Users/yourname/scripts/run_ipo.sh</string>
     </array>
     <key>StartCalendarInterval</key>
     <dict>
       <key>Hour</key><integer>10</integer>
       <key>Minute</key><integer>5</integer>
     </dict>
     <key>RunAtLoad</key><false/>
     <key>StandardOutPath</key><string>/tmp/ipo_autorun.log</string>
     <key>StandardErrorPath</key><string>/tmp/ipo_autorun.log</string>
   </dict>
   </plist>
   ```

   Adjust `Hour`/`Minute` to when you want the daily run to trigger.

3. Load (enable) or unload (disable) the job:

   ```bash
   launchctl load ~/Library/LaunchAgents/com.yourname.ipo.plist
   launchctl unload ~/Library/LaunchAgents/com.yourname.ipo.plist
   ```

   Optional: prefix `ProgramArguments` with `/usr/bin/caffeinate -i -s` (before
   `/bin/bash`) to prevent the Mac from sleeping during the run.

### Linux (cron)

Runs on schedule even without a logged-in desktop session:

```bash
crontab -e
```

```
# Run daily at 10:05
5 10 * * * /path/to/ipo_automate/venv/bin/python /path/to/ipo_automate/src/main.py --apply-all --headless >> /tmp/ipo_autorun.log 2>&1
```

### Linux (autostart on login, desktop environments)

Create `~/.config/autostart/ipo_autostart.desktop`:

```ini
[Desktop Entry]
Type=Application
Exec=sh -c 'sleep 30 && /path/to/run_ipo.sh >> /tmp/ipo_autorun.log 2>&1'
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=IPO Script
Comment=Apply for IPO after login
```

(`run_ipo.sh` here can be the same wrapper script shown in the macOS section, minus
launchd specifics — it works the same way on Linux.)

### Windows (Task Scheduler)

1. Create `run_ipo.ps1` in the repo folder:

   ```powershell
   $log = "$env:TEMP\ipo_autorun.log"
   Add-Content $log "===== IPO run started: $(Get-Date) ====="

   $maxRetries = 24
   $count = 0
   while (-not (Test-Connection -ComputerName google.com -Count 1 -Quiet)) {
     if ($count -ge $maxRetries) {
       Add-Content $log "Network unavailable, exiting."
       exit 1
     }
     Start-Sleep -Seconds 5
     $count++
   }

   Set-Location "C:\path\to\ipo_automate"
   & ".\venv\Scripts\python.exe" "src\main.py" --apply-all --headless *>> $log
   Add-Content $log "===== IPO run finished: $(Get-Date) ====="
   ```

2. Register a scheduled task (run PowerShell as Administrator):

   ```powershell
   schtasks /create /tn "IPO Automate" /tr "powershell.exe -ExecutionPolicy Bypass -File C:\path\to\ipo_automate\run_ipo.ps1" /sc onlogon /rl highest
   ```

   Or via the GUI: open **Task Scheduler** → **Create Task** → General tab: name it
   "IPO Automate" → Triggers tab: New → "At log on" → Actions tab: New → Program/script
   `powershell.exe`, arguments `-ExecutionPolicy Bypass -File C:\path\to\ipo_automate\run_ipo.ps1`.

### To see the log

```bash
# macOS / Linux
cat /tmp/ipo_autorun.log

# Windows (PowerShell)
Get-Content "$env:TEMP\ipo_autorun.log"
```

Add an alias for convenience (macOS/Linux):

```bash
alias ipoinfo='cat /tmp/ipo_autorun.log'
```

### Docker (optional)

It's possible to containerize this tool for stronger process isolation, but a
Dockerfile isn't provided or tested in this repo — multi-account support doesn't
require it, since each Selenium session already runs with its own isolated temporary
Chrome profile per account/run. If you want to containerize it anyway, a minimal
image would need Python, Chrome/Chromium, and a matching chromedriver, and you'd
mount `src/accounts.json` in as a read-only volume rather than baking it into the
image.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for educational purposes only. Use it at your own risk. The author is not responsible for any consequences of using this tool.
