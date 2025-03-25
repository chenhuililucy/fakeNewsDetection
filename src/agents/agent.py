import os
import http.client
import json
from langchain.chat_models import ChatOpenAI

class Agent:
    def __init__(self):
        self.short_term_memory = []
        self.long_term_memory = {}

    def remember_short_term(self, item):
        self.short_term_memory.append(item)

    def remember_long_term(self, key, value):
        self.long_term_memory[key] = value

    def get_short_term_memory(self):
        return self.short_term_memory

    def get_long_term_memory(self, key):
        return self.long_term_memory.get(key, None)

    def clear_short_term_memory(self):
        self.short_term_memory = []

    def clear_long_term_memory(self):
        self.long_term_memory = {}
