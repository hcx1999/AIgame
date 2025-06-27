import sys
import threading
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QScrollArea, QSizePolicy, QTextEdit, QPushButton, QMessageBox)
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject, QThread
from ctrller import Controller
from chatbot import ChatBot
import logging
from dotenv import load_dotenv
from Prompt_injection import check_prompt_injection, truncate_text
from Sensitive_word_screening import search_keywords_in_text
from pic import generate_style_image

load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class BubbleLabel(QLabel):
    def __init__(self, text="", is_bot=True):
        try:
            super().__init__(text)
            self.setWordWrap(True)
            self.setFont(QFont("Arial", 12))
            self.setContentsMargins(10, 10, 10, 10)
            self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
            if is_bot:
                self.setStyleSheet("background-color: #cce5ff; border-radius: 10px; padding: 8px;")
            else:
                self.setStyleSheet("background-color: #e2e2e2; border-radius: 10px; padding: 8px;")
            self.adjustSize()
        except Exception as e:
            logger.error(f"BubbleLabel 初始化失败: {str(e)}")

class ScrollablePanel(QWidget):
    def __init__(self):
        try:
            super().__init__()
            self.layout = QVBoxLayout(self)
            self.layout.setAlignment(Qt.AlignTop)
            self.setLayout(self.layout)
        except Exception as e:
            logger.error(f"ScrollablePanel 初始化失败: {str(e)}")

    def add_widget(self, widget):
        try:
            if widget:
                self.layout.addWidget(widget)
        except Exception as e:
            logger.error(f"添加小部件失败: {str(e)}")

class ChatWorker(QObject):
    stream_signal = pyqtSignal(str)
    finish_signal = pyqtSignal()

    def __init__(self, bot: ChatBot, user_input: str):
        try:
            super().__init__()
            self.bot = bot
            self.user_input = user_input
        except Exception as e:
            logger.error(f"ChatWorker 初始化失败: {str(e)}")

    def run(self):
        try:
            for chunk in self.bot.chat_stream(self.user_input):
                self.stream_signal.emit(chunk)
            self.finish_signal.emit()
        except Exception as e:
            logger.error(f"ChatWorker 运行失败: {str(e)}")
            self.stream_signal.emit(f"处理聊天时出现错误: {str(e)}")
            self.finish_signal.emit()

class MainWindow(QMainWindow):
    def __init__(self):
        try:
            super().__init__()
            self.setWindowTitle("多智能体剧情游戏")
            self.setFixedSize(1200, 800)
            self.option_buttons = []
            self.bot = ChatBot()
            self.setup_ui()
            self.background_summary = ""
            self.last_image_path = "./test.png"
            QTimer.singleShot(0, self.start_game_thread)
            logger.info("MainWindow 初始化成功")
        except Exception as e:
            logger.error(f"MainWindow 初始化失败: {str(e)}")

    def setup_ui(self):
        try:
            main_widget = QWidget()
            main_layout = QHBoxLayout(main_widget)

            self.story_area = ScrollablePanel()
            self.story_scroll = QScrollArea()
            self.story_scroll.setWidgetResizable(True)
            self.story_scroll.setWidget(self.story_area)
            self.story_scroll.setStyleSheet("background-color: white;")

            self.chat_area = ScrollablePanel()
            bot_bubble = BubbleLabel("我是你的智能游戏助手，请向我发送你想要的游戏背景来开始游戏吧！或者你也可以跟我聊聊你感兴趣的其他事情", is_bot=True)
            self.chat_area.add_widget(bot_bubble)

            self.chat_scroll = QScrollArea()
            self.chat_scroll.setWidgetResizable(True)
            self.chat_scroll.setWidget(self.chat_area)
            self.chat_scroll.setStyleSheet("background-color: white;")

            self.input_box = QTextEdit()
            self.input_box.setFixedHeight(50)
            self.send_button = QPushButton("发送")
            self.send_button.clicked.connect(self.send_message)

            input_layout = QHBoxLayout()
            input_layout.addWidget(self.input_box)
            input_layout.addWidget(self.send_button)

            right_panel = QVBoxLayout()
            right_panel.addWidget(self.chat_scroll)
            right_panel.addLayout(input_layout)

            main_layout.addWidget(self.story_scroll, 2)
            main_layout.addLayout(right_panel, 1)

            self.setCentralWidget(main_widget)
            logger.info("UI 设置完成")
        except Exception as e:
            logger.error(f"UI 设置失败: {str(e)}")

    def start_game_thread(self):
        try:
            self.controller = Controller()
            self.controller_thread = QThread()
            self.controller.moveToThread(self.controller_thread)
            self.controller.update_signal.connect(self.update_ui)
            self.controller.NPC_signal.connect(self.update_NPC)
            self.controller_thread.started.connect(self.controller.run)
            self.controller_thread.start()
            self.send_choice_to_ctrller = self.controller.choice_signal.emit
            self.send_background_to_ctrller = self.controller.background_signal.emit
            logger.info("游戏线程启动成功")
        except Exception as e:
            logger.error(f"启动游戏线程失败: {str(e)}")

    def update_ui(self, narrative, new_role, options):
        try:
            self.add_story(narrative)

            new_image_path = generate_style_image(narrative, self.last_image_path)
            image_label = QLabel()
            pixmap = QPixmap(new_image_path)
            image_label.setPixmap(pixmap.scaledToWidth(256))
            self.story_area.add_widget(image_label)
            self.last_image_path = new_image_path  # 更新为最新图

            if new_role:
                self.add_story(f"你遇到了 {new_role[0]}!")
            if options:
                self.add_story("\n玩家选择:")

                for btn in self.option_buttons:
                    btn.setParent(None)
                self.option_buttons.clear()

                for i, opt in enumerate(options):
                    btn = QPushButton(f"{i+1}. {opt}")
                    btn.clicked.connect(lambda _, content=opt:self.choose_option(content))
                    self.story_area.add_widget(btn)
                    self.option_buttons.append(btn)
        except Exception as e:
            logger.error(f"更新UI失败: {str(e)}")

    def update_NPC(self, npc_info):
        try:
            if npc_info:
                for npc in npc_info:
                    self.add_story(f"{npc['role']}: {npc['content'].strip()}")
        except Exception as e:
            logger.error(f"更新NPC信息失败: {str(e)}")

    def choose_option(self, content):
        try:
            if hasattr(self, 'send_choice_to_ctrller'):
                self.send_choice_to_ctrller(content)
                self.add_story(content)
        except Exception as e:
            logger.error(f"选择选项失败: {str(e)}")

    def send_background(self, background):
        try:
            if hasattr(self, 'send_background_to_ctrller') and background:
                self.send_background_to_ctrller(background)
        except Exception as e:
            logger.error(f"发送背景失败: {str(e)}")

    def add_story(self, text):
        try:
            if text:
                label = QLabel(text)
                label.setWordWrap(True)
                label.setFont(QFont("Arial", 12))
                label.setStyleSheet("padding: 8px;")
                self.story_area.add_widget(label)
        except Exception as e:
            logger.error(f"添加故事内容失败: {str(e)}")

    def send_message(self):
        try:
            user_text = self.input_box.toPlainText().strip()
            if not user_text:
                return
            self.input_box.clear()

            user_text = truncate_text(user_text, 100)
            if user_text == "__超出字数限制":
                QMessageBox.warning(self, "字数限制检测", "输入字符过多，超出字数限制")
                return
            found_keywords = check_prompt_injection(user_text)
            if found_keywords:
                warning_msg = f"检测到潜在的提示注入关键词：{"，".join(found_keywords)}"
                QMessageBox.warning(self, "提示注入检测", warning_msg)
                return
            sensitive_keywords = search_keywords_in_text(user_text)
            if sensitive_keywords:
                warning_msg = f"检测到敏感词：{', '.join(sensitive_keywords)}\n请修改内容避免违规。"
                QMessageBox.warning(self, "敏感词检测", warning_msg)
                return

            user_bubble = BubbleLabel(user_text, is_bot=False)
            self.chat_area.add_widget(user_bubble)

            self.bot_bubble = BubbleLabel("", is_bot=True)
            self.chat_area.add_widget(self.bot_bubble)

            self.chat_thread = QThread()
            self.chat_worker = ChatWorker(self.bot, user_text)
            self.chat_worker.moveToThread(self.chat_thread)

            self.chat_worker.stream_signal.connect(self.append_bot_text)
            self.chat_worker.finish_signal.connect(self.chat_thread.quit)
            self.chat_thread.started.connect(self.chat_worker.run)
            self.chat_thread.finished.connect(self.chat_worker.deleteLater)
            self.chat_thread.finished.connect(self.chat_thread.deleteLater)

            self.chat_thread.start()
        except Exception as e:
            logger.error(f"发送消息失败: {str(e)}")

    def append_bot_text(self, chunk: str):
        try:
            chunk = chunk.strip()
            if chunk != '':
                self.bot_bubble.setText(self.bot_bubble.text() + chunk)
                self.bot_bubble.adjustSize()

            if "【背景总结】" in self.bot_bubble.text() and self.background_summary == "":
                if "。" in self.bot_bubble.text():
                    self.background_summary = self.bot_bubble.text().strip().replace("【背景总结】：", "")
                    self.send_background(self.background_summary)
        except Exception as e:
            logger.error(f"追加机器人文本失败: {str(e)}")

if __name__ == '__main__':
    try:
        app = QApplication(sys.argv)
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        logger.error(f"应用程序启动失败: {str(e)}")
        print(f"应用程序启动失败: {str(e)}")
