# -*- coding: utf-8 -*-
"""内置编程助手引擎"""
import json
import re
from server.services.ollama import chat as ollama_chat


class CodeEngine:
    def __init__(self):
        self.default_model = "qwen2.5:1.5b"
        self.code_model = "deepseek-coder:6.7b"

    def complete_code(self, code, language="python"):
        prompt = f"You are a senior {language} developer. Complete the following code, only output the completed code, no explanation:\n\n```{language}\n{code}\n```"
        result = ollama_chat([{"role": "user", "content": prompt}], model=self.code_model, timeout=30)
        return {"ok": True, "completion": result, "language": language}

    def find_bugs(self, code, language="python"):
        prompt = f"You are a senior {language} code reviewer. Find all bugs and potential issues in this code:\n\n```{language}\n{code}\n```\n\nOutput format:\n1. Critical issues\n2. Logic errors\n3. Performance issues\n4. Security concerns\n5. Improvement suggestions"
        result = ollama_chat([{"role": "user", "content": prompt}], model=self.code_model, timeout=60)
        return {"ok": True, "analysis": result, "language": language}

    def architecture_review(self, description, tech_stack=""):
        prompt = f"You are a senior system architect. Review this project:\n\nDescription: {description}\nTech stack: {tech_stack or 'Not specified'}\n\nAnalyze:\n1. Recommended architecture\n2. Tech stack suggestions\n3. Potential risks\n4. Scalability considerations\n5. Deployment plan"
        result = ollama_chat([{"role": "user", "content": prompt}], model=self.default_model, timeout=60)
        return {"ok": True, "review": result}

    def code_review(self, code, language="python"):
        prompt = f"You are a senior {language} code reviewer. Review this code:\n\n```{language}\n{code}\n```\n\nRate (1-10) and suggest improvements for:\n1. Readability\n2. Performance\n3. Security\n4. Maintainability\n5. Best practices"
        result = ollama_chat([{"role": "user", "content": prompt}], model=self.code_model, timeout=60)
        return {"ok": True, "review": result, "language": language}

    def refactor_suggestion(self, code, language="python"):
        prompt = f"You are a senior {language} developer. Suggest refactoring for this code and output the refactored version:\n\n```{language}\n{code}\n```\n\nOutput:\n## Issues\n## Refactoring Plan\n## Refactored Code\n```{language}\n```"
        result = ollama_chat([{"role": "user", "content": prompt}], model=self.code_model, timeout=60)
        return {"ok": True, "refactor": result, "language": language}

    def generate_tests(self, code, language="python"):
        prompt = f"You are a senior test engineer. Generate complete test cases for this code:\n\n```{language}\n{code}\n```\n\nInclude:\n1. Unit tests\n2. Edge cases\n3. Exception tests\nOutput runnable test code."
        result = ollama_chat([{"role": "user", "content": prompt}], model=self.code_model, timeout=60)
        return {"ok": True, "tests": result, "language": language}

    def explain_code(self, code, language="python"):
        prompt = f"You are a senior {language} developer. Explain this code in simple terms:\n\n```{language}\n{code}\n```\n\nExplain:\n1. Overall function\n2. Key logic\n3. Techniques/patterns used\n4. Possible improvements"
        result = ollama_chat([{"role": "user", "content": prompt}], model=self.code_model, timeout=60)
        return {"ok": True, "explanation": result, "language": language}


code_engine = CodeEngine()