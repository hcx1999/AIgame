from god import GodAgent
import npc
from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, QThread, QEventLoop
import logging
from dotenv import load_dotenv
load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


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
        try:
            super().__init__()
            self.god = GodAgent()
            self.choice_signal.connect(self.handle_choice)
            self.background_signal.connect(self.receive_background)
            self.pending_choice = None
            self.waiting = False
            self.story_start = False
            logger.info("Controller 初始化成功")
        except Exception as e:
            logger.error(f"Controller 初始化失败: {str(e)}")
            raise

    def run(self):
        try:
            self.background_loop = QEventLoop()
            self.background_loop.exec_()
            self.update_signal.emit("开始游戏", [], [])

            while True:
                try:
                    narrative, options, new_role = self.god.generate_narrative()
                    self.update_signal.emit(narrative, new_role, options)

                    # 等待玩家选择
                    self.choice_loop = QEventLoop()
                    self.choice_loop.exec_()  # 在这里阻塞，直到 handle_choice 调用 quit()

                    player_choice = self.pending_choice
                    self.pending_choice = None

                    if not player_choice:
                        logger.warning("玩家选择为空，使用默认选择")
                        player_choice = "继续观察"

                    former_history = self.get_history()
                    former_history += '玩家做了' + player_choice + '\n'

                    npc_info = npc.interact((self.god.world_state['characters'], former_history))
                    self.NPC_signal.emit(npc_info)
                    info = (player_choice, npc_info)
                    self.god.update_information(info)

                except Exception as game_loop_error:
                    logger.error(f"游戏循环中出现错误: {str(game_loop_error)}")
                    self.update_signal.emit(f"游戏出现错误: {str(game_loop_error)}", [], ["重新开始"])
                    continue

        except Exception as e:
            logger.error(f"Controller 运行失败: {str(e)}")
            self.update_signal.emit(f"控制器运行失败: {str(e)}", [], [])

    @pyqtSlot(str)
    def handle_choice(self, content):
        try:
            self.pending_choice = content
            if self.choice_loop is not None:
                self.choice_loop.quit()
        except Exception as e:
            logger.error(f"处理选择失败: {str(e)}")

    @pyqtSlot(str)
    def receive_background(self, background):
        try:
            if not background or not background.strip():
                logger.warning("接收到空的背景设定")
                return

            print(background)
            self.god.update_world_state(background=background)
            self.story_start = True
            if self.background_loop is not None:
                self.background_loop.quit()
            logger.info("背景设定接收成功")
        except Exception as e:
            logger.error(f"接收背景失败: {str(e)}")

    def get_history(self):
        try:
            history = ""
            for event in self.god.world_state["history"]:
                if event['role'] == "系统":
                    history += event['content'] + "\n"
                else:
                    history += f"{event['role']} 做了: {event['content'].strip()}\n"
            return history
        except Exception as e:
            logger.error(f"获取历史记录失败: {str(e)}")
            return "无法获取历史记录"
