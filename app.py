"""
app.py - ResGuard 最终版
- 侧边栏保留“本地/外部”选择，但实际统一走外部 API
- 移除演示案例功能
- 证据链改为可折叠区域
"""
import streamlit as st
from pathlib import Path
import tempfile
import json
import pandas as pd

from backend.amr_pipeline import run_amrfinder
from backend.rule_engine import RuleEngine
from backend.network_builder import build_network
from ai.api_client import generate_clinical_advice
from report.pdf_generator import generate_pdf_report
from frontend.evidence_chain_viewer import render_evidence_chain

# ========== 常量 ==========
API_CONFIG_FILE = Path(__file__).parent / "data" / "api_config.json"

st.set_page_config(page_title="ResGuard 耐药风险哨兵", layout="wide")
st.title("🛡️ ResGuard — 耐药基因组风险哨兵")

# ========== session_state 初始化 ==========
for key, default in [
    ("analysis_done", False),
    ("amr_json", None),
    ("risk", None),
    ("genes", None),
    ("ai_advice", None),
    ("ai_error", None),
    ("file_path", None),
]:
    if key not in st.session_state:
        st.session_state[key] = default

# ========== 工具函数 ==========
def load_api_config():
    if API_CONFIG_FILE.exists():
        try:
            with open(API_CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"api_url": "", "api_key": "", "api_model": ""}

def save_api_config(config):
    API_CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(API_CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def fallback_advice(risk_dict):
    genes = [d.get("gene", "") for d in risk_dict.get("details", []) if d.get("gene")]
    level = risk_dict.get("risk_level", "未知")
    phenotypes = list(set([d.get("phenotype", "") for d in risk_dict.get("details", []) if d.get("phenotype")]))
    parts = [f"### 规则模板解读\n\n该菌株综合风险等级：**{level}**。"]
    if genes:
        parts.append(f"检测到以下耐药相关基因：{'、'.join(genes)}。")
    if phenotypes:
        parts.append(f"可能耐药表型：{'、'.join(phenotypes)}。")
    parts.append("建议根据药敏试验结果选择有效抗生素。如为多重耐药株，需注意隔离和消毒措施。")
    parts.append("*（本解读由规则引擎自动生成，仅供参考，不可作为临床用药依据。）*")
    return "\n\n".join(parts)


# ============================================================
#  侧边栏（保留本地/外部选项，但实际全走外部 API）
# ============================================================
with st.sidebar:
    st.subheader("⚙️ AI 设置")

    # 保留选项，但不影响实际行为
    ai_mode = st.radio(
        "AI 引擎",
        ["本地 Ollama（离线）", "外部 API（在线）"],
        index=0,
        help="当前版本统一使用外部 API"
    )
    # 无论选什么，都用外部 API
    use_api = True

    saved = load_api_config()
    api_url = st.text_input("API 地址", value=saved.get("api_url", ""),
                            placeholder="https://api.openai.com/v1/chat/completions")
    api_key = st.text_input("API Key", value=saved.get("api_key", ""),
                            type="password", placeholder="sk-...")
    api_model = st.text_input("模型名", value=saved.get("api_model", ""),
                              placeholder="gpt-4o / deepseek-chat / qwen-turbo")
    new_config = {"api_url": api_url, "api_key": api_key, "api_model": api_model}
    if new_config != saved:
        save_api_config(new_config)


# ============================================================
#  主界面
# ============================================================
uploaded_file = st.file_uploader("选择基因组文件", type=["fna", "fasta", "fa"])
if uploaded_file is not None:
    temp_dir = Path(tempfile.gettempdir()) / "resguard_uploads"
    temp_dir.mkdir(exist_ok=True)
    file_path = temp_dir / uploaded_file.name
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    st.session_state.file_path = str(file_path)
    st.success(f"文件上传成功：{uploaded_file.name}")

    if not st.session_state.analysis_done:
        if st.button("🔬 开始分析", type="primary"):
            with st.spinner("正在运行 AMRFinderPlus 耐药基因检测（Docker）..."):
                try:
                    amr_json = run_amrfinder(str(file_path))
                    st.session_state.amr_json = amr_json
                except Exception as e:
                    st.error(f"分析失败：{e}")
                    st.stop()

            with st.spinner("进行风险评级..."):
                engine = RuleEngine()
                with open(amr_json, "r", encoding="utf-8") as f:
                    genes = json.load(f)
                mob_df = None
                mob_csv = Path(file_path).parent / "amrfinder_results" / f"{Path(file_path).stem}_mobsuite.csv"
                if mob_csv.exists():
                    try:
                        mob_df = pd.read_csv(mob_csv)
                    except Exception:
                        pass
                risk = engine.assess(genes, mob_df=mob_df)
                st.session_state.risk = risk
                st.session_state.genes = genes
                st.session_state.analysis_done = True
                st.session_state.ai_advice = None
                st.session_state.ai_error = None
            st.rerun()


# ============================================================
#  结果展示
# ============================================================
if st.session_state.analysis_done:
    st.success("分析完成！")

    amr_json = st.session_state.amr_json
    risk = st.session_state.risk

    if st.button("🔄 重新分析", type="secondary"):
        for k in ["analysis_done", "amr_json", "risk", "genes", "ai_advice", "ai_error", "file_path"]:
            st.session_state[k] = None if k != "analysis_done" else False
        st.rerun()

    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("📊 风险评级结果")
        level_color = {"极高": "red", "高": "orange", "中": "gold", "低": "green", "未知": "grey"}
        level = risk.get("risk_level", "未知") if risk else "未知"
        st.markdown(f"### 综合风险：<span style='color:{level_color.get(level, 'black')};'>{level}</span>",
                    unsafe_allow_html=True)
        st.write(risk.get("summary", "") if risk else "")

        if risk:
            st.markdown("### 检测到的耐药基因")
            detail_data = []
            for d in risk.get("details", []):
                detail_data.append({
                    "基因": d.get("gene", ""),
                    "表型": d.get("phenotype", ""),
                    "风险等级": d.get("level", ""),
                    "说明": d.get("note", ""),
                    "位置": d.get("scope", "")
                })
            st.dataframe(detail_data, use_container_width=True)

    with col2:
        st.subheader("🔗 耐药传播风险网络图")
        if amr_json and Path(amr_json).exists():
            try:
                mob_csv_path = Path(st.session_state.file_path).parent / "amrfinder_results" / f"{Path(st.session_state.file_path).stem}_mobsuite.csv"
                if not mob_csv_path.exists():
                    mob_csv_path = None
                net_html = build_network(amr_json, mob_csv_path)
                with open(net_html, "r", encoding="utf-8") as f:
                    html_content = f.read()
                st.components.v1.html(html_content, height=600)
            except Exception as e:
                st.warning(f"网络图生成失败：{e}")

    # ---- AI 解读（统一走外部 API）----
    st.markdown("---")
    st.subheader("🤖 AI 临床用药建议")

    if st.button("🤖 生成 AI 解读", type="secondary"):
        with st.spinner("AI 正在生成解读..."):
            try:
                if not Path(amr_json).exists():
                    st.error("分析结果文件丢失")
                else:
                    advice, error = generate_clinical_advice(
                        amr_json,
                        use_api=True,                 # 强制外部 API
                        api_url=api_url,
                        api_key=api_key,
                        api_model=api_model
                    )
                    if error:
                        st.warning(f"AI 调用失败（{error}），自动切换至规则模板。")
                        advice = fallback_advice(risk)
                    elif not advice or len(advice.strip()) < 30:
                        st.warning("AI 返回内容过短，自动切换至规则模板。")
                        advice = fallback_advice(risk)
                    st.session_state.ai_advice = advice
                    st.session_state.ai_error = None
            except Exception as e:
                st.warning(f"AI 调用异常（{e}），自动切换至规则模板。")
                st.session_state.ai_advice = fallback_advice(risk)
                st.session_state.ai_error = None
        st.rerun()

    if st.session_state.ai_advice:
        st.success("AI 解读已生成")
        st.markdown(st.session_state.ai_advice)
    elif st.session_state.ai_error:
        st.error(f"AI 调用失败：{st.session_state.ai_error}")
        st.info("系统已自动使用规则模板解读。")

    # ---- 传播证据链（可折叠） ----
    st.markdown("---")
    with st.expander("🔎 传播证据链（点击展开）", expanded=False):
        merged_json_path = Path(st.session_state.file_path).parent / "amrfinder_results" / f"{Path(st.session_state.file_path).stem}_merged_report.json"
        if merged_json_path.exists():
            try:
                with open(merged_json_path, "r", encoding="utf-8") as f:
                    merged_report = json.load(f)
                for gene_data in merged_report.get("genes", []):
                    render_evidence_chain(gene_data)
            except Exception as e:
                st.error(f"证据链加载失败: {e}")
        else:
            st.info("尚未生成传播证据链报告（需 MOB‑suite 分析完成）")

    # ---- PDF 报告 ----
    st.markdown("---")
    st.subheader("📄 生成 PDF 报告")
    if st.button("生成并下载 PDF"):
        try:
            pdf_dir = Path(tempfile.gettempdir()) / "resguard_reports"
            pdf_dir.mkdir(exist_ok=True)
            base_name = Path(st.session_state.file_path).stem
            pdf_path = pdf_dir / f"{base_name}_report.pdf"

            evidence_text = ""
            merged_json_source = Path(st.session_state.file_path).parent / "amrfinder_results" / f"{base_name}_merged_report.json"
            if merged_json_source.exists():
                with open(merged_json_source, "r", encoding="utf-8") as f:
                    merged_report = json.load(f)
                for gene_data in merged_report.get("genes", []):
                    evidence_text += f"**{gene_data.get('gene_name', '')}** ({gene_data.get('drug_class', '')})\n"
                    for step in gene_data.get("evidence_chain", []):
                        evidence_text += f"  {step['step']:02d}. {step['title']} [{step['confidence']}]: {step['result']}\n"
                    evidence_text += "\n"

            if Path(amr_json).exists():
                from report.pdf_generator import generate_pdf_report as pdf_gen
                pdf_gen(
                    amr_json,
                    risk,
                    str(pdf_path),
                    ai_text=st.session_state.get("ai_advice"),
                    evidence_text=evidence_text
                )
                with open(pdf_path, "rb") as f:
                    st.download_button("下载报告", f, file_name=pdf_path.name, mime="application/pdf")
            else:
                st.error("缺少分析数据")
        except Exception as e:
            st.error(f"PDF 生成失败：{e}")