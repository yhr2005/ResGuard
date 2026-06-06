"""
backend/network_builder.py
PyVis 网络图生成（区分质粒/染色体 + 基因颜色恢复）
"""
import json
from pathlib import Path
from pyvis.network import Network

def build_network(amr_json: Path, mob_csv: Path = None, output_html: Path = None):
    with open(amr_json, "r", encoding="utf-8") as f:
        genes = json.load(f)

    # contig -> "plasmid" / "chromosome" / "unknown"
    contig_type = {}
    if mob_csv and Path(mob_csv).exists():
        # 读取 MOB 结果
        from backend.mob_analyzer import parse_mob_results
        try:
            mob_df = parse_mob_results(str(mob_csv))
            for _, row in mob_df.iterrows():
                cid = row["contig_id"]
                mob = row.get("mobility", "unknown")
                if mob != "unknown" and mob != "non-mobilizable":
                    contig_type[cid] = "plasmid"
                else:
                    contig_type[cid] = "chromosome"
        except Exception:
            pass

    # 未在 MOB 中的 contig
    for g in genes:
        cid = g.get("contig_id", "")
        if cid and cid not in contig_type:
            contig_type[cid] = "unknown"

    net = Network(height="600px", width="100%", directed=False)
    net.add_node("菌株基因组", label="菌株基因组", color="#4CAF50", size=30, shape="triangle")

    # Contig 节点
    for cid, ctype in contig_type.items():
        if ctype == "plasmid":
            color = "#FFA500"
            label = f"质粒 {cid}"
        elif ctype == "chromosome":
            color = "#87CEEB"
            label = f"染色体 {cid}"
        else:
            color = "#CCCCCC"
            label = f"Contig {cid}"

        net.add_node(cid, label=label, color=color, size=20, shape="dot")
        net.add_edge("菌株基因组", cid)

    # 加载规则库获取基因颜色
    rules_path = Path(__file__).parent.parent / "data" / "rules" / "amr_rules.json"
    gene_colors = {}
    if rules_path.exists():
        with open(rules_path, "r", encoding="utf-8") as f:
            rules_data = json.load(f)
        for rule in rules_data.get("genes", []):
            gene_colors[rule["gene"].upper()] = rule.get("color", "grey")

    color_map = {"red": "#DC3545", "orange": "#FD7E14", "yellow": "#FFC107", "grey": "#6C757D"}

    # 基因节点
    for g in genes:
        gene_name = g["gene_symbol"]
        contig = g.get("contig_id", "")
        gene_color = color_map.get(gene_colors.get(gene_name.upper(), "grey"), "#6C757D")
        net.add_node(gene_name, label=gene_name, color=gene_color, size=15,
                     title=f"基因: {gene_name}")

        if contig in contig_type:
            net.add_edge(contig, gene_name)
        else:
            net.add_edge("菌株基因组", gene_name)

    net.set_options("""{
      "physics": {
        "barnesHut": {
          "gravitationalConstant": -8000,
          "springLength": 200
        },
        "minVelocity": 0.75
      }
    }""")

    if output_html is None:
        output_html = Path("data/temp/network.html")
    output_html.parent.mkdir(parents=True, exist_ok=True)
    net.save_graph(str(output_html))
    return output_html