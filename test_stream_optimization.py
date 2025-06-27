#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
AI剧情游戏 - 流式输出优化测试
测试新的打字机效果、光标动画和批量更新功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from mainwindow import MainWindow
import logging

# 配置详细日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('ai_game_stream_test.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)

def main():
    """主函数"""
    try:
        print("🎮 AI剧情游戏 - 流式输出优化版本")
        print("=" * 50)
        print("✨ 新功能特性:")
        print("   🎬 优化的打字机效果 - 批量字符处理")
        print("   ⚡ 光标闪烁动画 - 增强视觉反馈")
        print("   🔧 可调节打字速度 - 菜单->设置->打字机速度")
        print("   🎯 批量UI更新 - 减少重绘，提升性能")
        print("   🌊 平滑滚动 - 更流畅的用户体验")
        print("=" * 50)
        print("💡 使用提示:")
        print("   - 通过菜单栏 '设置' -> '打字机速度' 调整AI回复速度")
        print("   - 在AI回复过程中会看到闪烁的光标")
        print("   - 所有UI元素都经过优化，响应更加流畅")
        print("   - 支持全屏显示，UI元素半透明叠加")
        print("=" * 50)
        
        # 创建应用
        app = QApplication(sys.argv)
        app.setApplicationName("AI Interactive Story - Stream Optimized")
        app.setApplicationVersion("2.0.0")
        
        # 设置应用样式
        app.setStyle('Fusion')
        
        # 创建主窗口
        window = MainWindow()
        
        # 显示窗口
        window.show()
        
        # 启动应用事件循环
        logger.info("应用程序启动成功")
        return app.exec_()
        
    except Exception as e:
        logger.error(f"应用程序启动失败: {str(e)}")
        print(f"❌ 启动失败: {str(e)}")
        return 1

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 用户中断，程序退出")
        sys.exit(0)
    except Exception as e:
        print(f"❌ 未处理的异常: {str(e)}")
        logger.error(f"未处理的异常: {str(e)}", exc_info=True)
        sys.exit(1)
