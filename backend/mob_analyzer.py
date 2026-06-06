"""
backend/mob_analyzer.py
MOB‑suite 集成模块（修复 low_memory 冲突 + 无耐药基因时跳过 MOB）
"""
import subprocess
import json
import pandas as pd
from pathlib import Path
from typing import List, Optional, Dict, Any

IMAGE = "mobsuite:latest"
KB_PATH = Path(__file__).parent.parent / "data" / "gene_plasmid_kb.json"


def _load_kb():
    if KB_PATH.exists():
        with open(KB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


_COL_ALIASES = {
    "contig_id":   ["contig_id", "contig", "#contig", "seqid"],
    "rep_type":    ["rep_type(s)", "rep_type", "replicon_type"],
    "relaxase_type": ["relaxase_type(s)", "relaxase_type", "relaxase"],
    "mobility":    ["predicted_mobility", "mobility", "mobilizable"],
    "mpf_type":    ["mpf_type", "mpf_type(s)", "mpf"],
    "size":        ["size", "length"],
    "sample_id":   ["sample_id", "sample"],
}

def _find_col(df, target):
    for alias in _COL_ALIASES.get(target, [target]):
        if alias in df.columns:
            return alias
    for col in df.columns:
        if col.lower() == target.lower():
            return col
    return None


def run_mob_typer(fasta_path: str, output_dir: str) -> str:
    fasta = Path(fasta_path).resolve()
    out = Path(output_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)

    container_out = "/output/mobtyper_results.txt"
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{fasta.parent}:/input:ro",
        "-v", f"{out}:/output",
        IMAGE,
        "mob_typer",
        "-i", f"/input/{fasta.name}",
        "-o", container_out,
        "-s", fasta.stem,
        "-x",
        "-n", "4",
    ]
    print(f"MOB‑suite: {' '.join(cmd)}")
    subprocess.run(cmd, check=True, capture_output=True, text=True)
    return str(out / "mobtyper_results.txt")


def parse_mob_results(result_file: str,
                      target_contigs: Optional[List[str]] = None) -> pd.DataFrame:
    result_path = Path(result_file)
    if not result_path.exists():
        raise FileNotFoundError(f"结果文件不存在: {result_path}")

    # ⚡ 关键修复：去掉 low_memory=False（默认使用 c 引擎，完全兼容）
    df = pd.read_csv(result_path, sep="\t", comment="#")
    print(f"[MOB] 列名: {list(df.columns)}")

    mapped = {}
    for t in ["contig_id", "rep_type", "relaxase_type", "mobility", "mpf_type", "size", "sample_id"]:
        found = _find_col(df, t)
        if found:
            mapped[found] = t

    if "contig_id" not in mapped.values():
        print(f"[MOB] ❌ 未能匹配 contig_id，实际列名: {list(df.columns)}")
        return pd.DataFrame(columns=["contig_id", "rep_type", "relaxase_type", "mobility", "mpf_type", "size", "sample_id"])

    df = df[list(mapped.keys())].rename(columns=mapped)
    df.fillna({
        "rep_type": "unknown", "relaxase_type": "unknown",
        "mobility": "unknown", "mpf_type": "unknown"
    }, inplace=True)

    if target_contigs:
        df = df[df["contig_id"].isin(target_contigs)]

    return df


def analyze_mobility(contig_fasta_path: str,
                     target_contigs: Optional[List[str]] = None) -> pd.DataFrame:
    fasta = Path(contig_fasta_path)
    out_dir = fasta.parent / f"{fasta.stem}_mobsuite"
    out_dir.mkdir(exist_ok=True)
    result_file = run_mob_typer(str(fasta), str(out_dir))
    df = parse_mob_results(result_file, target_contigs)
    return df


def merge_amr_mob_results(amr_json_path: str, mob_df: pd.DataFrame,
                          sample_id: str = "sample") -> Dict[str, Any]:
    with open(amr_json_path, "r", encoding="utf-8") as f:
        amr_genes = json.load(f)

    kb = _load_kb()

    contig_info = {}
    if not mob_df.empty:
        for _, row in mob_df.iterrows():
            contig_info[row["contig_id"]] = {
                "rep_type": row.get("rep_type", "unknown"),
                "mobility": row.get("mobility", "unknown"),
                "relaxase": row.get("relaxase_type", "unknown"),
            }

    merged_genes = []
    for gene in amr_genes:
        contig = gene.get("contig_id", "")
        plasmid = contig_info.get(contig, {})
        gene_name = gene["gene_symbol"]
        kb_entry = kb.get(gene_name, {})

        plasmid_source = "MOB‑suite" if plasmid else "知识库"
        plasmid_name = plasmid.get("rep_type") or kb_entry.get("plasmid", "unknown")
        mobility = plasmid.get("mobility") or kb_entry.get("mobility", "unknown")

        evidence = [
            {"step": 1, "title": "基因检出", "tool": "AMRFinderPlus",
             "result": f"{gene_name} (一致性 {gene.get('identity_pct','')}%)",
             "confidence": "High" if float(gene.get("identity_pct", 0)) > 90 else "Medium"},
        ]

        if plasmid_name and plasmid_name != "unknown":
            evidence.append({
                "step": 2, "title": "质粒定位",
                "tool": plasmid_source if plasmid else "知识库",
                "result": f"位于 {plasmid_name} 型质粒" + (f" (contig {contig})" if contig else ""),
                "confidence": "High" if plasmid else "Medium",
            })
        else:
            evidence.append({
                "step": 2, "title": "质粒定位", "tool": "知识库",
                "result": "暂未获得质粒信息",
                "confidence": "Low",
            })

        if mobility and mobility != "unknown":
            evidence.append({
                "step": 3, "title": "移动性判定",
                "tool": plasmid_source if plasmid else "知识库",
                "result": mobility,
                "confidence": "High" if plasmid else "Medium",
            })
        else:
            evidence.append({
                "step": 3, "title": "移动性判定", "tool": "知识库",
                "result": "未知",
                "confidence": "Low",
            })

        risk_text = f"风险：{gene.get('class','')}耐药"
        if mobility == "conjugative":
            risk_text += "，质粒可接合转移，传播风险极高"
        elif mobility == "mobilizable":
            risk_text += "，质粒可被辅助转移，中等传播风险"
        else:
            risk_text += "，传播风险较低或未知"

        evidence.append({
            "step": 4, "title": "综合结论", "tool": "规则引擎",
            "result": risk_text,
            "confidence": "High" if mobility in ("conjugative","mobilizable") else "Medium",
        })

        merged_genes.append({
            "gene_name": gene_name, "contig": contig,
            "drug_class": gene.get("class", ""),
            "plasmid_info": {
                "rep_type": plasmid_name,
                "mobility": mobility,
                "relaxase": plasmid.get("relaxase", "unknown"),
            },
            "evidence_chain": evidence,
        })

    return {
        "sample_id": sample_id,
        "analysis_date": pd.Timestamp.now().strftime("%Y-%m-%d %H:%M"),
        "tools": {"amrfinderplus": "4.2.7", "mob_suite": "3.1.9"},
        "genes": merged_genes,
    }


def upgrade_risk_with_mobility(risk_dict, mob_df, amr_genes=None):
    if mob_df.empty and not amr_genes:
        return risk_dict

    mob_map = dict(zip(mob_df["contig_id"], mob_df["mobility"])) if not mob_df.empty else {}

    gene_class_map = {}
    if amr_genes:
        for g in amr_genes:
            gene_class_map[g["gene_symbol"]] = g.get("class", "")

    for d in risk_dict.get("details", []):
        gene = d.get("gene", "")
        contig = d.get("scope", "")
        mobility = mob_map.get(contig, "unknown")

        if mobility == "conjugative":
            drug_class = gene_class_map.get(gene, "")
            if "BETA-LACTAM" in drug_class and any(
                sub in d.get("phenotype", "") for sub in ["碳青霉烯", "cephalosporin", "头孢"]
            ):
                d["level"] = "极高"
                d["note"] = (d.get("note", "") + "；因位于接合质粒且为碳青霉烯/超广谱β内酰胺酶，风险强制升级为极高").strip("；")
                continue

        if mobility == "mobilizable":
            lvl_order = {"待完善":0, "低":1, "中":2, "高":3, "极高":4}
            cur = lvl_order.get(d.get("level", "待完善"), 0)
            if cur < 4:
                new_lvl = ["待完善","低","中","高","极高"][cur+1]
                d["level"] = new_lvl
                d["note"] = (d.get("note", "") + f"；因位于可移动质粒，风险升级至{new_lvl}").strip("；")

    score = 0
    for d in risk_dict.get("details", []):
        lv = d.get("level", "待完善")
        if lv == "极高": score += 10
        elif lv == "高": score += 5
        elif lv == "中": score += 2
    if score >= 15: overall = "极高"
    elif score >= 8: overall = "高"
    elif score >= 3: overall = "中"
    else: overall = "低"
    risk_dict["risk_level"] = overall
    risk_dict["summary"] = f"共检测到 {len(risk_dict.get('details',[]))} 个耐药基因，综合风险（含质粒传播力修正）：{overall}"
    return risk_dict