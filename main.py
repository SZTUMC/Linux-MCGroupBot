import threading
from services import app, send_test_msg
from scheduled import ScheduledArea

if __name__ == "__main__":
    scheduler = ScheduledArea()
    scheduled_loop_thread = threading.Thread(target=scheduler.scheduled_loop, daemon=True)
    scheduled_loop_thread.start()
    send_test_msg("Bot已重启")
    app.run(host='0.0.0.0', port=4994)