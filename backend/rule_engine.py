"""
backend/rule_engine.py
规则引擎：根据基因匹配规则库 → 输出风险等级
新增：接受 MOB‑suite 结果，自动升级可接合质粒上的耐药基因风险
"""
import json
from pathlib import Path
from typing import List, Dict
from backend.mob_analyzer import upgrade_risk_with_mobility


class RuleEngine:
    def __init__(self, rules_path: Path = None):
        if rules_path is None:
            rules_path = Path(__file__).parent.parent / "data" / "rules" / "amr_rules.json"
        if not rules_path.exists():
            raise FileNotFoundError(f"规则文件缺失：{rules_path}")
        with open(rules_path, "r", encoding="utf-8") as f:
            self.rules = json.load(f)

    def assess(self, amr_genes: List[Dict], mob_df=None) -> Dict:
        """
        amr_genes: AMRFinder 输出的基因列表（每个包含 gene_symbol 等）
        mob_df: MOB‑suite 结果 DataFrame，可选。如果提供，会自动升级 conujgative 质粒上的基因风险。
        返回: { "risk_level": "极高"/"高"/"中"/"低", "details": [...], "summary": str }
        """
        risk_score = 0
        findings = []
        for gene in amr_genes:
            symbol = gene.get("gene_symbol", "")
            matched = None
            for rule in self.rules.get("genes", []):
                if rule["gene"].upper() == symbol.upper():
                    matched = rule
                    break
            if matched:
                level = matched["level"]
                if level == "极高":
                    risk_score += 10
                elif level == "高":
                    risk_score += 5
                elif level == "中":
                    risk_score += 2
                findings.append({
                    "gene": symbol,
                    "phenotype": matched.get("phenotype", "未知"),
                    "level": level,
                    "note": matched.get("note", ""),
                    "color": matched.get("color", "red"),
                    "scope": gene.get("scope", ""),
                })
            else:
                findings.append({
                    "gene": symbol,
                    "phenotype": "待评估",
                    "level": "待完善",
                    "note": "该基因暂未收录，需人工复核",
                    "color": "grey",
                    "scope": gene.get("scope", ""),
                })

        if risk_score >= 15:
            overall = "极高"
        elif risk_score >= 8:
            overall = "高"
        elif risk_score >= 3:
            overall = "中"
        else:
            overall = "低"

        risk_dict = {
            "risk_level": overall,
            "score": risk_score,
            "details": findings,
            "summary": f"共检测到 {len(findings)} 个耐药基因，综合风险等级：{overall}"
        }

        # ---- 如果提供了 MOB 数据，则进行风险升级 ----
        if mob_df is not None and not mob_df.empty:
            risk_dict = upgrade_risk_with_mobility(risk_dict, mob_df)

        return risk_dict