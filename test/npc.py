from camel.agents import ChatAgent
from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType
import os

from camel.utils import OpenAITokenCounter
from dotenv import load_dotenv
from safe_token_counter import SimpleTokenCounter

load_dotenv()

model = ModelFactory.create(
    model_platform=ModelPlatformType.OPENAI_COMPATIBLE_MODEL,
    model_type="Qwen/QwQ-32B",
    url='https://api.siliconflow.cn/v1',
    api_key=os.getenv("SILICONFLOW_API_KEY"),
    token_counter=SimpleTokenCounter()
)

agent = ChatAgent(
    model=model,
    output_language='中文',
)

#while True:
#    str = input("You: ")
#    response = agent.step(str)
#    print(response.msgs[0].content)


#str由character，info_str构成
#character是形如['钟离','胡桃’,'空']
#info_str则为当前剧情加玩家选择比如'四个人一起玩炸金花，玩家选择作弊。'
def interact(info):
    character,info_str=info #character是字典
    return_info=[]
    for dic in character.keys():
        #print("当前角色:", dic)
        return_str=""
        name=dic
        des=character[dic]["traits"] #这意味着character是一个字典
        input=info_str+'你是'+name+'，你的性格如下：'+des+'请以'+name+"为主语写一下接下来的言行，控制在50字以内。要求能够让故事能持续下去，不必完结太快。"
        response = agent.step(input)
        return_info.append({"role": name, "content": response.msgs[0].content})
        return_str += name + "做了:" + response.msgs[0].content.strip() + "\n"
        #info_str=info_str+response.msgs[0].content
        #print(return_str)
    #return(info_str)
    return return_info

'''
character={"小明":"沉稳内敛，不善言辞，但心思细腻，善于观察细节。做事认真负责，一旦决定的事情就会全力以赴，不达目的绝不罢休。平时话不多，但每句话都经过深思熟虑，给人一种可靠的感觉。",
           "小美":"热情开朗，性格外向，善于与人交往，总是能迅速融入新环境。她充满活力，对生活充满热情，喜欢尝试新鲜事物。同时，她也很有同情心，乐于助人，是朋友眼中的“开心果”。",
           "小王":"冷静理性，善于分析问题，逻辑思维能力很强。面对复杂的情况，他总能保持冷静，迅速找到解决问题的关键。不过，他有时会显得有些冷漠，对人情世故不太在意，更注重事情的本质和结果。"}
info_str="玩家李磊，小明，小美，小王四个人一起玩炸金花，玩家李磊选择作弊。"
god_data=[character,info_str]
print(interact(god_data))
'''