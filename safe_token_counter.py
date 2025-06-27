from typing import List
from camel.messages import OpenAIMessage
from camel.utils import BaseTokenCounter

class SimpleTokenCounter(BaseTokenCounter):
    def decode(self, token_ids: List[int]) -> str:
        return ' '.join([str(id) for id in token_ids])

    def encode(self, text: str) -> List[int]:
        return [ord(char) for char in text]

    def count_tokens_from_messages(self, messages: List[OpenAIMessage]) -> int:
        total_tokens = 0
        for message in messages:
            total_tokens += self.count_tokens(message["content"])
        return total_tokens

    def count_tokens(self, text: str) -> int:
        return len(text.split())  # 简单按空格分词