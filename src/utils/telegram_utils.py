import requests
import os

class TelegramNotifier:
    def __init__(self, token=None, chat_id=None):
        self.telegram_token = token or os.environ.get('TELEGRAM_TOKEN')
        self.telegram_chat_id = chat_id or os.environ.get('TELEGRAM_CHAT_ID')

    def send_message(self, message):
        """Send message via Telegram bot"""
        try:
            telegram_api_url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
            params = {
                "chat_id": self.telegram_chat_id,
                "text": message,
                "parse_mode": "HTML"
            }
            response = requests.post(telegram_api_url, params=params)
            if not response.json().get("ok"):
                print(f"Failed to send Telegram message: {response.json()}")
        except Exception as e:
            print(f"Error sending Telegram message: {str(e)}")

    def alert_changes(self, changes):
        """Alert user of any changes via console and Telegram"""
        if not changes:
            return

        print("\n=== Changes Detected! ===")
        telegram_message = "🔔 <b>Course Changes Detected!</b>\n\n"

        for change in changes:
            course_info = f"{change['subject']} {change['course_num']} - {change['title']}"

            # Console output
            print(f"\nCourse: {course_info}")
            print(f"Instructor: {change['instructor']}")
            print(f"CRN: {change['crn']}")
            print(f"Status Change: {change['old_status']} → {change['new_status']}")

            # Telegram message
            telegram_message += f"📚 <b>{course_info}</b>\n"
            telegram_message += f"Instructor: {change['instructor']}\n"
            telegram_message += f"CRN: {change['crn']}\n"
            telegram_message += f"Status: {change['old_status']} → {change['new_status']}\n\n"

            if change['new_status'] == 'Available' and change['old_status'] in ['Full', 'Closed', 'Not tracked']:
                print('\a')  # System beep
                telegram_message = "🚨 COURSE AVAILABLE! 🚨\n\n" + telegram_message

        self.send_message(telegram_message)


