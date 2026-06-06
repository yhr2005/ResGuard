"""
ai/model_manager.py
Ollama 模型生命周期管理（适配 qwen3.5:4b-q4_K_M）
"""
import subprocess
import requests
from pathlib import Path

OLLAMA_URL = "http://localhost:11434"
OLLAMA_EXE = str(Path.home() / "AppData" / "Local" / "Programs" / "Ollama" / "ollama.exe")

class ModelManager:
    def __init__(self, model_name: str = "qwen3.5:4b-q4_K_M"):
        self.model_name = model_name

    def _run_cmd(self, *args, timeout=10):
        try:
            proc = subprocess.run(
                [OLLAMA_EXE] + list(args),
                capture_output=True, text=True, timeout=timeout,
                creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, "CREATE_NO_WINDOW") else 0
            )
            return proc.returncode == 0, proc.stdout.strip()
        except:
            return False, ""

    def is_service_running(self):
        ok, _ = self._run_cmd("list", timeout=5)
        return ok

    def is_installed(self):
        ok, out = self._run_cmd("list", timeout=5)
        return ok and self.model_name in out

    def is_loaded(self):
        ok, out = self._run_cmd("ps", timeout=5)
        if not ok:
            return False
        return self.model_name in out.replace(":latest", "")  # 忽略 :latest 后缀

    def load(self, timeout=120):
        s = requests.Session()
        s.trust_env = False
        try:
            r = s.post(f"{OLLAMA_URL}/api/generate", json={
                "model": self.model_name,
                "prompt": "OK",
                "stream": False,
                "options": {"num_predict": 2},
                "keep_alive": -1
            }, timeout=timeout)
            return r.status_code == 200
        except:
            return False

    def unload(self):
        ok, _ = self._run_cmd("stop", self.model_name, timeout=10)
        return ok

    def status_text(self):
        if not self.is_service_running():
            return "⚫ Ollama 服务未运行"
        if self.is_loaded():
            return "🟢 已加载到 GPU"
        if self.is_installed():
            return "🟡 已安装但未加载（点击加载按钮）"
        return "🔴 模型未安装"