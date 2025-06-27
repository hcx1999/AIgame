from camel.agents import ChatAgent
from camel.messages import BaseMessage
from camel.models import ModelFactory
from camel.configs import ChatGPTConfig
from camel.types import ModelType, ModelPlatformType
from typing import Dict, List, Tuple, Any
import re

assistant_model_config=ChatGPTConfig(
                temperature=0.9,
            )
class GodAgent:
    def __init__(
            self,
            model=ModelFactory.create(
                model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
                model_type="Qwen/QwQ-32B",
                url='https://api.siliconflow.cn/v1',
                api_key='sk-qseennfhdprismchczwnkzpohyjmuwgpiaywuclsisgugfvo',
                model_config_dict =assistant_model_config.as_dict(),
            ),
            system_message: str = "你是一位游戏叙事控制者",
            verbose: bool = False
    ):
        self.system_message = system_message
        self.model = model
        self.verbose = verbose

        # 核心记忆组件
        self.world_state = {
            "background": "",  # 世界观设定
            "characters": {},  # NPC信息 {name: {traits: [], status: {}}}
            "history": [],  # 交互历史 [{role, content}]
        }

    def update_world_state(
            self,
            background: str = None,
            characters: Dict = None,
            history: List[Dict] = None
    ):
        """更新世界观状态"""
        if background:
            self.world_state["background"] = background
        if history:
            self.world_state["history"].extend(history)

    def generate_narrative(self) -> Tuple[str, List[str], List[str]]:
        """生成剧情和选项"""
        prompt = self._build_prompt()
        agent = ChatAgent(
            BaseMessage.make_user_message(role_name="God", content=prompt),
            model=self.model
        )
        response = agent.step(prompt)
        return self._parse_response(response.msg.content)

    def _build_prompt(self) -> str:
        """构造上帝视角提示词"""
        # 1. 核心指令
        prompt = (
            "## 角色设定\n"
            "你是游戏世界的叙事控制者，负责推进剧情发展。根据以下要素：\n"
            "1. 生成1段3-5句的剧情叙述（包含环境描写和角色互动，应当涉及所有已存在角色）（要求输出里所有玩家进行的操作的主语都是“玩家”）\n"
            "2. 生成3-5个玩家选项（每个选项不超过15字）\n"
            "3. 新增角色是非常规事件，只有当剧情出现重大转折或需要关键人物时才新增。大部分回合不需要新增角色。\n\n"
        )

        # 2. 世界状态注入
        prompt += f"### 世界观背景\n{self._truncate_text(self.world_state['background'], 1000)}\n\n"

        # 3. 历史上下文
        prompt += "\n### 最近事件\n"
        for event in self.world_state["history"][-3:]:
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

    def _truncate_text(self, text: str, max_length: int) -> str:
        """截断文本到指定长度"""
        return text if len(text) <= max_length else text[:max_length] + "..."

    def _parse_response(self, response: str) -> Tuple[str, List[str], List[str]]:
        """解析模型输出，提取剧情、选项和新增角色"""
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
        #将剧情添加到历史信息中
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

        return narrative, options, new_role

    def apply_choice_effects(self, choice_text: str):
        """根据玩家选择更新游戏状态（需自定义逻辑）"""
        # 添加到历史记录
        self.world_state["history"].append({
            "role": "玩家",
            "content": f"玩家选择{choice_text}"
        })

    def update_information(self, information: Tuple[str, List[Dict]]):
        user_choice = information[0]
        npc_action = information[1]
        self.apply_choice_effects(user_choice)
        self.world_state["history"].extend(npc_action)
