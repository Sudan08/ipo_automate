# Automate Meroshare IPO

A Python application to automate Meroshare IPO (Initial Public Offering) application processes in Nepal's capital market.

## Project Overview

This project aims to automate the process of applying for IPOs through the Meroshare platform. It handles:

- Logging into your Meroshare account
- Checking available IPOs
- Automatically applying for new IPOs
- Tracking application status
- Notifying users about application results

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

Create a `.env` file in the project root with your Meroshare credentials:

```
MEROSHARE_USERNAME=your_username
MEROSHARE_PASSWORD=your_password
MEROSHARE_DP_ID=your_dp_id
MEROSHARE_CRN=your_customer_reference_number
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
--apply=IPO_NAME   Apply for a specific IPO by name
--headless         Run browser in headless mode
```

### Example Commands

```bash
# Check available IPOs
python src/main.py --check-only

# Apply for all available IPOs
python src/main.py --apply-all

# Apply for a specific IPO
python src/main.py --apply="Nepal Bank Limited"
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

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for educational purposes only. Use it at your own risk. The author is not responsible for any consequences of using this tool.

