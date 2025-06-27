#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from PyQt5.QtWidgets import QApplication

def main():
    """启动多智能体剧情游戏"""
    print("=== 🎮 多智能体剧情游戏 ===")
    print("最新特性：")
    print("1. 🖼️ 全屏沉浸式图片背景")
    print("2. ❌ 无白色分隔框，界面简洁")
    print("3. 📱 透明半透明UI叠加设计")
    print("4. ⌨️ 智能输入框，支持快捷键")
    print("5. 🎮 游戏选项按钮优化位置")
    print("6. 🎨 提升透明度，更好视觉效果")
    print("7. 📏 响应式布局，适应窗口大小")
    print("8. 💪 大字体清晰显示(16px)")
    print()
    
    try:
        app = QApplication(sys.argv)
        
        from mainwindow import MainWindow
        window = MainWindow()
        window.show()
        
        print("✅ 程序启动成功！")
        print("游戏说明：")
        print("- 🖼️ 图片完全占据窗口，沉浸式体验")
        print("- 💬 剧情显示区在图片顶部，半透明设计")
        print("- 🎮 选项按钮在输入框上方，便于操作")
        print("- ⌨️ 输入框在底部，支持Ctrl+Enter发送")
        print("- 📱 可以调整窗口大小，布局自动适应")
        print("- 💭 只显示最近一次对话，界面清爽")
        print("- 🔤 大字体粗体显示，阅读舒适")
        print()
        print("开始你的AI剧情冒险吧！🚀")
        
        sys.exit(app.exec_())
        
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
