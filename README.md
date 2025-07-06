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

Create a `.env` file in the src folder with your Meroshare credentials:

```
MEROSHARE_USERNAME=your_username
MEROSHARE_PASSWORD=your_password
MEROSHARE_DP_ID=your_dp_id
MEROSHARE_CRN=your_crn_number
MEROSHARE_TRANSACTIONPIN=your_transaction_pin
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
--check-only       Only check available IPOs without applying
--apply-all        Apply for all available IPOs
```

### Example Commands

```bash
# Check available IPOs
python src/main.py --check-only

# Apply for all available IPOs
python src/main.py --apply-all

```

## Project Structure

```
automate-meroshare-ipo/
├── src/                # Source code
│   ├── main.py         # Entry point
│   ├── meroshare/      # Meroshare API interactions
│   ├── models/         # Data models
│   └── utils/          # Utility functions
├── tests/              # Test files
├── venv/               # Virtual environment (not tracked in git)
├── .env                # Environment variables (not tracked in git)
├── .gitignore          # Git ignore file
├── requirements.txt    # Project dependencies
└── README.md           # This file
```

## Automate in linux OS

Create a bash script command to run the program

- Create /scripts in root folder of your device
- create ipo_script.sh
- add code similar to below to start

```
#!/bin/bash

# Wait for network connectivity before proceeding
max_retries=24 # wait up to 1 minute (12*5s)
count=0

until ping -c1 google.com &>/dev/null; do
  if [ $count -ge $max_retries ]; then
    echo "Network not available after waiting, exiting."
    exit 1
  fi
  echo "Waiting for network to be available..."
  sleep 5
  ((count++))
done

# Run your Python script
PYTHON_SCRIPT="path to your main.py"

if [ -f "$PYTHON_SCRIPT" ]; then
  echo "Waiting 10 sec"
  sleep 10
  echo "Running Python script: $PYTHON_SCRIPT"
  python3 "$PYTHON_SCRIPT" --apply-all
else
  echo "Error: Python script not found at $PYTHON_SCRIPT"
  exit 1
fi

```

## To setup at autostart on bootup

Inorder to setup auto start on laptop:

- create a file .desktop(eg: ipo_autostart.desktop) on /.config/autostart
- Add below code at this file

```

[Desktop Entry]
Type=Application
Exec=sh -c 'sleep 30 && (path to ipo_script) >> /tmp/ipo_autorun.log 2>&1'
Hidden=false
NoDisplay=false
X-GNOME-Autostart-enabled=true
Name=IPO Script
Comment=Apply for IPO after login

```

## To see log

To get log easily:

- Add alias to see the /tmp/ipo_autorun.log

```
alias ipoinfo='ls -l /tmp | grep ipo && cat /tmp/ipo_autorun.log'
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for educational purposes only. Use it at your own risk. The author is not responsible for any consequences of using this tool.
