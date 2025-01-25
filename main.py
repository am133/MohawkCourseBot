from src.monitor import RegistrationMonitor
from src.utils.telegram_utils import TelegramNotifier
import time


def main():
    monitor = None
    notifier = TelegramNotifier()
    max_retries = 3
    retry_count = 0

    try:
        while retry_count < max_retries:
            try:
                # Initialize monitor if not exists
                if not monitor:
                    monitor = RegistrationMonitor()

                # Start monitoring
                monitor.monitor_courses()
                break  # Exit loop if monitoring completes successfully

            except Exception as e:
                retry_count += 1
                print(f"Attempt {retry_count}/{max_retries} failed: {str(e)}")

                if retry_count < max_retries:
                    print("Retrying in 60 seconds...")
                    time.sleep(60)
                else:
                    print("Maximum retry attempts reached. Exiting...")
                    notifier.send_message("⚠️ Course monitor stopped after maximum retries")

                # Clean up failed monitor instance
                if monitor:
                    monitor.close()
                    monitor = None

    except KeyboardInterrupt:
        print("\nProgram terminated by user")
        notifier.send_message("ℹ️ Course monitor stopped by user")

    finally:
        if monitor:
            monitor.close()


if __name__ == "__main__":
    main()
