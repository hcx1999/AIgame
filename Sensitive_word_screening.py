import os
import sys
from flashtext import KeywordProcessor

def resource_path(relative_path):
    """兼容 PyInstaller 打包路径"""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.abspath(relative_path)

# 批量读取文件夹下所有敏感词
def load_keywords_from_folder(folder_path):
    keywords = set()
    absolute_folder_path = resource_path(folder_path)
    for filename in os.listdir(absolute_folder_path):
        if filename.endswith('.txt'):
            file_path = os.path.join(absolute_folder_path, filename)
            with open(file_path, encoding='utf-8', errors='ignore') as f:
                for line in f:
                    word = line.strip().rstrip(',')  # 去除多余空格与末尾逗号
                    if word:
                        keywords.add(word)
    return list(keywords)

# 加载所有敏感词
folder = 'sensitive_words'
keywords = load_keywords_from_folder(folder)

# 初始化关键词处理器
kp = KeywordProcessor()
kp.add_keywords_from_list(keywords)

# 检索文本
def search_keywords_in_text(text):
    return kp.extract_keywords(text)
