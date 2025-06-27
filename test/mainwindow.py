import sys
import threading
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLabel, QScrollArea, QSizePolicy, QTextEdit, QPushButton)
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject, QThread
from ctrller import Controller
from chatbot import ChatBot


class BubbleLabel(QLabel):
    def __init__(self, text="", is_bot=True):
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


class ScrollablePanel(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout(self)
        self.layout.setAlignment(Qt.AlignTop)
        self.setLayout(self.layout)

    def add_widget(self, widget):
        self.layout.addWidget(widget)


class ChatWorker(QObject):
    stream_signal = pyqtSignal(str)
    finish_signal = pyqtSignal()

    def __init__(self, bot: ChatBot, user_input: str):
        super().__init__()
        self.bot = bot
        self.user_input = user_input

    def run(self):
        for chunk in self.bot.chat_stream(self.user_input):
            self.stream_signal.emit(chunk)
        self.finish_signal.emit()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("多智能体剧情游戏")
        self.setFixedSize(1200, 800)
        self.option_buttons = []
        self.bot = ChatBot()
        self.setup_ui()
        self.background_summary = ""
        QTimer.singleShot(0, self.start_game_thread)

    def setup_ui(self):
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

    def start_game_thread(self):
        self.controller = Controller()
        self.controller_thread = QThread()
        self.controller.moveToThread(self.controller_thread)
        self.controller.update_signal.connect(self.update_ui)
        self.controller.NPC_signal.connect(self.update_NPC)
        self.controller_thread.started.connect(self.controller.run)
        self.controller_thread.start()
        self.send_choice_to_ctrller = self.controller.choice_signal.emit
        self.send_background_to_ctrller = self.controller.background_signal.emit

    def update_ui(self, narrative, new_role, options):
        self.add_story(narrative)
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

    def update_NPC(self, npc_info):
        for npc in npc_info:
            self.add_story(f"{npc["role"]}: {npc['content'].strip()}")

    def choose_option(self, content):
        if hasattr(self, 'send_choice_to_ctrller'):
            self.send_choice_to_ctrller(content)
            self.add_story(content)

    def send_background(self, background):
        if hasattr(self, 'send_background_to_ctrller'):
            self.send_background_to_ctrller(background)

    def add_story(self, text):
        label = QLabel(text)
        label.setWordWrap(True)
        label.setFont(QFont("Arial", 12))
        label.setStyleSheet("padding: 8px;")
        self.story_area.add_widget(label)

    def send_message(self):
        user_text = self.input_box.toPlainText().strip()
        if not user_text:
            return
        self.input_box.clear()

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

    def append_bot_text(self, chunk: str):
        chunk = chunk.strip()
        if chunk != '':
            self.bot_bubble.setText(self.bot_bubble.text() + chunk)
            self.bot_bubble.adjustSize()

        if "【背景总结】" in self.bot_bubble.text() and self.background_summary == "":
            if "。" in self.bot_bubble.text():
                self.background_summary = self.bot_bubble.text().strip().replace("【背景总结】：", "")
                self.send_background(self.background_summary)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
