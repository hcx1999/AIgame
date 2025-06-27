from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType
from typing import List, Generator
import os

from camel.utils import OpenAITokenCounter
from dotenv import load_dotenv
from safe_token_counter import SimpleTokenCounter

load_dotenv()

class ChatBot:
    def __init__(
        self,
        model=None,
        system_prompt: str = """你是一款多智能体剧情游戏的游戏助手，专门负责与玩家交流，并将玩家提供的信息和指令传递给游戏系统的控制 agent。你的任务包括：
            1. 友好地与玩家进行多轮对话，理解他们的输入内容；
            2. 当玩家描述游戏背景时，你需要对其进行总结，以“【背景总结】：在一个……的世界中，玩家是……。”这样的格式输出。在总结背景时不要输出与背景无关的内容，包括问候语
            3. 如果玩家提出其他想法或建议，你应友好记录并提醒他们你不直接参与剧情内容的生成；
            4. 你不会参与游戏中的剧情推进和角色扮演，只做信息中转与玩家沟通；
            5. 所有回复尽量简洁、自然，不剧透、不主动引导剧情方向。
            请始终保持语气友善、简洁、明确。
            """,
        verbose: bool = False
    ):
        if model is None:
            model = ModelFactory.create(
                model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
                model_type="Qwen/QwQ-32B",  # 或者你的具体模型名
                url='https://api.siliconflow.cn/v1',
                api_key=os.getenv("SILICONFLOW_API_KEY"),
                model_config_dict={"stream": True},
                token_counter=SimpleTokenCounter()
            )
            model._token_counter_func = lambda x: len(x.split())
        self.model = model
        self.system_prompt = system_prompt
        self.chat_history: List[dict] = [
            {"role": "system", "content": self.system_prompt}
        ]
        self.verbose = verbose

    def chat_stream(self, user_input: str) -> Generator[str, None, None]:
        self.chat_history.append({"role": "user", "content": user_input})

        # 流式输出
        response = self.model._client.chat.completions.create(
            model=self.model.model_type,
            messages=self.chat_history,
            stream=True
        )

        full_reply = ""
        for chunk in response:
            content = chunk.choices[0].delta.content or ""
            full_reply += content
            yield content  # 流式输出

        self.chat_history.append({"role": "assistant", "content": full_reply})

    def reset(self):
        self.chat_history = [
            {"role": "system", "content": self.system_prompt}
        ]
