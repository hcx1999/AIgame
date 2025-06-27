import sys
import threading
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QProgressBar, QToolBar, QMessageBox, QTextEdit, QFrame, QScrollArea, QStatusBar, QAction,
                             QLabel, QPushButton)
from PyQt5.QtGui import QFont, QPixmap, QIcon
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject, QThread
from ctrller import Controller
from chatbot import ChatBot
import logging
from dotenv import load_dotenv
from Prompt_injection import check_prompt_injection, truncate_text
from Sensitive_word_screening import search_keywords_in_text
import os

from pic import generate_style_image

load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatWorker(QObject):
    stream_signal = pyqtSignal(str)
    char_signal = pyqtSignal(str)  # 单字符信号，用于更流畅的显示
    batch_signal = pyqtSignal(str)  # 批量字符信号，用于平滑流式输出
    finish_signal = pyqtSignal()

    def __init__(self, bot, user_input: str, typing_speed=0.005):
        try:
            super().__init__()
            self.bot = bot
            self.user_input = user_input
            self.accumulated_response = ""
            self.typing_speed = typing_speed  # 可调节的打字速度
            self.batch_size = 3  # 批量发送字符数，平衡流畅度和性能
        except Exception as e:
            logger.error(f"ChatWorker 初始化失败: {str(e)}")

    def run(self):
        try:
            print(f"=== ChatWorker 开始运行 ===")  # 调试日志
            print(f"用户输入: {self.user_input}")  # 调试日志
            print(f"ChatBot实例: {self.bot}")  # 调试日志
            
            chunk_count = 0
            char_buffer = ""
            
            for chunk in self.bot.chat_stream(self.user_input):
                chunk_count += 1
                print(f"收到第{chunk_count}个响应块: {chunk[:50]}...")  # 调试日志
                
                # 批量处理字符以提高性能
                for char in chunk:
                    self.accumulated_response += char
                    char_buffer += char
                    
                    # 当缓冲区达到批量大小或遇到标点符号时发送
                    if len(char_buffer) >= self.batch_size or char in '，。！？；：':
                        self.batch_signal.emit(char_buffer)
                        char_buffer = ""
                        
                        # 优化的延迟控制
                        import time
                        time.sleep(self.typing_speed)
                
                # 发送剩余的字符
                if char_buffer:
                    self.batch_signal.emit(char_buffer)
                    char_buffer = ""
                
                # 同时发送完整的chunk用于兼容
                self.stream_signal.emit(chunk)
            
            print(f"=== ChatWorker 完成，共收到{chunk_count}个响应块 ===")  # 调试日志
            self.finish_signal.emit()
        except Exception as e:
            print(f"ChatWorker运行异常: {str(e)}")  # 调试日志
            logger.error(f"ChatWorker 运行失败: {str(e)}")
            self.stream_signal.emit(f"处理聊天时出现错误: {str(e)}")
            self.finish_signal.emit()

class MainWindow(QMainWindow):
    def __init__(self):
        try:
            super().__init__()
            self.setWindowTitle("🎮 多智能体剧情游戏 - AI Interactive Story")
            self.setMinimumSize(1200, 800)
            self.resize(1400, 900)
            
            # 设置应用样式
            self.setStyleSheet("""
                QMainWindow {
                    background-color: #f5f5f5;
                }
                QPushButton {
                    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                                    stop:0 #4fc3f7, stop:1 #29b6f6);
                    border: none;
                    border-radius: 6px;
                    color: white;
                    font-weight: bold;
                    padding: 8px 16px;
                    min-height: 25px;
                }
                QPushButton:hover {
                    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                                    stop:0 #81d4fa, stop:1 #4fc3f7);
                }
                QPushButton:pressed {
                    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                                    stop:0 #0277bd, stop:1 #01579b);
                }
            """)
            
            self.option_buttons = []
            self.background_summary = ""
            self.last_image_path = resource_path("test.png")
            self.game_started = False
            self.options_hint = None
            self.bot = None  # 延迟初始化ChatBot
            self.current_user_input = ""  # 保存当前用户输入
            
            # 流式输出相关状态
            self.is_streaming = False
            self.current_response = ""
            self.cursor_visible = True
            self.typing_speed = 0.005  # 默认打字速度
            
            # 光标闪烁定时器
            self.cursor_timer = QTimer()
            self.cursor_timer.timeout.connect(self.toggle_cursor)
            
            # UI更新定时器，用于批量更新减少重绘
            self.ui_update_timer = QTimer()
            self.ui_update_timer.timeout.connect(self.batch_update_ui)
            self.ui_update_timer.setSingleShot(True)
            self.pending_ui_update = False
            
            # 创建状态栏
            self.create_status_bar()
            
            # 创建菜单栏
            self.create_menu_bar()
            
            # 创建工具栏
            self.create_tool_bar()
            
            # 设置UI
            self.setup_ui()
            
            QTimer.singleShot(0, self.start_game_thread)
            logger.info("MainWindow 初始化成功")
        except Exception as e:
            logger.error(f"MainWindow 初始化失败: {str(e)}")
            
    def create_status_bar(self):
        """创建状态栏"""
        try:
            self.status_bar = QStatusBar()
            self.setStatusBar(self.status_bar)
            
            # 添加进度条
            self.progress_bar = QProgressBar()
            self.progress_bar.setVisible(False)
            self.progress_bar.setMaximumWidth(200)
            self.status_bar.addPermanentWidget(self.progress_bar)
            
            # 设置初始状态
            self.status_bar.showMessage("准备就绪 - 请在输入框中输入游戏背景开始游戏")
        except Exception as e:
            logger.error(f"创建状态栏失败: {str(e)}")
    
    def create_menu_bar(self):
        """创建菜单栏"""
        try:
            menubar = self.menuBar()
            
            # 文件菜单
            file_menu = menubar.addMenu('文件(&F)')
            
            # 新游戏动作
            new_game_action = QAction('新游戏(&N)', self)
            new_game_action.setShortcut('Ctrl+N')
            new_game_action.triggered.connect(self.new_game)
            file_menu.addAction(new_game_action)
            
            file_menu.addSeparator()
            
            # 退出动作
            exit_action = QAction('退出(&X)', self)
            exit_action.setShortcut('Ctrl+Q')
            exit_action.triggered.connect(self.close)
            file_menu.addAction(exit_action)
            
            # 设置菜单
            settings_menu = menubar.addMenu('设置(&S)')
            
            # 流式输出设置
            typing_speed_action = QAction('打字机速度(&T)', self)
            typing_speed_action.triggered.connect(self.show_typing_speed_dialog)
            settings_menu.addAction(typing_speed_action)
            
            # 帮助菜单
            help_menu = menubar.addMenu('帮助(&H)')
            
            about_action = QAction('关于(&A)', self)
            about_action.triggered.connect(self.show_about)
            help_menu.addAction(about_action)
            
        except Exception as e:
            logger.error(f"创建菜单栏失败: {str(e)}")
    
    def create_tool_bar(self):
        """创建工具栏"""
        try:
            toolbar = QToolBar()
            self.addToolBar(toolbar)
            
            # 新游戏按钮
            new_game_action = QAction('🎮 新游戏', self)
            new_game_action.triggered.connect(self.new_game)
            toolbar.addAction(new_game_action)
            
            toolbar.addSeparator()
            
            # 生成图片按钮
            generate_image_action = QAction('🎨 重新生成图片', self)
            generate_image_action.triggered.connect(self.generate_current_image)
            toolbar.addAction(generate_image_action)
            
        except Exception as e:
            logger.error(f"创建工具栏失败: {str(e)}")
    
    def new_game(self):
        """开始新游戏"""
        try:
            reply = QMessageBox.question(self, '新游戏', '确定要开始新游戏吗？这将清除当前进度。',
                                       QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                # 重置游戏状态
                self.background_summary = ""
                self.game_started = False
                
                # 清除选项按钮
                self.clear_options()
                self.show_options_hint("等待游戏开始...")
                
                # 重置剧情显示
                self.narrative_content.setText("欢迎来到多智能体剧情游戏！\n请在下方输入游戏背景开始你的冒险...")
                
                # 重置图片显示
                self.image_label.setText("🎮 多智能体剧情游戏\n\n请通过菜单开始新游戏...")
                self.image_label.setStyleSheet("""
                    QLabel {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                                                  stop:0 #667eea, stop:1 #764ba2);
                        color: white;
                        font-size: 24px;
                        font-weight: bold;
                        border: none;
                    }
                """)
                
                # 重启控制器线程
                if hasattr(self, 'controller_thread'):
                    self.controller_thread.quit()
                    self.controller_thread.wait()
                
                QTimer.singleShot(100, self.start_game_thread)
                
                self.status_bar.showMessage("新游戏已开始 - 系统正在初始化...")
                logger.info("开始新游戏")
        except Exception as e:
            logger.error(f"新游戏失败: {str(e)}")
    
    def clear_chat(self):
        """清除聊天记录（在新UI中此方法保留用于菜单功能）"""
        try:
            self.status_bar.showMessage("游戏界面已重置")
            logger.info("界面已重置")
        except Exception as e:
            logger.error(f"重置界面失败: {str(e)}")
    
    def generate_current_image(self):
        """重新生成当前剧情图片"""
        try:
            if hasattr(self, 'last_narrative') and self.last_narrative:
                self.status_bar.showMessage("正在重新生成图片...")
                self.progress_bar.setVisible(True)
                
                # 异步生成图片
                def generate_image():
                    try:
                        if hasattr(self, 'last_image_path') and os.path.exists(self.last_image_path):
                            new_image_path = generate_style_image(self.last_narrative, self.last_image_path)
                            if new_image_path and os.path.exists(new_image_path):
                                self.display_image(new_image_path)
                                self.last_image_path = new_image_path
                                self.status_bar.showMessage("图片重新生成完成")
                            else:
                                self.status_bar.showMessage("图片生成失败")
                        else:
                            self.status_bar.showMessage("没有可用的基础图片")
                    except Exception as e:
                        logger.error(f"生成图片失败: {str(e)}")
                        self.status_bar.showMessage("图片生成失败")
                    finally:
                        self.progress_bar.setVisible(False)
                
                # 在新线程中生成图片
                threading.Thread(target=generate_image, daemon=True).start()
            else:
                QMessageBox.information(self, '提示', '暂时没有可生成图片的剧情内容')
        except Exception as e:
            logger.error(f"生成图片失败: {str(e)}")
    
    def show_about(self):
        """显示关于对话框"""
        try:
            QMessageBox.about(self, '关于', 
                            '多智能体剧情游戏\n\n'
                            '这是一个基于AI的交互式剧情游戏，\n'
                            '支持智能对话、剧情生成和图片创作。\n\n'
                            '版本: 1.0\n'
                            '开发: AI Assistant')
        except Exception as e:
            logger.error(f"显示关于对话框失败: {str(e)}")

    def setup_ui(self):
        """设置全新的极简UI：全屏图片+底部选项按钮"""
        try:
            # 创建中央部件
            central_widget = QWidget()
            self.setCentralWidget(central_widget)
            
            # 主垂直布局
            main_layout = QVBoxLayout(central_widget)
            main_layout.setContentsMargins(0, 0, 0, 0)
            main_layout.setSpacing(0)
            
            # 创建一个堆叠容器，让图片和其他元素重叠
            from PyQt5.QtWidgets import QStackedWidget
            stacked_widget = QWidget()
            stacked_widget.setStyleSheet("background: transparent;")
            
            # 全屏图片显示区域
            self.image_label = QLabel(stacked_widget)
            self.image_label.setGeometry(0, 0, 1400, 900)  # 占据整个区域
            self.image_label.setAlignment(Qt.AlignCenter)
            self.image_label.setStyleSheet("""
                QLabel {
                    background-color: #000000;
                    border: none;
                }
            """)
            
            # 设置默认图片
            if hasattr(self, 'last_image_path') and os.path.exists(self.last_image_path):
                self.display_image(self.last_image_path)
            else:
                # 显示默认欢迎图片或纯色背景
                self.image_label.setText("🎮 多智能体剧情游戏\n\n请在下方输入框中输入游戏背景开始游戏...")
                self.image_label.setStyleSheet("""
                    QLabel {
                        background: qlineargradient(x1:0, y1:0, x2:1, y2:1, 
                                                  stop:0 #667eea, stop:1 #764ba2);
                        color: white;
                        font-size: 24px;
                        font-weight: bold;
                        border: none;
                    }
                """)
            
            # 剧情输出区域（叠加在图片上）
            self.narrative_container = QFrame(stacked_widget)
            self.narrative_container.setGeometry(20, 20, 1360, 300)  # 位置和大小
            self.narrative_container.setStyleSheet("""
                QFrame {
                    background-color: rgba(0, 0, 0, 0.6);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    border-radius: 10px;
                }
            """)
            
            narrative_layout = QVBoxLayout(self.narrative_container)
            narrative_layout.setContentsMargins(15, 10, 15, 10)
            narrative_layout.setSpacing(5)
            
            # 剧情标题
            self.narrative_title = QLabel("📖 游戏剧情")
            self.narrative_title.setStyleSheet("""
                QLabel {
                    color: #ffffff;
                    font-size: 14px;
                    font-weight: bold;
                    background: transparent;
                    border: none;
                    padding: 5px 0px;
                }
            """)
            narrative_layout.addWidget(self.narrative_title)
            
            # 剧情内容显示区域（可滚动）
            self.narrative_scroll = QScrollArea()
            self.narrative_scroll.setWidgetResizable(True)
            self.narrative_scroll.setStyleSheet("""
                QScrollArea {
                    background-color: transparent;
                    border: none;
                }
                QScrollBar:vertical {
                    background-color: rgba(255, 255, 255, 0.2);
                    width: 8px;
                    border-radius: 4px;
                }
                QScrollBar::handle:vertical {
                    background-color: rgba(255, 255, 255, 0.5);
                    border-radius: 4px;
                }
            """)
            
            self.narrative_content = QLabel()
            self.narrative_content.setWordWrap(True)
            self.narrative_content.setAlignment(Qt.AlignTop)
            self.narrative_content.setStyleSheet("""
                QLabel {
                    color: #ffffff;
                    font-size: 16px;
                    font-weight: bold;
                    line-height: 1.6;
                    background: transparent;
                    border: none;
                    padding: 15px;
                }
            """)
            self.narrative_content.setText("🎮 欢迎来到多智能体剧情游戏！\n\n请在下方输入框中描述游戏背景开始你的冒险...")
            
            self.narrative_scroll.setWidget(self.narrative_content)
            narrative_layout.addWidget(self.narrative_scroll)
            
            # 输入框区域（叠加在图片底部）
            self.input_container = QFrame(stacked_widget)
            self.input_container.setGeometry(20, 640, 1360, 80)  # 定位在底部
            self.input_container.setStyleSheet("""
                QFrame {
                    background-color: rgba(0, 0, 0, 0.5);
                    border: none;
                    border-radius: 10px;
                }
            """)
            
            input_layout = QHBoxLayout(self.input_container)
            input_layout.setContentsMargins(20, 10, 20, 10)
            input_layout.setSpacing(10)
            
            # 输入框
            self.input_box = QTextEdit()
            self.input_box.setMaximumHeight(50)
            self.input_box.setMinimumHeight(40)
            self.input_box.setPlaceholderText("请输入游戏背景或与AI对话... (按 Ctrl+Enter 发送)")
            self.input_box.setStyleSheet("""
                QTextEdit {
                    font-family: '微软雅黑';
                    font-size: 12px;
                    background-color: rgba(255, 255, 255, 0.9);
                    border: 2px solid rgba(79, 195, 247, 0.8);
                    border-radius: 10px;
                    padding: 8px 12px;
                    color: #333333;
                    selection-background-color: #007bff;
                }
                QTextEdit:focus {
                    border-color: rgba(33, 150, 243, 1);
                    background-color: rgba(255, 255, 255, 0.95);
                }
                QTextEdit:hover {
                    border-color: rgba(129, 212, 250, 0.9);
                }
            """)
            
            # 发送按钮
            self.send_button = QPushButton("发送 📤")
            self.send_button.setMinimumWidth(80)
            self.send_button.setMinimumHeight(40)
            self.send_button.setMaximumHeight(50)
            self.send_button.setFont(QFont("微软雅黑", 10, QFont.Bold))
            self.send_button.setCursor(Qt.PointingHandCursor)
            self.send_button.setStyleSheet("""
                QPushButton {
                    font-size: 12px;
                    font-weight: bold;
                    border: none;
                    border-radius: 10px;
                    padding: 8px 16px;
                    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                                    stop:0 #28a745, stop:1 #20c997);
                    color: white;
                    text-align: center;
                }
                QPushButton:hover {
                    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                                    stop:0 #34ce57, stop:1 #2dd4aa);
                    transform: translateY(-1px);
                }
                QPushButton:pressed {
                    background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                                    stop:0 #1e7e34, stop:1 #138496);
                    transform: translateY(0px);
                }
                QPushButton:disabled {
                    background-color: #6c757d;
                    color: #adb5bd;
                }
            """)
            self.send_button.clicked.connect(self.send_message)
            
            input_layout.addWidget(self.input_box)
            input_layout.addWidget(self.send_button)
            
            # 底部选项按钮区域（叠加在图片底部）
            self.options_container = QWidget(stacked_widget)
            self.options_container.setGeometry(20, 530, 1360, 100)  # 定位在输入框上方
            self.options_container.setStyleSheet("""
                QWidget {
                    background-color: rgba(0, 0, 0, 0.6);
                    border-radius: 10px;
                }
            """)
            
            self.options_layout = QHBoxLayout(self.options_container)
            self.options_layout.setContentsMargins(20, 15, 20, 15)
            self.options_layout.setSpacing(15)
            
            # 初始化空的选项按钮列表
            self.option_buttons = []
            
            # 添加默认提示文本
            self.options_hint = QLabel("游戏选项将在这里显示...")
            self.options_hint.setAlignment(Qt.AlignCenter)
            self.options_hint.setStyleSheet("""
                QLabel {
                    color: #cccccc;
                    font-size: 14px;
                    background: transparent;
                    border: none;
                }
            """)
            self.options_layout.addWidget(self.options_hint)
            
            # 将堆叠容器添加到主布局，让图片占据全部空间
            main_layout.addWidget(stacked_widget, 1)
            
            # 设置键盘快捷键
            self.input_box.installEventFilter(self)
            
            logger.info("极简UI设置完成")
        except Exception as e:
            logger.error(f"UI 设置失败: {str(e)}")
    
    def display_image(self, image_path):
        """全屏显示图片"""
        try:
            if os.path.exists(image_path):
                pixmap = QPixmap(image_path)
                if not pixmap.isNull():
                    # 获取标签尺寸并缩放图片以适应全屏
                    label_size = self.image_label.size()
                    scaled_pixmap = pixmap.scaled(
                        label_size, Qt.KeepAspectRatio, Qt.SmoothTransformation
                    )
                    self.image_label.setPixmap(scaled_pixmap)
                    self.image_label.setText("")  # 清除文本
                    logger.info(f"图片显示成功: {image_path}")
                else:
                    logger.error(f"无法加载图片: {image_path}")
            else:
                logger.error(f"图片不存在: {image_path}")
        except Exception as e:
            logger.error(f"显示图片失败: {str(e)}")
    
    def update_options(self, options):
        """更新底部选项按钮"""
        try:
            # 清除所有现有选项
            self.clear_options()
            
            if options:
                # 移除提示文本
                if self.options_hint:
                    self.options_hint.setParent(None)
                    self.options_hint = None
                
                # 创建新的选项按钮
                for i, option in enumerate(options):
                    btn = QPushButton(f"{i+1}. {option}")
                    btn.setMinimumHeight(50)
                    btn.setMaximumHeight(60)
                    btn.setFont(QFont("微软雅黑", 12, QFont.Bold))
                    btn.setCursor(Qt.PointingHandCursor)
                    btn.setStyleSheet("""
                        QPushButton {
                            background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                                            stop:0 #4fc3f7, stop:1 #29b6f6);
                            border: 2px solid #0277bd;
                            border-radius: 12px;
                            color: white;
                            font-weight: bold;
                            padding: 8px 16px;
                            text-align: center;
                        }
                        QPushButton:hover {
                            background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                                            stop:0 #81d4fa, stop:1 #4fc3f7);
                            border-color: #01579b;
                            transform: scale(1.05);
                        }
                        QPushButton:pressed {
                            background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                                            stop:0 #0277bd, stop:1 #01579b);
                            transform: scale(0.95);
                        }
                        QPushButton:disabled {
                            background-color: #666666;
                            color: #999999;
                            border-color: #444444;
                        }
                    """)
                    
                    # 连接点击信号
                    btn.clicked.connect(lambda checked, content=option: self.choose_option(content))
                    
                    self.options_layout.addWidget(btn)
                    self.option_buttons.append(btn)
                
                logger.info(f"更新了 {len(options)} 个选项按钮")
            else:
                # 如果没有选项，显示提示文本
                self.show_options_hint("等待下一轮选项...")
                
        except Exception as e:
            logger.error(f"更新选项失败: {str(e)}")
    
    def clear_options(self):
        """清除所有选项按钮"""
        try:
            for btn in self.option_buttons:
                btn.setParent(None)
            self.option_buttons.clear()
        except Exception as e:
            logger.error(f"清除选项失败: {str(e)}")
    
    def show_options_hint(self, hint_text="游戏选项将在这里显示..."):
        """显示选项提示文本"""
        try:
            if not self.options_hint:
                self.options_hint = QLabel(hint_text)
                self.options_hint.setAlignment(Qt.AlignCenter)
                self.options_hint.setStyleSheet("""
                    QLabel {
                        color: #cccccc;
                        font-size: 14px;
                        background: transparent;
                        border: none;
                    }
                """)
            else:
                self.options_hint.setText(hint_text)
            
            self.options_layout.addWidget(self.options_hint)
        except Exception as e:
            logger.error(f"显示选项提示失败: {str(e)}")
    
    def eventFilter(self, obj, event):
        """处理键盘事件"""
        try:
            if obj == self.input_box and event.type() == event.KeyPress:
                # Ctrl+Enter 发送消息
                if event.key() == Qt.Key_Return and event.modifiers() == Qt.ControlModifier:
                    self.send_message()
                    return True
                # Enter 换行（默认行为）
                elif event.key() == Qt.Key_Return and event.modifiers() == Qt.NoModifier:
                    return False  # 让默认行为处理
                # Escape 清空输入框
                elif event.key() == Qt.Key_Escape:
                    self.input_box.clear()
                    return True
            return super().eventFilter(obj, event)
        except Exception as e:
            logger.error(f"事件过滤失败: {str(e)}")
            return False

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
        """更新游戏界面：显示图片、剧情和选项"""
        try:
            self.status_bar.showMessage("正在更新游戏界面...")
            
            # 保存当前剧情用于图片生成
            self.last_narrative = narrative
            
            # 更新剧情显示
            self.update_narrative_display(narrative, new_role)
            
            # 生成并显示剧情图片
            if hasattr(self, 'last_image_path') and os.path.exists(self.last_image_path):
                try:
                    self.status_bar.showMessage("正在生成剧情图片...")
                    new_image_path = generate_style_image(narrative, self.last_image_path)
                    if new_image_path and os.path.exists(new_image_path):
                        self.display_image(new_image_path)
                        self.last_image_path = new_image_path
                        self.status_bar.showMessage("剧情图片生成完成")
                    else:
                        self.status_bar.showMessage("图片生成失败，使用默认图片")
                except Exception as img_error:
                    logger.error(f"图片生成错误: {str(img_error)}")
                    self.status_bar.showMessage("图片生成失败，继续游戏")
            
            # 更新选项按钮
            if options:
                self.update_options(options)
                self.status_bar.showMessage("界面更新完成 - 请选择你的行动")
            else:
                self.clear_options()
                self.show_options_hint("等待下一轮选项...")
                self.status_bar.showMessage("界面更新完成")
                
        except Exception as e:
            logger.error(f"更新UI失败: {str(e)}")
            self.status_bar.showMessage("界面更新失败")
    
    def update_narrative_display(self, narrative, new_role=None):
        """更新剧情显示区域"""
        try:
            current_text = self.narrative_content.text()
            
            # 添加新的剧情内容
            new_content = f"\n\n📖 {narrative}"
            
            # 如果有新角色登场
            if new_role:
                new_content += f"\n\n🎭 新角色登场：{new_role[0]}!"
            
            # 更新显示内容
            if current_text == "欢迎来到多智能体剧情游戏！\n请在下方输入游戏背景开始你的冒险...":
                # 第一次更新，替换欢迎文本
                self.narrative_content.setText(new_content.strip())
            else:
                # 追加新内容
                self.narrative_content.setText(current_text + new_content)
            
            # 自动滚动到底部
            QTimer.singleShot(100, self.scroll_narrative_to_bottom)
            
        except Exception as e:
            logger.error(f"更新剧情显示失败: {str(e)}")
    
    def scroll_narrative_to_bottom(self):
        """滚动剧情显示到底部"""
        try:
            scrollbar = self.narrative_scroll.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
        except Exception as e:
            logger.error(f"滚动剧情显示失败: {str(e)}")
    
    def add_chat_response_to_narrative(self, response_text):
        """将AI聊天响应添加到剧情显示"""
        try:
            current_text = self.narrative_content.text()
            
            # 添加AI响应
            new_content = f"\n\n🤖 AI助手：{response_text}"
            
            # 更新显示内容
            if current_text == "欢迎来到多智能体剧情游戏！\n请在下方输入游戏背景开始你的冒险...":
                # 第一次更新，替换欢迎文本
                self.narrative_content.setText(new_content.strip())
            else:
                # 追加新内容
                self.narrative_content.setText(current_text + new_content)
            
            # 自动滚动到底部
            QTimer.singleShot(100, self.scroll_narrative_to_bottom)
            
        except Exception as e:
            logger.error(f"添加聊天响应失败: {str(e)}")



    def update_NPC(self, npc_info):
        """更新NPC信息（在剧情显示区域显示）"""
        try:
            if npc_info:
                current_text = self.narrative_content.text()
                npc_content = ""
                
                for npc in npc_info:
                    npc_message = f"\n🎭 {npc['role']}: {npc['content'].strip()}"
                    npc_content += npc_message
                
                # 更新剧情显示
                if npc_content:
                    self.narrative_content.setText(current_text + npc_content)
                    
                    # 自动滚动到底部
                    QTimer.singleShot(100, self.scroll_narrative_to_bottom)
                    
                    # 在状态栏显示简短提示
                    self.status_bar.showMessage("NPC行动已更新")
                    logger.info(f"NPC更新已显示在剧情区域")
                    
                    # 3秒后恢复正常状态栏信息
                    QTimer.singleShot(3000, lambda: self.status_bar.showMessage("准备下一轮行动..."))
        except Exception as e:
            logger.error(f"更新NPC信息失败: {str(e)}")

    def choose_option(self, content):
        """选择游戏选项"""
        try:
            if hasattr(self, 'send_choice_to_ctrller'):
                self.send_choice_to_ctrller(content)
                
                # 在剧情区域显示玩家选择
                current_text = self.narrative_content.text()
                player_choice = f"\n\n👤 玩家选择: {content}"
                self.narrative_content.setText(current_text + player_choice)
                QTimer.singleShot(100, self.scroll_narrative_to_bottom)
                
                # 禁用所有选项按钮并显示选择结果
                for btn in self.option_buttons:
                    btn.setEnabled(False)
                    if btn.text().endswith(content) or content in btn.text():
                        # 高亮选择的按钮
                        btn.setStyleSheet("""
                            QPushButton {
                                background-color: qlineargradient(x1:0, y1:0, x2:0, y2:1, 
                                                                stop:0 #4caf50, stop:1 #388e3c);
                                border: 2px solid #2e7d32;
                                border-radius: 12px;
                                color: white;
                                font-weight: bold;
                                padding: 8px 16px;
                            }
                        """)
                    else:
                        # 其他按钮变灰
                        btn.setStyleSheet("""
                            QPushButton {
                                background-color: #666666;
                                color: #999999;
                                border: 1px solid #444444;
                                border-radius: 12px;
                                font-weight: bold;
                                padding: 8px 16px;
                            }
                        """)
                
                self.status_bar.showMessage(f"已选择: {content} - 等待剧情发展...")
                logger.info(f"玩家选择: {content}")
        except Exception as e:
            logger.error(f"选择选项失败: {str(e)}")

    def send_background(self, background):
        """发送游戏背景（保留接口兼容性）"""
        try:
            if hasattr(self, 'send_background_to_ctrller') and background:
                self.send_background_to_ctrller(background)
                self.game_started = True
                self.status_bar.showMessage("游戏背景已设置，游戏开始！")
                logger.info(f"游戏背景已设置: {background}")
        except Exception as e:
            logger.error(f"发送背景失败: {str(e)}")
    
    def resizeEvent(self, event):
        """窗口大小改变时重新调整布局"""
        try:
            super().resizeEvent(event)
            
            # 获取当前窗口大小
            width = self.width()
            height = self.height()
            
            # 调整图片标签大小
            if hasattr(self, 'image_label'):
                self.image_label.setGeometry(0, 0, width, height)
            
            # 调整剧情容器位置和大小
            if hasattr(self, 'narrative_container'):
                container_width = width - 40  # 左右各留20px边距
                self.narrative_container.setGeometry(20, 20, container_width, 300)
            
            # 调整输入框容器位置和大小
            if hasattr(self, 'input_container'):
                container_width = width - 40
                input_y = height - 160  # 距离底部160px
                self.input_container.setGeometry(20, input_y, container_width, 80)
            
            # 调整选项容器位置和大小
            if hasattr(self, 'options_container'):
                container_width = width - 40
                options_y = height - 270  # 距离底部270px，确保在输入框上方
                self.options_container.setGeometry(20, options_y, container_width, 100)
            
            # 如果有图片显示，重新调整大小
            if hasattr(self, 'last_image_path') and self.last_image_path and os.path.exists(self.last_image_path):
                QTimer.singleShot(100, lambda: self.display_image(self.last_image_path))
                
        except Exception as e:
            logger.error(f"窗口大小调整失败: {str(e)}")
    
    def init_chatbot(self):
        """初始化ChatBot实例"""
        if self.bot is None:
            try:
                from chatbot import ChatBot
                self.bot = ChatBot()
                self.status_bar.showMessage("AI助手已就绪")
                return True
            except Exception as e:
                logger.error(f"ChatBot初始化失败: {str(e)}")
                self.status_bar.showMessage("AI助手初始化失败")
                QMessageBox.warning(self, '警告', f'AI助手初始化失败：{str(e)}')
                return False
        return True

    def send_message(self):
        """发送消息到AI助手"""
        try:
            print("=== 开始发送消息 ===")  # 调试日志
            
            # 确保ChatBot已初始化
            if not self.init_chatbot():
                return
            
            user_text = self.input_box.toPlainText().strip()
            print(f"用户输入: {user_text}")  # 调试日志
            
            # 输入验证
            if not user_text:
                self.input_box.setStyleSheet(self.input_box.styleSheet() + """
                    QTextEdit {
                        border-color: #dc3545 !important;
                    }
                """)
                self.status_bar.showMessage("请输入消息内容")
                # 2秒后恢复正常样式
                QTimer.singleShot(2000, self.reset_input_style)
                return

            user_text = truncate_text(user_text, 100)
            if user_text == "__超出字数限制":
                QMessageBox.warning(self, "字数限制检测", "输入字符过多，超出字数限制")
                return
            found_keywords = check_prompt_injection(user_text)
            if found_keywords:
                warning_msg = f"检测到潜在的提示注入关键词：{','.join(found_keywords)}"
                QMessageBox.warning(self, "提示注入检测", warning_msg)
                return
            sensitive_keywords = search_keywords_in_text(user_text)
            if sensitive_keywords:
                warning_msg = f"检测到敏感词：{', '.join(sensitive_keywords)}\n请修改内容避免违规。"
                QMessageBox.warning(self, "敏感词检测", warning_msg)
                return

            # 保存用户输入
            self.current_user_input = user_text
            self.current_response = ""
            self.is_streaming = True
            
            # 显示最新的对话 - 只显示当前这一轮
            self.narrative_content.setText(f"👤 你：{user_text}\n\n🤖 AI助手：正在思考...")
            self.scroll_narrative_to_bottom()
            
            # 清空输入框
            self.input_box.clear()
            self.reset_input_style()
            
            # 禁用发送按钮防止重复发送
            self.send_button.setEnabled(False)
            self.send_button.setText("发送中...")

            # 显示进度条
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)  # 无限进度条
            self.status_bar.showMessage("正在处理您的消息...")
            
            print("创建聊天工作线程...")  # 调试日志
            # 创建聊天工作线程
            self.chat_thread = QThread()
            self.chat_worker = ChatWorker(self.bot, user_text, self.typing_speed)
            self.chat_worker.moveToThread(self.chat_thread)

            # 连接信号
            self.chat_worker.stream_signal.connect(self.process_chat_response)
            self.chat_worker.char_signal.connect(self.process_char_response)
            self.chat_worker.batch_signal.connect(self.process_batch_response)  # 新增批量字符处理
            self.chat_worker.finish_signal.connect(self.chat_finished)
            self.chat_thread.started.connect(self.chat_worker.run)
            self.chat_thread.finished.connect(self.chat_worker.deleteLater)
            self.chat_thread.finished.connect(self.chat_thread.deleteLater)

            print("启动聊天线程...")  # 调试日志
            
            # 设置流式输出状态
            self.is_streaming = True
            self.current_response = ""
            
            # 启动光标闪烁效果
            self.start_cursor_animation()
            
            self.chat_thread.start()
            print("聊天线程已启动")  # 调试日志
            
        except Exception as e:
            logger.error(f"发送消息失败: {str(e)}")
            print(f"发送消息异常: {str(e)}")  # 调试日志
            self.status_bar.showMessage("发送消息失败")
            self.chat_finished()  # 恢复UI状态
            QMessageBox.critical(self, '错误', f'发送消息时出现错误：{str(e)}')
    
    def reset_input_style(self):
        """重置输入框样式"""
        try:
            self.input_box.setStyleSheet("""
                QTextEdit {
                    font-family: '微软雅黑';
                    font-size: 12px;
                    background-color: rgba(255, 255, 255, 0.9);
                    border: 2px solid rgba(79, 195, 247, 0.8);
                    border-radius: 10px;
                    padding: 8px 12px;
                    color: #333333;
                    selection-background-color: #007bff;
                }
                QTextEdit:focus {
                    border-color: rgba(33, 150, 243, 1);
                    background-color: rgba(255, 255, 255, 0.95);
                }
                QTextEdit:hover {
                    border-color: rgba(129, 212, 250, 0.9);
                }
            """)
        except Exception as e:
            logger.error(f"重置输入框样式失败: {str(e)}")
    
    def start_cursor_animation(self):
        """启动光标闪烁动画"""
        self.cursor_visible = True
        self.cursor_timer.start(500)  # 每500ms闪烁一次
    
    def stop_cursor_animation(self):
        """停止光标闪烁动画"""
        self.cursor_timer.stop()
        self.cursor_visible = False
    
    def toggle_cursor(self):
        """切换光标显示状态"""
        self.cursor_visible = not self.cursor_visible
        self.request_ui_update()
    
    def request_ui_update(self):
        """请求UI更新（批量更新以减少重绘）"""
        if not self.pending_ui_update:
            self.pending_ui_update = True
            self.ui_update_timer.start(16)  # ~60fps更新频率
    
    def batch_update_ui(self):
        """批量更新UI"""
        try:
            if self.pending_ui_update:
                self.pending_ui_update = False
                
                # 构建显示文本
                cursor_char = "▋" if self.cursor_visible and self.is_streaming else ""
                display_text = f"👤 你：{self.current_user_input}\n\n🤖 AI助手：{self.current_response}{cursor_char}"
                
                # 更新显示
                self.narrative_content.setText(display_text)
                
                # 平滑滚动到底部
                self.smooth_scroll_to_bottom()
                
        except Exception as e:
            logger.error(f"批量UI更新失败: {str(e)}")
    
    def smooth_scroll_to_bottom(self):
        """平滑滚动到底部"""
        try:
            scrollbar = self.narrative_scroll.verticalScrollBar()
            scrollbar.setValue(scrollbar.maximum())
        except Exception as e:
            logger.error(f"滚动失败: {str(e)}")
    
    def process_batch_response(self, batch_text: str):
        """处理批量字符AI响应流 - 优化的打字机效果"""
        try:
            self.current_response += batch_text
            self.request_ui_update()
            
        except Exception as e:
            logger.error(f"处理批量字符AI响应失败: {str(e)}")

    def chat_finished(self):
        """聊天完成后的处理"""
        try:
            self.progress_bar.setVisible(False)
            self.progress_bar.setRange(0, 100)  # 恢复正常进度条
            
            # 恢复发送按钮
            self.send_button.setEnabled(True)
            self.send_button.setText("发送 📤")
            
            # 重置流式状态
            self.is_streaming = False
            
            # 停止光标动画和UI更新
            self.stop_cursor_animation()
            self.ui_update_timer.stop()
            
            # 最终UI更新，移除光标
            display_text = f"👤 你：{self.current_user_input}\n\n🤖 AI助手：{self.current_response}"
            self.narrative_content.setText(display_text)
            self.smooth_scroll_to_bottom()
            
            # 清理响应状态
            if hasattr(self, 'current_response'):
                # 保持最终响应，不删除
                pass
            
            if hasattr(self, 'chat_thread'):
                self.chat_thread.quit()
                
            self.status_bar.showMessage("对话完成")
            print("=== 聊天完成，UI状态已恢复 ===")
                
        except Exception as e:
            logger.error(f"聊天完成处理失败: {str(e)}")

    def process_char_response(self, char: str):
        """处理单字符AI响应流 - 向后兼容，现在主要使用批量处理"""
        try:
            if not hasattr(self, 'current_response'):
                self.current_response = ""
            
            self.current_response += char
            
            # 使用批量更新机制
            self.request_ui_update()
            
        except Exception as e:
            logger.error(f"处理单字符AI响应失败: {str(e)}")

    def process_chat_response(self, chunk: str):
        """处理AI响应流 - 兼容模式，主要用于背景总结检测"""
        try:
            chunk = chunk.strip()
            if chunk != '':
                # 检查是否包含背景总结
                if "【背景总结】" in self.current_response and self.background_summary == "":
                    if "。" in self.current_response:
                        # 提取背景总结内容
                        if "【背景总结】：" in self.current_response:
                            summary_part = self.current_response.split("【背景总结】：")[1]
                            self.background_summary = summary_part.split("。")[0] + "。"
                        elif "【背景总结】:" in self.current_response:
                            summary_part = self.current_response.split("【背景总结】:")[1]
                            self.background_summary = summary_part.split("。")[0] + "。"
                        
                        if self.background_summary:
                            # 发送背景到游戏控制器
                            self.send_background(self.background_summary)
                            self.status_bar.showMessage("游戏背景已设置，剧情即将开始...")
                            
        except Exception as e:
            logger.error(f"处理AI响应失败: {str(e)}")

    def show_typing_speed_dialog(self):
        """显示打字机速度设置对话框"""
        try:
            from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QSlider, QLabel, QPushButton
            
            dialog = QDialog(self)
            dialog.setWindowTitle("打字机速度设置")
            dialog.setFixedSize(350, 150)
            
            layout = QVBoxLayout(dialog)
            
            # 标题
            title_label = QLabel("🎬 调整AI回复打字机效果速度")
            title_label.setStyleSheet("font-size: 14px; font-weight: bold; color: #2196F3;")
            layout.addWidget(title_label)
            
            # 速度滑块
            speed_label = QLabel("打字速度:")
            layout.addWidget(speed_label)
            
            speed_slider = QSlider(Qt.Horizontal)
            speed_slider.setRange(1, 100)
            current_speed_value = int((0.1 - self.typing_speed) * 1000)
            speed_slider.setValue(max(1, min(100, current_speed_value)))
            layout.addWidget(speed_slider)
            
            # 按钮
            button_layout = QHBoxLayout()
            ok_button = QPushButton("确定")
            cancel_button = QPushButton("取消")
            
            def apply_settings():
                speed_value = speed_slider.value()
                self.typing_speed = 0.1 - (speed_value - 1) * 0.099 / 99
                self.status_bar.showMessage(f"打字机速度已设置: {speed_value}/100", 3000)
                dialog.accept()
            
            ok_button.clicked.connect(apply_settings)
            cancel_button.clicked.connect(dialog.reject)
            
            button_layout.addWidget(cancel_button)
            button_layout.addWidget(ok_button)
            layout.addLayout(button_layout)
            
            dialog.exec_()
            
        except Exception as e:
            logger.error(f"显示设置对话框失败: {str(e)}")

def resource_path(relative_path):
    import sys, os
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.abspath(relative_path)