"""
ai/api_client.py – 强制外部 API
"""
import json
import requests
from pathlib import Path
from .prompts import CLINICAL_ADVICE

_session = requests.Session()
_session.trust_env = False

def query_api(prompt: str, api_url: str, api_key: str, model: str, timeout=60):
    if not api_url or not api_key or not model:
        raise RuntimeError("API 配置不完整")
    url = api_url.strip().rstrip("/")
    if not url.endswith("/chat/completions"):
        url += "/v1/chat/completions" if "/v1" in url else "/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key.strip()}", "Content-Type": "application/json"}
    payload = {
        "model": model.strip(),
        "messages": [
            {"role": "system", "content": "你是临床微生物学专家，请直接给出最终建议。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 2048
    }
    r = _session.post(url, json=payload, headers=headers, timeout=timeout)
    if r.status_code != 200:
        raise RuntimeError(f"API 错误 {r.status_code}: {r.text[:200]}")
    data = r.json()
    return data["choices"][0]["message"]["content"].strip()

def generate_clinical_advice(amr_json_path, use_api=True, api_url="", api_key="", api_model="", output_txt=None):
    with open(amr_json_path, "r", encoding="utf-8") as f:
        genes = json.load(f)
    if not genes:
        return "✅ 未检测到获得性耐药基因，该菌株可能为敏感株。", None
    genes_list = "\n".join([
        f"- {g.get('gene_symbol', '?')}（{g.get('class', '')}/{g.get('subclass', '')}，位置：{g.get('scope', '?')}）"
        for g in genes
    ])
    prompt = CLINICAL_ADVICE.format(genes_list=genes_list)
    try:
        advice = query_api(prompt, api_url, api_key, api_model)
        if output_txt:
            Path(output_txt).parent.mkdir(parents=True, exist_ok=True)
            with open(output_txt, "w", encoding="utf-8") as f:
                f.write(advice)
        return advice, None
    except Exception as e:
        return None, str(e)