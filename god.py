from camel.agents import ChatAgent
from camel.messages import BaseMessage
from camel.models import ModelFactory
from camel.types import ModelType, ModelPlatformType
from typing import Dict, List, Tuple, Any
import re
import logging
import os
from safe_token_counter import SimpleTokenCounter
from dotenv import load_dotenv

load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GodAgent:
    def __init__(
            self,
            model=None,
            system_message: str = "你是一位游戏叙事控制者",
            verbose: bool = False
    ):
        try:
            if model is None:
                model = ModelFactory.create(
                    model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
                    model_type="Qwen/QwQ-32B",
                    url='https://api.siliconflow.cn/v1',
                    api_key=os.getenv("SILICONFLOW_API_KEY"),
                    token_counter=SimpleTokenCounter()
                )
            self.system_message = system_message
            self.model = model
            self.verbose = verbose

            # 核心记忆组件
            self.world_state = {
                "background": "",  # 世界观设定
                "characters": {},  # NPC信息 {name: {traits: [], status: {}}}
                "history": [],  # 交互历史 [{role, content}]
            }
            logger.info("GodAgent 初始化成功")
        except Exception as e:
            logger.error(f"GodAgent 初始化失败: {str(e)}")
            raise

    def update_world_state(
            self,
            background: str = None,
            characters: Dict = None,
            history: List[Dict] = None
    ):
        """更新世界观状态"""
        try:
            if background:
                self.world_state["background"] = background
                logger.info("背景设定已更新")
            if characters:
                self.world_state["characters"].update(characters)
                logger.info("角色信息已更新")
            if history:
                self.world_state["history"].extend(history)
                logger.info("历史记录已更新")
        except Exception as e:
            logger.error(f"更新世界状态失败: {str(e)}")

    def generate_narrative(self) -> Tuple[str, List[str], List[str]]:
        """生成剧情和选项"""
        try:
            prompt = self._build_prompt()
            agent = ChatAgent(
                BaseMessage.make_user_message(role_name="God", content=prompt),
                model=self.model
            )
            response = agent.step(prompt)
            return self._parse_response(response.msg.content)
        except Exception as e:
            logger.error(f"生成剧情失败: {str(e)}")
            # 返回默认值，确保游戏可以继续
            return "发生了意想不到的情况...", ["观察周围", "等待片刻", "继续前进"], []

    def _build_prompt(self) -> str:
        """构造上帝视角提示词"""
        try:
            # 1. 核心指令
            prompt = (
                "## 角色设定\n"
                "你是游戏世界的叙事控制者，负责推进剧情发展。根据以下要素：\n"
                "1. 生成1段3-5句的剧情叙述（包含环境描写和角色互动，应当涉及所有已存在角色）（要求输出里所有玩家进行的操作的主语都是'玩家'）\n"
                "2. 生成3-5个玩家选项（每个选项不超过15字）\n"
                "3. 新增角色是非常规事件，只有当剧情出现重大转折或需要关键人物时才新增。大部分回合不需要新增角色。\n\n"
            )

            # 2. 世界状态注入
            background = self.world_state.get('background', '')
            prompt += f"### 世界观背景\n{self._truncate_text(background, 1000)}\n\n"

            # 3. 历史上下文
            prompt += "\n### 最近事件\n"
            history = self.world_state.get('history', [])
            for event in history[-3:]:
                role = event.get('role', '玩家')
                content = self._truncate_text(event.get('content', ''), 200)
                prompt += f"{role}: {content}\n"

            # 4. 输出格式要求
            prompt += (
                "\n## 输出格式要求\n"
                "请严格按照以下格式输出：\n"
                "剧情: [生成的叙述文本]\n"
                "选项:\n"
                "1. [选项1]\n"
                "2. [选项2]\n"
                "3. [选项3]"
                "若有新增角色，则添加以下内容："
                "\n新角色:新角色名字 新角色描述"
            )

            # 输出格式要求部分添加更明确的示例
            prompt += (
                "\n## 输出格式示例\n"
                "剧情: 小镇中人声鼎沸，热闹非凡\n"
                "选项:\n"
                "1. 向路人询问热闹的原因\n"
                "2. 前往镇中广场\n"
                "剧情: 你走进昏暗的酒馆，看到角落坐着一位神秘的老人...\n"
                "选项:\n"
                "1. 上前与老人交谈\n"
                "2. 在吧台点一杯麦酒\n"
                "3. 观察酒馆内的情况\n"
                "新角色:老巫师 穿着灰色长袍，手持橡木法杖"
            )

            return prompt
        except Exception as e:
            logger.error(f"构建提示词失败: {str(e)}")
            return "生成一个简单的冒险情节"

    def _truncate_text(self, text: str, max_length: int) -> str:
        """截断文本到指定长度"""
        try:
            return text if len(text) <= max_length else text[:max_length] + "..."
        except Exception as e:
            logger.error(f"截断文本失败: {str(e)}")
            return str(text)[:max_length] if text else ""

    def _parse_response(self, response: str) -> Tuple[str, List[str], List[str]]:
        """解析模型输出，提取剧情、选项和新增角色"""
        try:
            # 初始化变量
            narrative = ""
            options = []
            new_role = None

            # 尝试提取新角色信息（如果存在）
            new_role_match = re.search(r"新角色[:：]\s*(\S+)\s+([^\n]+)", response)
            if new_role_match:
                new_role_name = new_role_match.group(1).strip()
                new_role_desc = new_role_match.group(2).strip()
                new_role = [new_role_name, new_role_desc]
                # 将新角色添加到世界状态
                self.world_state["characters"][new_role_name] = {"traits": new_role_desc}

            # 尝试提取剧情部分
            narrative_match = re.search(r"剧情[:：]([\s\S]+?)选项[:：]", response, re.IGNORECASE)
            if narrative_match:
                narrative = narrative_match.group(1).strip()
            else:
                # 容错处理：尝试查找其他可能的剧情标识
                alt_narrative_match = re.search(r"(?:剧情|描述|叙述)[:：]?\s*([^\n]+(?:\n[^\n]+){0,4})", response)
                if alt_narrative_match:
                    narrative = alt_narrative_match.group(1).strip()
                else:
                    # 最后的容错：取前三行作为剧情
                    narrative = "\n".join(response.split("\n")[:3]).strip()
                    
            # 将剧情添加到历史信息中
            self.update_world_state(history=[
                {"role": "系统", "content": narrative}
            ])

            # 尝试提取选项部分
            options_section = ""
            options_match = re.search(r"选项[:：]([\s\S]+)", response, re.IGNORECASE)
            if options_match:
                options_section = options_match.group(1)
            elif new_role_match:
                # 如果找不到选项但有新角色，尝试在新角色前找选项
                options_match = re.search(r"选项[:：]([\s\S]+?)新角色[:：]", response, re.IGNORECASE)
                if options_match:
                    options_section = options_match.group(1)

            # 解析选项内容
            if options_section:
                # 使用更健壮的正则匹配多种格式的选项
                option_lines = re.findall(
                    r'^\s*(?:[-*]|\d+[.)]?)\s*(.+)$',
                    options_section,
                    re.MULTILINE
                )
                options = [line.strip() for line in option_lines if line.strip()]

            # 如果仍未找到选项，尝试最后几行作为选项
            if not options:
                last_lines = [line.strip() for line in response.split('\n')[-5:] if line.strip()]
                if 2 <= len(last_lines) <= 5:  # 最后2-5行可能是选项
                    options = last_lines

            # 确保选项数量在合理范围内
            options = options[:5]  # 最多保留5个选项
            
            # 如果仍然没有选项，提供默认选项
            if not options:
                options = ["观察周围", "继续前进", "等待片刻"]

            return narrative, options, new_role
            
        except Exception as e:
            logger.error(f"解析响应失败: {str(e)}")
            return "解析剧情时出现错误", ["重试", "继续"], []

    def apply_choice_effects(self, choice_text: str):
        """根据玩家选择更新游戏状态（需自定义逻辑）"""
        try:
            # 添加到历史记录
            self.world_state["history"].append({
                "role": "玩家",
                "content": f"玩家选择{choice_text}"
            })
        except Exception as e:
            logger.error(f"应用选择效果失败: {str(e)}")

    def update_information(self, information: Tuple[str, List[Dict]]):
        try:
            user_choice = information[0]
            npc_action = information[1]
            self.apply_choice_effects(user_choice)
            if npc_action:
                self.world_state["history"].extend(npc_action)
        except Exception as e:
            logger.error(f"更新信息失败: {str(e)}")