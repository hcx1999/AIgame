from god import GodAgent
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    try:
        god = GodAgent()

        # 加载世界观设定
        world_background = "在一个被黑暗魔法笼罩的奇幻世界，玩家是最后的龙裔战士..."

        # 配置初始状态
        god.update_world_state(
            background=world_background
        )

        logger.info("游戏开始")
        
        while True:
            try:
                narrative, options, new_role = god.generate_narrative()

                print("## 新剧情 ##")
                print(narrative)
                if new_role:
                    print("\n## 新角色 ##")
                    print(f"你遇到了{new_role[0]}!")
                print("\n## 玩家选项 ##")
                for i, opt in enumerate(options, 1):
                    print(f"{i}. {opt}")
                print()

                # 更新玩家行动
                try:
                    user_input = input("请选择 (输入数字): ")
                    if not user_input.strip():
                        print("输入不能为空，请重新选择")
                        continue
                        
                    player_choice = int(user_input)
                    
                    if player_choice < 1 or player_choice > len(options):
                        print(f"选择超出范围，请输入 1-{len(options)} 之间的数字")
                        continue
                        
                    info = (options[player_choice - 1], [])
                    god.update_information(info)
                    
                except ValueError:
                    print("请输入有效的数字")
                    continue
                except KeyboardInterrupt:
                    print("\n游戏已退出")
                    break
                except Exception as choice_error:
                    logger.error(f"处理玩家选择时出错: {str(choice_error)}")
                    print("处理选择时出现错误，请重试")
                    continue
                    
            except Exception as game_error:
                logger.error(f"游戏循环中出现错误: {str(game_error)}")
                print("游戏出现错误，正在尝试恢复...")
                continue
                
    except Exception as e:
        logger.error(f"游戏初始化失败: {str(e)}")
        print(f"游戏启动失败: {str(e)}")

if __name__ == "__main__":
    main()
