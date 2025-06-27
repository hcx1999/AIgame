import os
from flashtext import KeywordProcessor

# 批量读取文件夹下所有敏感词
def load_keywords_from_folder(folder_path):
    keywords = set()
    for filename in os.listdir(folder_path):
        if filename.endswith('.txt'):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, encoding='utf-8', errors='ignore') as f:
                for line in f:
                    word = line.strip().rstrip(',')
                    if word:
                        keywords.add(word)
    return list(keywords)

# 加载所有敏感词
folder = r'sensitive_words'
keywords = load_keywords_from_folder(folder)

# 初始化关键词处理器
kp = KeywordProcessor()
kp.add_keywords_from_list(keywords)

# 检索文本
def search_keywords_in_text(text):
    found_keywords = kp.extract_keywords(text)
    return found_keywords