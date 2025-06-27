from camel.agents import ChatAgent
from camel.models import ModelFactory
from camel.types import ModelPlatformType
import logging
import os
from safe_token_counter import SimpleTokenCounter
from dotenv import load_dotenv

load_dotenv()

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    model = ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
        model_type="Qwen/QwQ-32B",
        url='https://api.siliconflow.cn/v1',
        api_key=os.getenv("SILICONFLOW_API_KEY"),
        token_counter=SimpleTokenCounter()
    )

    agent = ChatAgent(
        model=model,
        output_language='中文'
    )
    logger.info("NPC 模块初始化成功")
except Exception as e:
    logger.error(f"NPC 模块初始化失败: {str(e)}")
    raise

#while True:
#    str = input("You: ")
#    response = agent.step(str)
#    print(response.msgs[0].content)


#str由character，info_str构成
#character是形如['钟离','胡桃’,'空']
#info_str则为当前剧情加玩家选择比如'四个人一起玩炸金花，玩家选择作弊。'
def interact(str):
    """处理NPC交互"""
    try:
        if not str or len(str) != 2:
            logger.error("传入参数格式错误")
            return []
            
        character, info_str = str
        
        if not character or not info_str:
            logger.warning("角色信息或情节信息为空")
            return []
            
        return_info = []
        
        for dic in character.keys():
            try:
                name = dic
                des = character[dic].get("traits", "")
                
                if not name or not des:
                    logger.warning(f"角色 {name} 信息不完整")
                    continue
                    
                input_text = info_str + '你是' + name + '，你的性格如下：' + des + '请以' + name + "为主语写一下接下来的言行，控制在50字以内。要求能够让故事能持续下去，不必完结太快。"
                
                response = agent.step(input_text)
                
                if response and response.msgs and len(response.msgs) > 0:
                    content = response.msgs[0].content
                    return_info.append({"role": name, "content": content})
                else:
                    logger.warning(f"角色 {name} 响应为空")
                    
            except Exception as char_error:
                logger.error(f"处理角色 {name} 时出错: {str(char_error)}")
                continue
                
        return return_info
        
    except Exception as e:
        logger.error(f"NPC 交互失败: {str(e)}")
        return []

'''
character={"小明":"沉稳内敛，不善言辞，但心思细腻，善于观察细节。做事认真负责，一旦决定的事情就会全力以赴，不达目的绝不罢休。平时话不多，但每句话都经过深思熟虑，给人一种可靠的感觉。",
           "小美":"热情开朗，性格外向，善于与人交往，总是能迅速融入新环境。她充满活力，对生活充满热情，喜欢尝试新鲜事物。同时，她也很有同情心，乐于助人，是朋友眼中的“开心果”。",
           "小王":"冷静理性，善于分析问题，逻辑思维能力很强。面对复杂的情况，他总能保持冷静，迅速找到解决问题的关键。不过，他有时会显得有点冷漠，对人情世故不太在意，更注重事情的本质和结果。"}
info_str="玩家李磊，小明，小美，小王四个人一起玩炸金花，玩家李磊选择作弊。"
god_data=[character,info_str]
print(interact(god_data))
'''