"""
backend/amr_pipeline.py
Docker 版：调用 AMRFinderPlus，并自动集成 MOB‑suite 质粒移动性分析
"""
import subprocess
import json
from pathlib import Path
from backend.mob_analyzer import analyze_mobility, merge_amr_mob_results


def run_amrfinder(assembly_fasta: str, output_dir: str = None) -> Path:
    fasta_path = Path(assembly_fasta).resolve()
    if not fasta_path.exists():
        raise FileNotFoundError(f"输入文件不存在：{fasta_path}")

    if output_dir is None:
        out_dir = fasta_path.parent / "amrfinder_results"
    else:
        out_dir = Path(output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    out_file = out_dir / f"{fasta_path.stem}_amrfinder.tsv"
    json_file = out_dir / f"{fasta_path.stem}_amrfinder.json"

    input_dir = fasta_path.parent

    # 1. 运行 AMRFinderPlus
    cmd = [
        "docker", "run", "--rm",
        "-v", f"{input_dir}:/input:ro",
        "-v", f"{out_dir}:/output",
        "ncbi/amr:latest",
        "amrfinder",
        "-n", f"/input/{fasta_path.name}",
        "--output", f"/output/{out_file.name}",
        "--threads", "4"
    ]
    try:
        print(f"正在运行 AMRFinderPlus（Docker）：{' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print("AMRFinderPlus 完成")
    except subprocess.CalledProcessError as e:
        print("AMRFinderPlus 报错：", e.stderr)
        raise RuntimeError(
            f"AMRFinderPlus 运行失败。\n"
            f"请确保 Docker Desktop 已启动。\n"
            f"错误信息：{e.stderr}"
        )

    # 2. TSV → JSON
    tsv_to_json(out_file, json_file)

    # 3. 自动运行 MOB‑suite（如果检测到耐药基因）
    try:
        with open(json_file, "r", encoding="utf-8") as f:
            amr_genes = json.load(f)
        # 提取携带耐药基因的 contig ID
        target_contigs = list(set(g["contig_id"] for g in amr_genes if g.get("contig_id")))
        if target_contigs:
            print("正在运行 MOB‑suite 进行质粒移动性分析……")
            mob_df = analyze_mobility(str(fasta_path), target_contigs)

            # 保存 MOB 原始结果（供规则引擎使用）
            mob_csv = out_dir / f"{fasta_path.stem}_mobsuite.csv"
            mob_df.to_csv(mob_csv, index=False)
            print(f"MOB 结果已保存至 {mob_csv}")

            # 生成融合报告（含证据链）
            merged = merge_amr_mob_results(json_file, mob_df, sample_id=fasta_path.stem)
            merged_path = out_dir / f"{fasta_path.stem}_merged_report.json"
            with open(merged_path, "w", encoding="utf-8") as f_merged:
                json.dump(merged, f_merged, ensure_ascii=False, indent=2)
            print(f"融合报告已保存至 {merged_path}")
    except Exception as e:
        print(f"MOB‑suite 分析失败（跳过，不影响主流程）：{e}")

    return json_file


def tsv_to_json(tsv_path: Path, json_path: Path):
    """将 AMRFinder TSV 输出转为 JSON（2026 版列名，自动跳过重复表头）"""
    import csv
    genes = []
    with open(tsv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(
            (line for line in f if not line.startswith("#")),
            delimiter="\t"
        )
        for row in reader:
            symbol = row.get("Element symbol", "").strip()
            # 跳过空行、以及重复出现的表头行
            if not symbol or symbol == "Element symbol":
                continue

            gene_info = {
                "gene_symbol": symbol,
                "gene_name": row.get("Element name", ""),
                "scope": row.get("Scope", ""),
                "element_type": row.get("Type", ""),
                "element_subtype": row.get("Subtype", ""),
                "class": row.get("Class", ""),
                "subclass": row.get("Subclass", ""),
                "method": row.get("Method", ""),
                "target_length": row.get("Target length", ""),
                "coverage_pct": row.get("% Coverage of reference", ""),
                "identity_pct": row.get("% Identity to reference", ""),
                "alignment_length": row.get("Alignment length", ""),
                "closest_ref_acc": row.get("Closest reference accession", ""),
                "closest_ref_name": row.get("Closest reference name", ""),
                "contig_id": row.get("Contig id", ""),
                "start": row.get("Start", ""),
                "stop": row.get("Stop", ""),
                "strand": row.get("Strand", ""),
            }
            genes.append(gene_info)

    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(genes, f, ensure_ascii=False, indent=2)
    print(f"AMR 基因信息已保存到 {json_path}，共 {len(genes)} 条记录")