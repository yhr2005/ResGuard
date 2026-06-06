# 🛡️ ResGuard — 耐药基因组风险哨兵
### ResGuard: AI-Powered AMR Sentinel for One Health

**面向基层疾控、水产养殖与教学场景的一键式细菌耐药风险筛查与传播潜力评估平台**

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10](https://img.shields.io/badge/Python-3.10-blue.svg)](https://www.python.org/)
![Platform: Windows 11](https://img.shields.io/badge/Platform-Windows%2011%20%7C%20Docker-lightgrey)

---

## 📖 项目简介

抗生素耐药性（AMR）是全球十大公共卫生威胁之一。在热带水产养殖、基层疾控等领域，耐药菌株的快速筛查与传播风险评估长期受限于**工具碎片化、专业门槛高、传播风险不明**三大痛点。

ResGuard 提供**全自动、离线、可解释**的耐药基因组分析服务。用户只需上传细菌全基因组序列（FASTA），系统即可自动完成：

- 耐药基因检测（AMRFinderPlus）
- 质粒移动性分析（MOB‑suite）
- 风险评级（规则引擎 + 质粒传播力联合判定）
- 交互式网络图（菌株‑质粒‑基因关系）
- AI 临床用药建议（支持离线本地模型 / 外部云端 API）
- PDF 报告导出（含证据链、网络图、AI 解读）

**无需 Linux，无需命令行基础，双击启动脚本即可运行。**

---

## 🎯 亮点与创新

| 亮点 | 说明 |
|------|------|
| 🔗 **多工具自动化整合** | 将 AMRFinderPlus、MOB‑suite、PyVis 及大语言模型融合为一条流水线 |
| 🧬 **证据链可视化** | 垂直时间线展示从基因检出→质粒定位→移动性判定→综合结论的完整推理链 |
| 🚨 **质粒传播力联动风险评级** | 若基因位于可接合转移质粒，自动提升预警等级（如碳青霉烯酶基因强制升至“极高”） |
| 💻 **Windows 原生 + Docker 封装** | 通过 Docker 运行生信工具，彻底屏蔽 Linux 依赖 |
| 🤖 **AI 容错机制** | 当本地模型不可用或 API 超时时，自动回退至规则引擎，确保不出现空白输出 |
| 📜 **完全开源** | MIT 协议，代码、规则库、操作文档全部开放 |

---

## 🧰 技术架构

```
用户上传 FASTA
       │
       ▼
 AMRFinderPlus (Docker)          ← 耐药基因检出
       │
       ├─▶ MOB‑suite (Docker)    ← 质粒移动性分析 (conjugative/mobilizable)
       │
       ├─▶ 规则引擎              ← 基因‑表型‑风险匹配 + 质粒联动升级
       │
       ├─▶ PyVis 网络图           ← 交互式菌株‑质粒‑基因网络
       │
       └─▶ AI 客户端              ← 本地 Ollama 或外部 API 生成中文建议
                     │
                     ▼
              PDF 生成器 (ReportLab)
```

### 关键依赖

| 组件 | 版本 | 用途 | 协议 |
|------|------|------|------|
| AMRFinderPlus | 4.2.7 | 耐药基因及点突变检测 | Public Domain |
| MOB‑suite | 3.1.9 | 质粒复制子、接合性预测 | Apache 2.0 |
| Streamlit | ≥1.28 | Web 界面框架 | Apache 2.0 |
| PyVis | ≥0.3 | 交互式网络图 | BSD‑3‑Clause |
| ReportLab | 4.x | PDF 报告生成 | BSD |
| Ollama | 最新 | 本地大模型运行环境 | MIT |
| Docker | 最新 | 生信工具容器化 | Apache 2.0 |
| Conda (Miniconda) | 最新 | Python 环境管理 | BSD‑3‑Clause |

---

## 📦 快速开始（Windows 11）

> **硬件建议**：8 核 CPU、32 GB 内存、NVIDIA RTX 4070（8 GB 显存），实际最低需求可更低。
> **软件要求**：Windows 11、Docker Desktop、Miniconda。

### 1. 克隆仓库
```bash
git clone https://github.com/your-name/ResGuard.git
cd ResGuard
```

### 2. 一键安装依赖
以**管理员身份**运行 PowerShell：
```powershell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
.\setup\install.bat   # 若该批处理已废弃，请参考下方手动安装
```
或手动执行（推荐）：
```powershell
conda create -n resguard python=3.10 -y
conda activate resguard
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 3. 构建 Docker 镜像（MOB‑suite）
```powershell
cd docker
docker build -f Dockerfile.mobsuite -t mobsuite:latest .
```
确保 Docker Desktop 已启动并配置了镜像加速器（如阿里云）。

### 4. 配置 AI 服务（可选）
- **本地 Ollama**：安装 Ollama Windows 版，执行 `ollama pull qwen3.5:4b-q4_K_M`，启动服务。
- **外部 API**：在应用侧边栏填入 OpenAI 兼容的 API 地址、Key 及模型名（如通义千问、DeepSeek）。

### 5. 启动应用
```powershell
conda activate resguard
streamlit run app.py --server.port 9000
```
或直接运行提供的启动脚本（带模拟自检动画）：
```powershell
./start_resguard.ps1
```
浏览器自动打开 `http://localhost:9000`。

---

## 🚀 使用说明

1. **上传基因组**：支持 `.fna`、`.fasta`、`.fa` 文件。
2. **点击“开始分析”**：系统自动运行 Docker 容器进行耐药基因检测和质粒分析（约 2‑5 分钟）。
3. **查看结果**：
 - 左侧：风险评级表格 + 耐药基因列表
 - 右侧：交互式网络图（红色边框 = 高风险可转移质粒）
4. **生成 AI 解读**（可选）：在侧边栏配置 API 后点击按钮，AI 将输出中文临床建议。
5. **下载 PDF 报告**：包含表格、AI 解读、证据链摘要。

### 演示数据（预装）
仓库 `data/demo/` 目录下提供了 3 个示例基因组，覆盖敏感株、单耐药株、多重耐药株，可在 Streamlit 首页一键加载。

---

## 📂 项目结构

```
ResGuard/
├── app.py                     # Streamlit 主界面
├── start_resguard.ps1         # 一键启动脚本（含环境自检动画）
├── requirements.txt           # Python 依赖
├── LICENSE                    # MIT 协议
├── README.md                  # 本文件
├── backend/
│   ├── amr_pipeline.py        # AMRFinderPlus 调用与 MOB 整合
│   ├── rule_engine.py         # 耐药规则引擎 + 风险升级
│   ├── network_builder.py     # PyVis 网络图生成
│   └── mob_analyzer.py        # MOB‑suite Docker 封装与融合
├── ai/
│   ├── api_client.py          # 外部 API / 本地 Ollama 统一调用
│   ├── model_manager.py       # Ollama 模型生命周期管理
│   ├── prompts.py             # AI 提示词模板
│   └── chat.py                # 预留对话功能
├── frontend/
│   └── evidence_chain_viewer.py # 证据链时间线可视化组件
├── report/
│   └── pdf_generator.py       # PDF 报告生成
├── data/
│   ├── rules/amr_rules.json   # 耐药基因规则库
│   ├── gene_plasmid_kb.json   # 质粒位置知识库
│   ├── demo/                  # 预置演示基因组
│   └── api_config.json        # API 配置（已加入 .gitignore）
├── docker/
│   └── Dockerfile.mobsuite    # MOB‑suite 镜像构建文件
└── docs/                      # 文档与截图（待补充）
```

## 🤝 贡献指南

欢迎任何形式的贡献！请遵循以下步骤：

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

### 安全提醒
请**不要**将 `data/api_config.json` 提交到仓库。该文件已包含在 `.gitignore` 中。

---

## 🛡️ 免责声明

本系统仅供教学、科研及公共卫生初步筛查使用，**不可作为临床诊断的直接依据**。所有用药建议应由执业医师或微生物学专业人员结合药敏试验结果最终确认。

---

## 🙏 致谢

- [NCBI AMRFinderPlus](https://github.com/ncbi/amr)
- [MOB‑suite](https://github.com/phac-nml/mob-suite)
- [Streamlit](https://streamlit.io/)
- [PyVis](https://pyvis.readthedocs.io/)
- [Ollama](https://ollama.com/)
- [通义千问 / DeepSeek 等模型提供商]

---
*~~作者的一些话：
上面基本是AI生成+人工审核。这个项目目前是只为比赛而生，而且作者水平不高。。。~~*