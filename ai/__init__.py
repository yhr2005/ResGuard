"""
ai/__init__.py
ResGuard AI 模块 — 负责本地 Ollama 模型管理 + 外部 API + 临床解读
"""
from .model_manager import ModelManager
from .api_client import generate_clinical_advice