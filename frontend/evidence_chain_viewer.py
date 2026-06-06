"""
frontend/evidence_chain_viewer.py
流动式证据链组件
"""
import streamlit as st

def _mobility_style(mobility: str):
    """返回 (边框颜色, 徽章颜色, 说明文字)"""
    m = mobility.lower()
    if "conjugative" in m:
        return "#dc3545", "高传播潜力"
    elif "mobilizable" in m:
        return "#fd7e14", "中等传播潜力"
    elif "non-mobilizable" in m:
        return "#28a745", "传播潜力低"
    else:
        return "#6c757d", "待确认"

def _confidence_color(conf: str):
    c = conf.lower()
    if c == "high": return "#28a745"
    elif c == "medium": return "#ffc107"
    return "#6c757d"

def _badge(conf: str):
    color = _confidence_color(conf)
    return f'<span style="background:{color}20;color:{color};padding:2px 8px;border-radius:10px;font-size:0.75em;margin-left:6px;">{conf.upper()}</span>'

def _step_card(step: int, title: str, tool: str, result: str, confidence: str, border_color: str = None):
    if border_color is None:
        border_color = _confidence_color(confidence)
    html = f"""
    <div style="border-left:5px solid {border_color}; margin-bottom:12px; padding:12px 16px; background:#fff; border-radius:8px; box-shadow:0 1px 4px rgba(0,0,0,0.05);">
        <div style="display:flex; align-items:center; margin-bottom:6px;">
            <span style="font-size:1.4em; font-weight:bold; color:{border_color}; margin-right:10px;">{step:02d}</span>
            <span style="font-size:1.1em; font-weight:600;">{title}</span>
            {_badge(confidence)}
        </div>
        <div style="color:#888; font-size:0.8em; margin-bottom:4px;">🔬 {tool}</div>
        <div style="color:#333; font-size:0.95em;">{result}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def render_evidence_chain(gene_data: dict):
    chain = gene_data.get("evidence_chain", [])
    if not chain:
        st.info("暂无证据链数据")
        return

    gene_name = gene_data.get("gene_name", "未知")
    drug_class = gene_data.get("drug_class", "")
    st.markdown(f"### 🧬 {gene_name} ({drug_class})")

    for idx, item in enumerate(chain):
        step = item.get("step", idx+1)
        title = item.get("title", "")
        tool = item.get("tool", "")
        result = item.get("result", "")
        conf = item.get("confidence", "Medium")

        # 移动性判定（step 3）特殊颜色
        if title == "移动性判定":
            mobility_val = result.strip()
            border, label = _mobility_style(mobility_val)
            # 替换 result 为带说明的文字
            result = f"{mobility_val}（{label}）"
            badge_conf = "High" if "conjugative" in mobility_val.lower() else conf
            _step_card(step, title, tool, result, badge_conf, border_color=border)
        elif title == "综合结论":
            # 默认展开
            with st.expander(f"✅ 结论: {title}", expanded=True):
                risk_level = gene_data.get("plasmid_info", {}).get("mobility", "")
                if "conjugative" in risk_level.lower() or "极高" in result:
                    st.error(f"**{tool}**\n\n{result}")
                elif "mobilizable" in risk_level.lower() or "高" in result:
                    st.warning(f"**{tool}**\n\n{result}")
                else:
                    st.success(f"**{tool}**\n\n{result}")
        else:
            _step_card(step, title, tool, result, conf)

    st.caption("💡 证据链基于 AMRFinderPlus 注释与结构化知识库推断（MOB‑suite 质粒分析模块已部署，待集成验证）")