import openai
import requests
import os
from datetime import datetime
from PIL import Image
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 配置 SiliconFlow API
try:
    client = openai.OpenAI(
        api_key='sk-qseennfhdprismchczwnkzpohyjmuwgpiaywuclsisgugfvo',
        base_url='https://api.siliconflow.cn/v1'
    )
    logger.info("OpenAI 客户端初始化成功")
except Exception as e:
    logger.error(f"OpenAI 客户端初始化失败: {str(e)}")
    raise

def encode_image_to_base64(image_path):
    """将图片编码为base64格式用于API调用"""
    try:
        if not os.path.exists(image_path):
            logger.error(f"图片文件不存在: {image_path}")
            return None
            
        with open(image_path, "rb") as image_file:
            import base64
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
            logger.info(f"图片编码成功: {image_path}")
            return encoded_string
    except Exception as e:
        logger.error(f"编码图片失败: {str(e)}")
        return None

def resize_image(image_path, max_size=(1024, 1024)):
    """调整图片尺寸以符合 API 要求"""
    try:
        if not os.path.exists(image_path):
            logger.error(f"图片文件不存在: {image_path}")
            return None
            
        with Image.open(image_path) as img:
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            temp_path = f"temp_resized_{timestamp}.jpg"
            
            img.save(temp_path, "JPEG", quality=85)
            logger.info(f"图片尺寸调整成功: {temp_path}")
            return temp_path
            
    except Exception as e:
        logger.error(f"调整图片尺寸失败: {str(e)}")
        return None

def analyze_image_style(image_path):
    """分析图片风格并返回风格描述"""
    try:
        if not os.path.exists(image_path):
            logger.error(f"图片文件不存在: {image_path}")
            return "artistic style, detailed illustration"
            
        with Image.open(image_path) as img:
            # 转换为RGB
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # 获取图像尺寸
            width, height = img.size
            
            # 简单的颜色分析
            sample_points = []
            for x in range(0, width, max(1, width//10)):
                for y in range(0, height, max(1, height//10)):
                    if x < width and y < height:
                        sample_points.append(img.getpixel((x, y)))
            
            if not sample_points:
                return "artistic style, detailed illustration"
            
            # 计算平均颜色
            avg_r = sum(p[0] for p in sample_points) / len(sample_points)
            avg_g = sum(p[1] for p in sample_points) / len(sample_points)
            avg_b = sum(p[2] for p in sample_points) / len(sample_points)
            avg_brightness = (avg_r + avg_g + avg_b) / 3
            
            style_descriptions = []
            
            # 根据亮度判断风格
            if avg_brightness < 80:
                style_descriptions.append("dark and moody atmosphere")
            elif avg_brightness > 180:
                style_descriptions.append("bright and luminous style")
            else:
                style_descriptions.append("balanced lighting")
            
            # 根据颜色偏向判断
            if avg_r > avg_g + 20 and avg_r > avg_b + 20:
                style_descriptions.append("warm red tones")
            elif avg_b > avg_r + 20 and avg_b > avg_g + 20:
                style_descriptions.append("cool blue tones")
            elif avg_g > avg_r + 10 and avg_g > avg_b + 10:
                style_descriptions.append("natural green tones")
            
            # 基于文件名的风格推断
            filename = os.path.basename(image_path).lower()
            if 'paint' in filename or 'art' in filename:
                style_descriptions.append("oil painting style")
            elif 'photo' in filename:
                style_descriptions.append("photographic realism")
            elif 'cartoon' in filename or 'anime' in filename:
                style_descriptions.append("cartoon/anime style")
            elif 'sketch' in filename:
                style_descriptions.append("pencil sketch style")
            elif 'watercolor' in filename:
                style_descriptions.append("watercolor painting style")
            else:
                style_descriptions.append("artistic illustration style")
            
            result = ", ".join(style_descriptions) if style_descriptions else "artistic style, detailed illustration"
            logger.info(f"图片风格分析完成: {result}")
            return result
            
    except Exception as e:
        logger.error(f"风格分析失败，使用默认风格: {str(e)}")
        return "artistic style, detailed illustration, same visual style as reference"

def generate_style_image(prompt, reference_image_path, model="black-forest-labs/FLUX.1-dev"):
    """根据参考图片生成相同风格的图像"""
    try:
        if not prompt or not prompt.strip():
            logger.error("提示词为空")
            return None
            
        if not os.path.exists(reference_image_path):
            logger.error(f"参考图片不存在: {reference_image_path}")
            return None
        
        logger.info(f"分析参考图片: {reference_image_path}")
        
        # 调整图片尺寸
        resized_image_path = resize_image(reference_image_path)
        if not resized_image_path:
            return None
        
        logger.info(f"使用 {model} 生成风格化图像...")
        
        # 分析参考图片的风格特征
        logger.info("正在分析参考图片风格...")
        
        # 根据文件名或简单分析来推断风格类型
        style_hints = analyze_image_style(reference_image_path)
        
        # 构建详细的风格化提示词
        style_prompt = f"{prompt}, {style_hints}, highly detailed, masterpiece quality"
        
        logger.info(f"风格化提示词: {style_prompt}")
        
        # 生成图像
        response = client.images.generate(
            model=model,
            prompt=style_prompt,
            size="1024x1024",
            n=1,
        )
        
        image_url = response.data[0].url
        image_response = requests.get(image_url, timeout=30)
        
        # 清理临时文件
        if os.path.exists(resized_image_path):
            os.remove(resized_image_path)
        
        if image_response.status_code == 200:
            if not os.path.exists("generated_images"):
                os.makedirs("generated_images")
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"generated_images/style_{timestamp}.png"
            
            with open(filename, 'wb') as f:
                f.write(image_response.content)
            
            logger.info(f"风格化图像已保存: {filename}")
            return filename
        else:
            logger.error(f"下载失败: {image_response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"生成失败: {str(e)}")
        return None

def main():
    """主函数"""
    try:
        logger.info("AI 风格化图像生成工具启动")
        print("🎨 AI 风格化图像生成工具")
        print("根据参考图片生成相同风格的新图像")
        print("-" * 40)
        
        # 使用高质量生成模型
        selected_model = "black-forest-labs/FLUX.1-dev"
        print(f"🤖 使用模型: {selected_model} (高质量生成)")
        
        # 检查多个可能的参考图片路径
        possible_paths = [
            "./generated_images/test.png",
            "./test.png", 
            "./sample.png",
            "./image.png",
            "./reference.png",
            "./ref.jpg",
            "./test.jpg"
        ]
        
        print("🔍 搜索参考图片...")
        reference_image = None
        for path in possible_paths:
            if os.path.exists(path):
                reference_image = path
                print(f"✅ 找到参考图片: {path}")
                break
        
        if not reference_image:
            print("❌ 找不到参考图片文件")
            print("💡 请将参考图片命名为以下任一名称并放在当前目录:")
            for path in possible_paths:
                print(f"   - {path}")
            print("\n📝 或者创建一个测试图片...")
            
            # 尝试生成一个测试图片作为参考
            try:
                print("🎨 正在生成测试参考图片...")
                test_response = client.images.generate(
                    model="black-forest-labs/FLUX.1-schnell",
                    prompt="a beautiful landscape painting, oil painting style",
                    size="1024x1024",
                    n=1,
                )
                
                test_url = test_response.data[0].url
                test_img_response = requests.get(test_url, timeout=30)
                
                if test_img_response.status_code == 200:
                    if not os.path.exists("generated_images"):
                        os.makedirs("generated_images")
                    
                    test_path = "./generated_images/test.png"
                    with open(test_path, 'wb') as f:
                        f.write(test_img_response.content)
                    
                    print(f"✅ 测试参考图片已生成: {test_path}")
                    reference_image = test_path
                else:
                    print("❌ 无法生成测试图片")
                    return
                
            except Exception as e:
                logger.error(f"生成测试图片失败: {str(e)}")
                print(f"❌ 生成测试图片失败: {str(e)}")
                return
        
        # 固定的生成描述
        description = "一只小猫"
        
        print(f"🎯 参考: {reference_image}")
        print(f"🎯 描述: {description}")
        print("⏳ 生成中...")
        
        # 生成风格化图像
        result = generate_style_image(description, reference_image, model=selected_model)
        
        if result:
            print(f"🖼️  风格化图像生成完成: {result}")
            print("🎉 任务完成!")
        else:
            print("❌ 生成失败")
            
    except Exception as e:
        logger.error(f"主函数执行失败: {str(e)}")
        print(f"❌ 程序执行失败: {str(e)}")

if __name__ == "__main__":
    main()
