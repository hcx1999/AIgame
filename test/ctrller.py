from god import GodAgent
import npc
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QThread, QEventLoop


class Controller(QObject):
    # 向界面发送剧情、角色、选项
    update_signal = pyqtSignal(str, object, list)
    # 向界面发送NPC行动
    NPC_signal = pyqtSignal(object)
    # 从界面接收玩家选择
    choice_signal = pyqtSignal(str)
    # 从界面接收游戏背景
    background_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.god = GodAgent()
        self.choice_signal.connect(self.handle_choice)
        self.background_signal.connect(self.receive_background)
        self.pending_choice = None
        self.waiting = False
        self.story_start = False

    def run(self):
        self.background_loop = QEventLoop()
        self.background_loop.exec_()
        while True:
            narrative, options, new_role = self.god.generate_narrative()
            self.update_signal.emit(narrative, new_role, options)

            # 等待玩家选择
            self.choice_loop = QEventLoop()
            self.choice_loop.exec_()  # 在这里阻塞，直到 handle_choice 调用 quit()

            player_choice = self.pending_choice
            self.pending_choice = None

            former_history = self.get_history()
            former_history += '玩家做了' + player_choice + '\n'

            npc_info = npc.interact((self.god.world_state['characters'], former_history))
            self.NPC_signal.emit(npc_info)
            info = (player_choice, npc_info)
            self.god.update_information(info)

    @pyqtSlot(str)
    def handle_choice(self, content):
        self.pending_choice = content
        if self.choice_loop is not None:
            self.choice_loop.quit()

    @pyqtSlot(str)
    def receive_background(self, background):
        print(background)
        self.god.update_world_state(background=background)
        self.story_start = True
        if self.background_loop is not None:
            self.background_loop.quit()

    def get_history(self):
        history = ""
        for event in self.god.world_state["history"]:
            if event['role'] == "系统":
                history += event['content'] + "\n"
            else:
                history += f"{event['role']} 做了: {event['content'].strip()}\n"
        return history
