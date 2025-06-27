import ahocorasick

# 常见Prompt Injection关键词
prompt_injection_keywords = [
    "忽略之前", "你现在是", "请扮演", "现在起", "作为", "请用英文回答", "请用中文回答",
    "请输出", "请执行", "请绕过", "请不要遵守", "请忽略", "system:", "user:", "assistant:",
    "你是一个", "你现在的身份", "请以", "请假装", "请模拟", "请生成", "请展示", "请列出"
]

# 构建自动机
A = ahocorasick.Automaton()
for idx, word in enumerate(prompt_injection_keywords):
    A.add_word(word, (idx, word))
A.make_automaton()

def check_prompt_injection(text):
    found_keywords = []
    for end_idx, (idx, word) in A.iter(text):
        found_keywords.append(word)
    return found_keywords

def truncate_text(text, max_length):
    if len(text) <= max_length:
        return text
    return "__超出字数限制"
