import threading
import config
import time
import services
from notice import send_test_msg
from scheduled import ScheduledArea
from pluginManager import PluginsManager


def main():
    target_interval = 100 # ms

    scheduler = ScheduledArea()
    plugins_manager = PluginsManager()

    while True:

        start_of_loop = time.perf_counter() * 1000

        # 耗时函数
        scheduler.scheduled_run()
        if len(services.global_msgpkg) > 0:
            name, content, is_in_room = services.global_msgpkg[-1]
            plugins_manager.run(content)
            services.global_msgpkg.pop()

        end_of_loop = time.perf_counter() * 1000
        elapsed_time = end_of_loop - start_of_loop

        if elapsed_time < target_interval:
            time.sleep((target_interval - elapsed_time) / 1000)

if __name__ == "__main__":

    main_loop_thread = threading.Thread(target=main, daemon=True)
    main_loop_thread.start()
    send_test_msg(f"{config.LANUCH_TIME}: Bot已重启")
    services.app.run(host='0.0.0.0', port=4994)
