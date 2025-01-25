# MohawkCourseBot 🚨

Automated course registration monitor for Mohawk College with real-time Telegram alerts and 2FA login handling.

![Python](https://img.shields.io/badge/python-3.8%2B-blue)
![Selenium](https://img.shields.io/badge/selenium-4.27-green)
![Telegram](https://img.shields.io/badge/telegram-bot-orange)

## Features ✨
- Real-time course availability monitoring
- Instant Telegram notifications for status changes
- Automated 2FA login handling using Selenium
- Retry mechanism for robust operation
- Cross-campus course tracking (Fennell Campus + Online)
- Multiple course section monitoring

## Prerequisites 📋
- Python 3.8+
- Telegram bot token ([create one via @BotFather](https://core.telegram.org/bots#6-botfather))
- Mohawk College credentials with 2FA access
- ChromeDriver for your browser version

## Installation ⚙️
1. Clone the repository:
```bash
git clone https://github.com/yourusername/MohawkCourseBot.git
cd MohawkCourseBot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Install ChromeDriver:
- Download from [ChromeDriver website](https://chromedriver.chromium.org/)
- Add to system PATH or place in project directory

## Configuration 🔧
Create `.env` file in project root:
```env
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
MOHAWK_USERNAME=your_mohawk_username
MOHAWK_PASSWORD=your_mohawk_password
```

## Usage 🚦
```bash
python main.py
```

The bot will:
1. Authenticate using 2FA via Selenium
2. Continuously monitor course statuses
3. Send Telegram alerts for changes:
   - 🟢 Course available: "COMP 10279 - Advanced Database (CRN: 27446) is now Available!"
   - 🔴 Course full: "COMP 10073 - Android Applic Develop (CRN: 27346) is now Full!"
   - ℹ️ Status changes for registered courses

## Project Structure 📁
```
MohawkCourseBot/
├── src/
│   ├── monitor/              # Course monitoring logic
│   └── utils/                # Helper functions
│       └── telegram_utils.py # Notification system
├── .gitignore
├── course_states.json        # Course status database
├── main.py                   # Main application
├── README.md
└── requirements.txt          # Dependencies
```

## Key Dependencies 📦
- `selenium`: Browser automation for 2FA login
- `requests`: HTTP communication with Telegram API
- `python-dotenv`: Environment variable management


## License 📄
Distributed under the MIT License. See `LICENSE` for more information.

---

**Note:** This project is not officially affiliated with Mohawk College. Use responsibly and in compliance with institutional policies.
```
