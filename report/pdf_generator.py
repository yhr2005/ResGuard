"""
report/pdf_generator.py
生成 PDF 报告（支持中文 + AI 解读 + 证据链）
"""
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import json
from pathlib import Path

FONT_PATH = "C:/Windows/Fonts/simhei.ttf"
if Path(FONT_PATH).exists():
    pdfmetrics.registerFont(TTFont("SimHei", FONT_PATH))
    CN_FONT = "SimHei"
else:
    CN_FONT = "Helvetica"

def generate_pdf_report(amr_json_path, risk_dict, output_pdf_path, ai_text=None, evidence_text=None):
    doc = SimpleDocTemplate(output_pdf_path, pagesize=A4,
                            rightMargin=2*cm, leftMargin=2*cm,
                            topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("CNTitle", parent=styles["Title"], fontName=CN_FONT, fontSize=18, spaceAfter=0.5*cm)
    heading_style = ParagraphStyle("CNHeading", parent=styles["Heading2"], fontName=CN_FONT, fontSize=14, spaceAfter=0.3*cm)
    normal_style = ParagraphStyle("CNNormal", parent=styles["Normal"], fontName=CN_FONT, fontSize=10, leading=14)

    with open(amr_json_path, "r", encoding="utf-8") as f:
        genes = json.load(f)

    story = []
    story.append(Paragraph("ResGuard 耐药基因组风险报告", title_style))
    story.append(Spacer(1, 0.5*cm))

    level = risk_dict.get("risk_level", "未知")
    story.append(Paragraph(f"综合风险等级：{level}", heading_style))
    story.append(Paragraph(risk_dict.get("summary", ""), normal_style))
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("检测到的耐药基因", heading_style))
    table_data = [["基因", "表型", "风险等级", "位置"]]
    for g in risk_dict.get("details", []):
        table_data.append([g.get("gene", ""), g.get("phenotype", ""), g.get("level", ""), g.get("scope", "")])
    table = Table(table_data, colWidths=[4*cm, 4*cm, 3*cm, 4*cm])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.grey),
        ("TEXTCOLOR", (0,0), (-1,0), colors.whitesmoke),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("GRID", (0,0), (-1,-1), 0.5, colors.black),
        ("FONTNAME", (0,0), (-1,-1), CN_FONT),
        ("FONTSIZE", (0,0), (-1,-1), 9),
    ]))
    story.append(table)
    story.append(Spacer(1, 0.5*cm))

    if evidence_text:
        story.append(Paragraph("传播证据链", heading_style))
        story.append(Paragraph(evidence_text.replace("\n", "<br/>"), normal_style))
        story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph("AI 临床用药建议", heading_style))
    if ai_text:
        story.append(Paragraph(ai_text.replace("\n", "<br/>"), normal_style))
    else:
        story.append(Paragraph("（请先在网页中生成 AI 解读后再下载报告）", normal_style))

    doc.build(story)