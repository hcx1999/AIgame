# 🎮 AI Interactive Story Game

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyQt5](https://img.shields.io/badge/PyQt5-5.15+-green.svg)](https://pypi.org/project/PyQt5/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

一款基于多智能体架构的沉浸式AI剧情游戏，结合了现代GUI界面、流式AI对话和动态图像生成技术。

## ✨ 核心特性

### 🤖 多智能体架构

- **ChatBot (chatbot.py)**: 游戏助手，负责与玩家交流和背景设定提取
- **GodAgent (god.py)**: 游戏叙事控制者，生成剧情和选项
- **NPC Agent (npc.py)**: 处理非玩家角色互动和反应
- **Controller (ctrller.py)**: 协调各个智能体的交互流程

### 🎨 沉浸式UI体验

- **全屏图片背景**: 支持动态场景图片生成
- **透明叠加设计**: 半透明UI元素不遮挡背景
- **流式打字机效果**: 实时字符流显示，支持速度调节
- **光标闪烁动画**: 增强视觉反馈和沉浸感
- **响应式布局**: 自适应窗口大小变化

### 🛡️ 安全性保障

- **提示词注入防护** (Prompt_injection.py): 检测并阻止恶意提示词
- **敏感词过滤** (Sensitive_word_screening.py): 多级敏感内容筛查
- **输入长度限制**: 防止过长输入影响性能

### 🖼️ 多模态内容生成

- **AI图像生成** (pic.py): 基于剧情自动生成场景图片
- **风格化渲染**: 支持多种艺术风格和画面风格
- **实时图像更新**: 根据剧情发展动态切换背景

## 🚀 快速开始

### 环境要求

- Python 3.10+
- PyQt5 5.15+
- OpenAI API 兼容接口

### 安装依赖

```bash
pip install -r requirements.txt
```

### 配置API密钥

创建 `.env` 文件并添加：

```env
SILICONFLOW_API_KEY=your_api_key_here
```

### 启动游戏

```bash
python main.py
```

## 📁 项目结构

```
AIgame/
├── main.py                    # 主启动文件
├── mainwindow.py             # 主窗口和UI逻辑
├── chatbot.py                # 游戏助手智能体
├── god.py                    # 叙事控制智能体
├── npc.py                    # NPC互动智能体
├── ctrller.py                # 多智能体控制器
├── pic.py                    # AI图像生成模块
├── Prompt_injection.py       # 提示词注入防护
├── Sensitive_word_screening.py # 敏感词过滤
├── safe_token_counter.py     # Token计数器
├── requirements.txt          # 依赖列表
├── sensitive_words/          # 敏感词词库
├── generated_images/         # 生成的图片存储
└── README.md                # 项目文档
```

## 🎯 核心模块详解

### ChatBot (聊天助手)

负责与玩家的初始交流和背景设定提取：

- 友好的对话界面
- 自动提取游戏背景信息
- 格式化输出："【背景总结】：在一个...的世界中，玩家是..."
- 支持流式输出和实时响应

### GodAgent (叙事控制者)

游戏的核心叙事引擎：

- 维护世界状态和角色信息
- 根据玩家选择生成后续剧情
- 提供多样化的选项供玩家选择
- 动态调整故事走向

### NPC Agent (角色互动)

处理非玩家角色的行为和反应：

- 基于角色性格生成对话
- 响应玩家行为和选择
- 维护角色状态和关系

### 图像生成系统

智能场景图片生成：

- 根据剧情内容自动生成背景图
- 支持多种艺术风格（动漫、写实、水彩等）
- 场景描述智能解析和优化
- 图片缓存和管理

## 🎮 游戏流程

1. **启动游戏**: 运行 `main.py` 进入游戏界面
2. **背景设定**: 与ChatBot交流，描述你想要的游戏世界
3. **剧情生成**: GodAgent根据背景生成开场剧情
4. **选择决策**: 从提供的选项中选择你的行动
5. **NPC反应**: NPC根据你的选择做出相应反应
6. **循环推进**: 剧情根据你的选择持续发展

## ⚙️ 高级配置

### 打字机效果设置

- 菜单栏 → 设置 → 打字机速度
- 可调节范围：1-100（数值越高速度越快）
- 实时预览效果

### API配置

支持多种AI模型接口：

- SiliconFlow API (默认)
- OpenAI API
- 其他兼容接口

### 安全设置

- 敏感词词库位于 `sensitive_words/` 目录
- 提示词注入检测可在 `Prompt_injection.py` 中自定义
- 支持自定义过滤规则

## 🛠️ 开发指南

### 添加新的NPC

1. 在 `npc.py` 中定义角色特征
2. 更新角色互动逻辑
3. 在 `god.py` 中注册新角色

### 自定义图像生成

1. 修改 `pic.py` 中的风格提示词
2. 调整图像生成参数
3. 添加新的风格模板

### 扩展UI功能

1. 在 `mainwindow.py` 中添加新的UI组件
2. 实现相应的信号槽连接
3. 更新样式表和布局

## 🔧 故障排除

### 常见问题

**Q: 启动时出现API连接错误**
A: 检查 `.env` 文件中的API密钥是否正确设置

**Q: 图片生成失败**
A: 确认网络连接正常，API配额充足

**Q: 界面显示异常**
A: 确认PyQt5版本兼容性，尝试更新到最新版本

**Q: 打字机效果卡顿**
A: 降低打字机速度设置，或关闭其他占用CPU的程序

### 日志调试

游戏运行时会生成详细日志，可用于问题排查：

- 控制台输出：实时运行状态
- 日志文件：详细错误信息和调用栈

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

1. Fork 本项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🎯 未来规划

### 短期目标

- [ ] 添加音效系统
- [ ] 实现游戏存档功能
- [ ] 优化AI响应速度
- [ ] 增加更多UI主题

### 长期愿景

- [ ] 多语言支持
- [ ] 语音交互功能
- [ ] 游戏数值系统（血条、好感度等）
- [ ] 多结局分支系统
- [ ] 社区创作工具

## 🌟 致谢

- [CAMEL AI](https://github.com/camel-ai/camel) - 多智能体框架
- [PyQt5](https://riverbankcomputing.com/software/pyqt/) - GUI框架
- [SiliconFlow](https://siliconflow.cn/) - AI API服务
- 所有贡献者和用户的支持

---

*开始你的AI冒险之旅吧！* 🚀✨
