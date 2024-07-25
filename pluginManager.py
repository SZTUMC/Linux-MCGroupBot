import pkgutil
import plugins
import time
import notice

class PluginsManager:
    """
    插件管理者
    """
    plugin_count: int = 0
    invail_count: int = 0
    all_plugins: list = []

    def __init__(self):
        self.plugin_count = 0
        self.invail_count = 0

        # 加载插件目录所有合法插件
        for _, plg, _ in pkgutil.iter_modules(plugins.__path__):
            try:
                plugin = getattr(__import__( 'plugins.' + plg), plg)
                self.all_plugins.append(plugin)
                self.plugin_count += 1
                ...
            except AttributeError as e:
                self.invail_count += 1
                print("faild to load " + plg + ":" + str(e))

        notice.send_test_msg(f"{self.plugin_count}个合法插件已加载,\
            {self.invail_count}个插件加载失败，请检查后台日志")

    def run(self, content: str):
        """
        在主程序被调用
        """
        for plugin in self.all_plugins:
            quick_answer = plugin.quick_answer(content)
            if quick_answer:
                print(quick_answer)

            if content[0] == '/' and len(content.split(' ')) > 1:
                command, args = content[1:].split(' ')
                if plugin.onCommand(command, args):
                    command_return = plugin.command_run(command, args)
                    print(command_return)

                localTime = time.localtime(time.time())
                if plugin.onScheduled(localTime):
                    scheduled_return = plugin.scheduled_run(localTime)
                    print(scheduled_return)

                plugin.run()

    def load_plugin(self, name: str):
        pass


    def unload_plugin(self, name: str):
        pass


