from camel.models import ModelFactory
from camel.types import ModelPlatformType
from typing import List, Generator
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ChatBot:
    def __init__(
        self,
        model=None,
        system_prompt: str = """你是一款多智能体剧情游戏的游戏助手，专门负责与玩家交流，并将玩家提供的信息和指令传递给游戏系统的控制 agent。你的任务包括：
            1. 友好地与玩家进行多轮对话，理解他们的输入内容；
            2. 当玩家描述游戏背景时，你需要对其进行总结，以"【背景总结】：在一个……的世界中，玩家是……。"这样的格式输出。在总结背景时不要输出与背景无关的内容，包括问候语
            3. 如果玩家提出其他想法或建议，你应友好记录并提醒他们你不直接参与剧情内容的生成；
            4. 你不会参与游戏中的剧情推进和角色扮演，只做信息中转与玩家沟通；
            5. 所有回复尽量简洁、自然，不剧透、不主动引导剧情方向。
            请始终保持语气友善、简洁、明确。
            """,
        verbose: bool = False
    ):
        try:
            if model is None:
                model = ModelFactory.create(
                    model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
                    model_type="Qwen/QwQ-32B",  # 或者你的具体模型名
                    url='https://api.siliconflow.cn/v1',
                    api_key='sk-qseennfhdprismchczwnkzpohyjmuwgpiaywuclsisgugfvo',
                    model_config_dict={"stream": True}
                )
            self.model = model
            self.system_prompt = system_prompt
            self.chat_history: List[dict] = [
                {"role": "system", "content": self.system_prompt}
            ]
            self.verbose = verbose
            logger.info("ChatBot 初始化成功")
        except Exception as e:
            logger.error(f"ChatBot 初始化失败: {str(e)}")
            raise

    def chat_stream(self, user_input: str) -> Generator[str, None, None]:
        try:
            if not user_input or not user_input.strip():
                logger.warning("用户输入为空")
                yield "请输入有效的内容。"
                return
                
            self.chat_history.append({"role": "user", "content": user_input})

            # 流式输出
            response = self.model._client.chat.completions.create(
                model=self.model.model_type,
                messages=self.chat_history,
                stream=True
            )

            full_reply = ""
            for chunk in response:
                try:
                    content = chunk.choices[0].delta.content or ""
                    full_reply += content
                    yield content  # 流式输出
                except Exception as chunk_error:
                    logger.error(f"处理流式响应块时出错: {str(chunk_error)}")
                    continue

            self.chat_history.append({"role": "assistant", "content": full_reply})
            
        except Exception as e:
            logger.error(f"聊天流处理失败: {str(e)}")
            yield f"抱歉，处理您的请求时出现错误: {str(e)}"

    def reset(self):
        try:
            self.chat_history = [
                {"role": "system", "content": self.system_prompt}
            ]
            logger.info("ChatBot 重置成功")
        except Exception as e:
            logger.error(f"ChatBot 重置失败: {str(e)}")
            raise
