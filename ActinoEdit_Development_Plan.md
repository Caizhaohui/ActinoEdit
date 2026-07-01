# ActinoEdit 可执行开发计划

> **项目名称**：ActinoEdit — 放线菌与工业微生物 CRISPR 基因编辑设计工具
>
> **技术栈**：Python 3.10+ | Typer | NiceGUI | SQLite | Biopython | Pandas | Jinja2
>
> **总体路线**：CLI 核心 → 统一 Pipeline → 本地 Web → 一键启动 → 放线菌特色功能 → 本地数据库 → 工业微生物平台

---

## 目录

- [项目总览](#项目总览)
- [技术架构](#技术架构)
- [开发阶段与里程碑](#开发阶段与里程碑)
- [Phase 1：CLI MVP（第1周）](#phase-1cli-mvp第1周)
- [Phase 2：CLI 实用版（第2周）](#phase-2cli-实用版第2周)
- [Phase 3：本地 Web MVP（第3周）](#phase-3本地-web-mvp第3周)
- [Phase 4：一键启动与本地封装（第4周）](#phase-4一键启动与本地封装第4周)
- [Phase 5：放线菌特色功能（第5周）](#phase-5放线菌特色功能第5周)
- [Phase 6：本地数据库（第6周）](#phase-6本地数据库第6周)
- [Phase 7：工业微生物数据库平台（第7周+）](#phase-7工业微生物数据库平台第7周)
- [核心数据模型](#核心数据模型)
- [仓库目录结构](#仓库目录结构)
- [验收标准与质量门禁](#验收标准与质量门禁)

---

## 项目总览

### 定位

ActinoEdit 是一个面向 **放线菌、链霉菌和工业微生物** 的本地化 CRISPR 靶点设计工具。

### 核心目标

| 目标 | 说明 |
|------|------|
| 自定义基因组上传 | 支持用户上传微生物基因组 FASTA 文件 |
| 多微生物适配 | 适配不同微生物的 sgRNA 设计参数 |
| 高 GC 工业菌支持 | 专为放线菌/链霉菌等高 GC 菌优化 |
| 本地运行 | 保护企业或实验室菌株数据安全 |
| 渐进式开发 | CLI 核心 → 本地 Web → 数据库平台 |

### 产品版本路线

```
v0.1  CLI MVP                    ← 第1周交付
v0.2  CLI 实用版（脱靶+评分+报告） ← 第2周交付
v0.3  本地 Web MVP               ← 第3周交付
v0.4  一键启动器 / 本地应用封装    ← 第4周交付
v0.5  多微生物 profile 支持
v0.6  放线菌特色功能（BGC/CRISPRi/碱基编辑） ← 第5周交付
v0.7  本地 SQLite 项目数据库      ← 第6周交付
v1.0  工业微生物数据库平台         ← 第7周+交付
```

---

## 技术架构

### 核心原则

```
CLI (Typer)  ──┐
               ├──→  统一 Pipeline (pipeline.py)  ──→  核心算法模块
Web (NiceGUI) ─┘         ↑ 不依赖 UI 层
```

- **核心 CRISPR 设计逻辑独立于 CLI 和 Web UI**
- CLI 和 Web UI 调用同一个 `run_design_pipeline()` 函数
- 不在 UI 代码中重复实现生物算法
- 所有核心模块保持小型化和可测试性

### 技术栈选型

| 层级 | 技术 | 用途 |
|------|------|------|
| 语言 | Python 3.10+ | 主开发语言 |
| 包管理 | uv / poetry | 依赖管理 |
| CLI | Typer + Rich | 命令行界面与终端美化 |
| 序列解析 | Biopython | FASTA/GenBank 解析 |
| 数据处理 | Pandas + OpenPyXL | 表格处理与 Excel 输出 |
| 报告生成 | Jinja2 | HTML 报告模板 |
| 本地 Web | NiceGUI | 本地 Web 应用框架 |
| 数据库 | SQLite → PostgreSQL | 本地/内网数据存储 |
| 测试 | Pytest | 单元与集成测试 |
| 代码质量 | Ruff + MyPy | Lint 与类型检查 |

---

## 开发阶段与里程碑

| 阶段 | 周期 | 里程碑 | 核心交付物 |
|------|------|--------|-----------|
| Phase 1 | Week 1 | CLI MVP | `actinoedit design` 命令，输出 CSV |
| Phase 2 | Week 2 | CLI 实用版 | 脱靶搜索 + 评分 + Excel/HTML 报告 |
| Phase 3 | Week 3 | 本地 Web MVP | `actinoedit-web` 启动本地页面 |
| Phase 4 | Week 4 | 本地应用封装 | 双击启动，自动打开浏览器 |
| Phase 5 | Week 5 | 放线菌特色版 | BGC 注释 + CRISPRi + 碱基编辑 |
| Phase 6 | Week 6 | 本地数据库版 | SQLite 项目管理 |
| Phase 7 | Week 7+ | 工业微生物平台 | PostgreSQL + 多用户内网部署 |

---

## Phase 1：CLI MVP（第1周）

> **目标**：实现第一个可用的命令行工具
>
> **验收命令**：
> ```bash
> actinoedit design \
>   --genome examples/demo_genome.fasta \
>   --gff examples/demo_annotation.gff \
>   --target geneA \
>   --pam NGG \
>   --spacer-length 20 \
>   --output results/guides.csv
> ```

### Task 1：初始化项目骨架

**优先级**：🔴 最高 | **预计工时**：0.5 天

**执行步骤**：

1. 创建 `pyproject.toml`，配置依赖：
   - 运行依赖：`biopython`, `pandas`, `openpyxl`, `typer`, `rich`, `jinja2`, `pyyaml`
   - 开发依赖：`pytest`, `ruff`, `mypy`
2. 创建 src-layout 包结构 `src/actinoedit/`
3. 添加 CLI 入口点 `actinoedit`（Typer）
4. 预留 Web 入口点 `actinoedit-web`（暂不实现）
5. 创建 `README.md` 和 `AGENTS.md`
6. 添加 GitHub Actions CI 工作流（pytest + ruff）
7. 创建示例文件：
   - `examples/demo_genome.fasta`（小型人工基因组）
   - `examples/demo_annotation.gff`（对应注释）
   - `examples/profiles/` 下的 YAML 配置文件
8. 添加冒烟测试：`import actinoedit; actinoedit --help`

**验收标准**：

```bash
pip install -e ".[dev]"
actinoedit --help        # 应显示帮助信息
pytest                   # 所有测试通过
ruff check .             # 无 lint 错误
```

---

### Task 2：核心数据模型

**优先级**：🔴 最高 | **预计工时**：0.5 天

**执行步骤**：

1. 创建 `src/actinoedit/core/models.py`
2. 定义以下 dataclass：

| 模型 | 字段 |
|------|------|
| `Contig` | name, sequence, length, gc_content |
| `GeneFeature` | contig, start, end, strand, locus_tag, gene_name, product, feature_type |
| `TargetRegion` | contig, start, end, strand, label |
| `GuideCandidate` | guide_id, contig, spacer, pam, start, end, strand, pam_start, pam_end, cut_site, gc_content, target_label |
| `OffTargetHit` | guide_id, contig, start, end, strand, sequence, mismatch_count, mismatch_positions, nearby_gene |
| `GuideScore` | guide_id, specificity_score, gc_score, position_score, homopolymer_penalty, final_score, recommendation |
| `OrganismProfile` | name, display_name, default_pam, spacer_length, max_mismatches, recommended_gc_min/max, high_gc_warning_threshold, ... |

3. 坐标规则：
   - **公共坐标**：1-based inclusive（基因组坐标）
   - **内部计算**：0-based half-open（Python 切片）
   - 提供显式转换方法

4. 编写单元测试：对象创建、坐标转换、验证

---

### Task 3：FASTA 解析模块

**优先级**：🔴 最高 | **预计工时**：0.5 天

**执行步骤**：

1. 创建 `src/actinoedit/io/fasta.py`
2. 实现功能：
   - 读取单/多 contig FASTA 文件
   - 返回 `dict[str, Contig]`
   - 序列标准化为大写
   - 验证 IUPAC DNA 碱基
   - 计算长度和 GC 含量
3. 错误处理：空文件、重复 contig 名、非法字符
4. 使用临时文件编写 pytest 测试

---

### Task 4：GFF3 / GenBank 解析模块

**优先级**：🔴 最高 | **预计工时**：1 天

**执行步骤**：

1. 创建 `src/actinoedit/io/gff.py`：
   - 解析标准 GFF3 格式
   - 提取 gene、CDS、rRNA、tRNA 特征
   - 解析属性：ID、locus_tag、gene、Name、product
   - 兼容 Prokka 和 Bakta 风格 GFF
   - 忽略注释和 FASTA 尾部
   - 提供搜索辅助函数：`find_by_locus_tag()`, `find_by_gene_name()`, `find_features_in_region()`

2. 创建 `src/actinoedit/io/gbk.py`：
   - 使用 Biopython 解析 GenBank 文件
   - 提取 CDS 和 gene 特征
   - 返回 `GeneFeature` 对象

3. 编写测试（使用人工 GFF/GenBank 内容）

---

### Task 5：PAM Pattern 模块

**优先级**：🔴 最高 | **预计工时**：0.5 天

**执行步骤**：

1. 创建 `src/actinoedit/core/pam.py`
2. 支持 IUPAC DNA 模式：A, C, G, T, N, R, Y, S, W, K, M, B, D, H, V
3. 实现函数：
   - `compile_pam(pattern)` — 转换为正则表达式
   - `is_pam_match(sequence, pattern)` — 匹配检测
   - `reverse_complement(sequence)` — 反向互补
4. 支持 PAM 类型：NGG, NGA, NAG, TTTV, NNGRRT
5. 测试覆盖：各 PAM 类型、小写输入、非法字符

---

### Task 6：sgRNA 扫描模块

**优先级**：🔴 最高 | **预计工时**：1 天

**执行步骤**：

1. 创建 `src/actinoedit/core/scanner.py`
2. 输入参数：contig 名、DNA 序列、目标坐标、PAM 模式、spacer 长度、nuclease 配置
3. 默认配置（SpCas9）：PAM=NGG, spacer=20bp, cut offset=PAM 上游 3bp
4. 扫描正负双链
5. 返回 `GuideCandidate` 对象（1-based 坐标）
6. 避免跨 contig 边界的候选
7. 计算 GC 含量
8. 生成稳定的 guide_id
9. 测试：正向链、反向链、无 PAM、多 PAM、边界情况

---

### Task 7：目标区域选择模块

**优先级**：🔴 最高 | **预计工时**：0.5 天

**执行步骤**：

1. 创建 `src/actinoedit/core/target.py`
2. 支持选择方式：
   - `locus_tag`
   - `gene_name`
   - 坐标字符串：`contig:start-end`
3. 支持可选的侧翼扩展
4. 返回 `TargetRegion`
5. 验证目标存在，歧义时给出清晰错误
6. 添加 CLI 子命令 `actinoedit target-info`
7. 编写测试

---

### Task 8：第一版 design 命令

**优先级**：🔴 最高 | **预计工时**：1 天

**执行步骤**：

1. 实现 `actinoedit design` 命令
2. 流程：加载 FASTA → 加载 GFF/GBK → 解析目标区域 → 扫描候选 sgRNA → 输出 CSV
3. CSV 输出列：guide_id, target_label, contig, start, end, strand, spacer, pam, pam_start, pam_end, cut_site, gc_content
4. 使用 Rich 打印终端摘要表格
5. 编写集成测试

---

## Phase 2：CLI 实用版（第2周）

> **目标**：支持脱靶搜索、评分和多格式报告
>
> **验收命令**：
> ```bash
> actinoedit design \
>   --genome examples/demo_genome.fasta \
>   --gff examples/demo_annotation.gff \
>   --target geneA \
>   --profile streptomyces \
>   --output-prefix results/geneA
> ```
> **输出**：`geneA_guides.csv`, `geneA_report.xlsx`, `geneA_report.html`

### Task 9：脱靶搜索

**优先级**：🔴 高 | **预计工时**：1 天

**执行步骤**：

1. 创建 `src/actinoedit/core/offtarget.py`
2. 输入：基因组 contigs、候选 guides、max_mismatches（默认 3）
3. 搜索所有 contig 的正负双链
4. 比较 spacer 长度窗口，计算 mismatch 数
5. 返回 `OffTargetHit` 对象
6. 包含 on-target hit（mismatch_count=0）
7. 支持排除精确 on-target 坐标
8. 测试：精确匹配、1/2 mismatch、反向互补命中、多 contig

---

### Task 10：放线菌/高 GC 评分系统

**优先级**：🔴 高 | **预计工时**：1 天

**执行步骤**：

1. 创建 `src/actinoedit/core/scoring.py`
2. 评分维度：

| 维度 | 说明 |
|------|------|
| specificity_score | 脱靶命中越少越高 |
| gc_score | 偏好 profile 指定的 GC 范围 |
| position_score | knockout 模式下偏好 CDS 前 1/3 |
| homopolymer_penalty | 惩罚长同聚物 |

3. 推荐等级：`excellent` / `good` / `caution` / `avoid`
4. 权重可通过 `config.yaml` 配置
5. 为每个评分组件编写测试
6. 将评分列添加到 design CSV 输出

---

### Task 11：Organism Profile 支持

**优先级**：🔴 高 | **预计工时**：0.5 天

**执行步骤**：

1. 创建 `src/actinoedit/core/profiles.py`
2. 加载 `examples/profiles/*.yaml` 配置文件
3. 内置 profile：actinomycete, streptomyces, ecoli, bacillus, yeast, custom
4. CLI 选项：`--profile streptomyces`
5. 用户指定 `--pam` 或 `--spacer-length` 时覆盖 profile 默认值
6. 测试 profile 加载和参数覆盖行为

**Profile 配置示例**（streptomyces）：

```yaml
name: streptomyces
display_name: Streptomyces / Actinomycete
default_pam: NGG
spacer_length: 20
max_mismatches: 3
recommended_gc_min: 40
recommended_gc_max: 80
high_gc_warning_threshold: 75
prefer_cds_first_third_for_knockout: true
enable_bgc_annotation: true
offtarget_strictness: high
```

---

### Task 12：统一 Pipeline

**优先级**：🔴 最高 | **预计工时**：1 天

**执行步骤**：

1. 创建 `src/actinoedit/core/pipeline.py`
2. 定义 `DesignInput` dataclass：

```python
@dataclass
class DesignInput:
    genome_path: str
    annotation_path: str
    target: str
    pam: str
    spacer_length: int
    max_mismatches: int
    organism_profile: str
    output_prefix: str
```

3. 定义 `DesignResult` dataclass：

```python
@dataclass
class DesignResult:
    target_region: TargetRegion
    guide_candidates: list[GuideCandidate]
    off_target_hits: list[OffTargetHit]
    guide_scores: list[GuideScore]
    warnings: list[str]
    output_files: list[str]
```

4. 实现 `run_design_pipeline(input: DesignInput) -> DesignResult`
5. Pipeline 调用：FASTA 解析 → GFF/GBK 解析 → 目标解析 → PAM 扫描 → 脱靶搜索 → 评分 → 报告导出
6. **Pipeline 不依赖 Typer CLI 或 Web UI**
7. 更新 CLI `design` 命令调用 `run_design_pipeline`
8. 使用人工 demo 文件编写 pipeline 测试

---

### Task 13：Excel 和 HTML 报告

**优先级**：🔴 高 | **预计工时**：1 天

**执行步骤**：

1. 创建报告模块：
   - `src/actinoedit/reports/tables.py` — DataFrame 转换
   - `src/actinoedit/reports/excel.py` — Excel 多 Sheet 导出
   - `src/actinoedit/reports/html.py` — HTML 报告生成
   - `src/actinoedit/reports/templates/report.html.j2` — Jinja2 模板

2. Excel 报告 Sheet：
   - `guide_candidates` — 候选指南表
   - `off_targets` — 脱靶命中表
   - `parameters` — 设计参数
   - `warnings` — 警告信息

3. HTML 报告内容：
   - 项目摘要
   - 目标区域信息
   - Top guides 排行
   - 脱靶摘要
   - 警告提示

4. 更新 CLI 支持 `--output-prefix`，生成三个文件

5. 测试文件创建

---

## Phase 3：本地 Web MVP（第3周）

> **目标**：实现本地 Web 应用
>
> **验收命令**：`actinoedit-web` → 打开 `http://127.0.0.1:8080`

### Task 14：本地 Web 项目骨架

**优先级**：🔴 高 | **预计工时**：0.5 天

**执行步骤**：

1. 创建 Web 模块：
   - `src/actinoedit/web/app.py` — 应用入口
   - `src/actinoedit/web/pages.py` — 页面定义
   - `src/actinoedit/web/components.py` — 可复用组件
   - `src/actinoedit/web/state.py` — 状态管理
   - `src/actinoedit/web/runner.py` — Pipeline 执行器

2. 添加 `actinoedit-web` 命令
3. 应用标题：`ActinoEdit Local - CRISPR Design Toolkit`
4. 单页 UI 区域：输入文件、微生物 profile、CRISPR 参数、目标输入、运行设计、结果表格、警告、下载
5. 冒烟测试：import web 模块

---

### Task 15：文件上传与参数表单

**优先级**：🔴 高 | **预计工时**：1 天

**执行步骤**：

1. 文件输入：genome FASTA、annotation GFF/GBK（上传或路径输入）
2. 微生物 profile 下拉菜单
3. 参数输入：PAM、spacer length、max mismatches、GC 范围
4. 目标输入：支持 locus_tag、gene name、contig:start-end
5. Profile 切换时自动更新默认参数
6. 允许手动覆盖 profile 默认值
7. 基础验证与清晰错误提示

---

### Task 16：连接 Web 与 Pipeline

**优先级**：🔴 最高 | **预计工时**：1 天

**执行步骤**：

1. 点击 "Run Design" 时：
   - 收集文件输入、profile、参数、目标
   - 创建 `DesignInput`
   - 调用 `run_design_pipeline()`
2. 显示进度和日志消息
3. 保持 UI 响应（异步执行）
4. Pipeline 完成后：显示摘要、警告、输出路径、填充结果表格
5. 错误处理：清晰错误消息 + 可折叠的 debug 日志

---

### Task 17：结果表格、筛选与下载

**优先级**：🔴 高 | **预计工时**：1 天

**执行步骤**：

1. 交互式结果表格，列：guide_id, target_label, contig, start, end, strand, spacer, pam, gc_content, off_target_0mm~3mm, final_score, recommendation
2. 排序：final_score、gc_content、脱靶数
3. 筛选：recommendation、GC 范围、最大脱靶数
4. 下载按钮：CSV、Excel、HTML 报告
5. 支持复制选中行到剪贴板

---

### Task 18：Demo 模式

**优先级**：🟡 中 | **预计工时**：0.5 天

**执行步骤**：

1. 添加 "Load Demo Dataset" 按钮
2. 使用 `examples/demo_genome.fasta` + `examples/demo_annotation.gff` + streptomyces profile
3. 自动填充所有输入字段
4. 允许运行 demo 设计
5. 更新 README 的 demo 说明

---

## Phase 4：一键启动与本地封装（第4周）

> **目标**：非编程用户无需命令行即可使用

### Task 19：一键启动器

**优先级**：🟡 中 | **预计工时**：0.5 天

**执行步骤**：

1. 创建 `scripts/run_actinoedit_local.py`
2. 启动 actinoedit-web，绑定 127.0.0.1，选择默认端口
3. 自动打开默认浏览器
4. 打印本地 URL
5. 添加 CLI 选项：`actinoedit-web --open-browser`
6. README 分别为命令行用户和非编程用户提供说明

---

### Task 20：本地打包

**优先级**：🟡 中 | **预计工时**：1 天

**执行步骤**：

1. PyInstaller 配置，支持：
   - Windows `.exe`
   - macOS `.app` bundle
   - Linux 可执行文件
2. 构建脚本：`scripts/build_windows.ps1`, `scripts/build_macos.sh`, `scripts/build_linux.sh`
3. 包含资源：示例 profiles、报告模板、demo 数据
4. README 打包说明
5. 故障排除：端口占用、浏览器未打开、文件缺失、权限问题

---

## Phase 5：放线菌特色功能（第5周）

### Task 21：antiSMASH / BGC 注释整合

**优先级**：🟡 中 | **预计工时**：1 天

**执行步骤**：

1. 创建 `src/actinoedit/annotation/bgc.py`
2. 读取 antiSMASH GenBank 输出或简单 BGC BED 文件
3. 定义 `BGCRegion` dataclass：contig, start, end, bgc_id, bgc_type, product
4. 标注 guide 是否在 BGC 内
5. 标注最近的 BGC（guide 在 BGC 外但较近时）
6. 添加列：bgc_id, bgc_type, bgc_context
7. Excel/HTML 报告中包含 BGC 信息
8. 使用人工 BGC 记录编写测试

---

### Task 22：CRISPRi 模式

**优先级**：🟡 中 | **预计工时**：1 天

**执行步骤**：

1. 添加 CLI/Web 选项 `mode = crispri`
2. 对基因目标定义候选区域：上游启动子区、起始密码子附近、早期 CDS
3. 链注释：template / non_template
4. CRISPRi 专用位置评分
5. 输出列：crispri_region_type, distance_to_start_codon, target_strand_relation
6. 不包含湿实验操作细节
7. 编写测试

---

### Task 23：碱基编辑分析模块

**优先级**：🟡 中 | **预计工时**：1.5 天

**执行步骤**：

1. 创建 `src/actinoedit/core/base_editor.py`
2. 支持 CBE（C→T）和 ABE（A→G）
3. 可配置编辑窗口
4. CDS 内的 guide 预测密码子级后果：同义/错义/无义突变
5. 检测可能的提前终止密码子
6. 检测编辑窗口内的旁观者编辑
7. 添加输出 Sheet：`predicted_edits`
8. CLI 命令：`actinoedit base-edit --editor CBE`
9. Web UI 添加碱基编辑模式选项
10. 使用人工 CDS 示例编写测试

---

## Phase 6：本地数据库（第6周）

> **目标**：从"一次性设计工具"升级为"本地项目管理工具"

### Task 24：SQLite 数据库原型

**优先级**：🟡 中 | **预计工时**：1.5 天

**执行步骤**：

1. 创建 `src/actinoedit/db/` 模块
2. 数据库表：

| 表名 | 说明 |
|------|------|
| organism | 菌株记录 |
| genome | 基因组记录 |
| gene | 基因记录 |
| bgc | BGC 记录 |
| guide | sgRNA 记录 |
| editing_project | 编辑项目 |
| validation_result | 验证结果 |

3. 使用 SQLModel 或 SQLAlchemy
4. CLI 命令：
   - `actinoedit db init` — 初始化数据库
   - `actinoedit db import-genome` — 导入基因组
   - `actinoedit db list-organisms` — 列出菌株
   - `actinoedit db save-guides` — 保存 guides
5. 正常 CLI design 模式不依赖数据库
6. 使用临时 SQLite 数据库编写测试

---

### Task 25：本地 Web 数据库页面

**优先级**：🟡 中 | **预计工时**：1 天

**执行步骤**：

1. 添加页面：Organisms, Genomes, Genes, Guides, Editing Projects, Validation Results
2. 支持将基因组 FASTA 和注释导入本地 SQLite
3. 支持保存 guide 设计结果到数据库
4. 按菌株、基因、项目浏览已保存的 guides
5. 导出选项：CSV、Excel、项目报告
6. 数据库功能保持可选

---

## Phase 7：工业微生物数据库平台（第7周+）

### Task 26：PostgreSQL / 内网平台准备

**优先级**：🟢 低 | **预计工时**：2 天

**执行步骤**：

1. 抽象数据库配置：
   - SQLite：本地单用户模式
   - PostgreSQL：多用户内网模式
2. 配置文件支持：`local.yaml`, `lab_server.yaml`
3. 环境变量支持数据库 URL
4. 使用 Alembic 管理数据库迁移
5. 文档更新：`docs/database.md`
   - 本地模式说明
   - 实验室服务器模式说明
   - 备份策略
   - 数据隐私注意事项

---

## 核心数据模型

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│    Contig        │     │  GeneFeature      │     │  TargetRegion   │
│─────────────────│     │──────────────────│     │─────────────────│
│ name             │     │ contig            │     │ contig          │
│ sequence         │     │ start (1-based)   │     │ start (1-based) │
│ length           │     │ end (1-based)     │     │ end (1-based)   │
│ gc_content       │     │ strand            │     │ strand          │
└─────────────────┘     │ locus_tag         │     │ label           │
                        │ gene_name         │     └─────────────────┘
                        │ product           │
                        │ feature_type      │
                        └──────────────────┘

┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│ GuideCandidate   │     │  OffTargetHit     │     │  GuideScore     │
│─────────────────│     │──────────────────│     │─────────────────│
│ guide_id         │     │ guide_id          │     │ guide_id        │
│ contig           │     │ contig            │     │ specificity     │
│ spacer           │     │ start / end       │     │ gc_score        │
│ pam              │     │ strand            │     │ position_score  │
│ start / end      │     │ sequence          │     │ homopolymer_pen │
│ strand           │     │ mismatch_count    │     │ final_score     │
│ pam_start/end    │     │ mismatch_positions│     │ recommendation  │
│ cut_site         │     │ nearby_gene       │     └─────────────────┘
│ gc_content       │     └──────────────────┘
│ target_label     │
└─────────────────┘

┌──────────────────────────────────────────────────────────────┐
│                      OrganismProfile                          │
│──────────────────────────────────────────────────────────────│
│ name | display_name | default_pam | spacer_length            │
│ max_mismatches | recommended_gc_min | recommended_gc_max     │
│ high_gc_warning_threshold | prefer_cds_first_third           │
│ enable_bgc_annotation | offtarget_strictness                 │
└──────────────────────────────────────────────────────────────┘
```

### 坐标系统规则

| 场景 | 坐标系统 | 示例 |
|------|----------|------|
| 公共报告 / 用户展示 | 1-based inclusive | 基因位置 100..200 |
| Python 内部计算 | 0-based half-open | `seq[99:200]` |
| 转换 | 必须显式且经过测试 | `to_slice()` / `from_slice()` |

---

## 仓库目录结构

```
actinoedit/
├── pyproject.toml
├── README.md
├── LICENSE
├── AGENTS.md
├── .gitignore
│
├── .github/
│   └── workflows/
│       └── test.yml
│
├── src/
│   └── actinoedit/
│       ├── __init__.py
│       ├── cli.py                  # Typer CLI 入口
│       ├── config.py               # 配置管理
│       │
│       ├── io/                     # 文件解析层
│       │   ├── __init__.py
│       │   ├── fasta.py            # FASTA 解析
│       │   ├── gff.py              # GFF3 解析
│       │   └── gbk.py              # GenBank 解析
│       │
│       ├── core/                   # 核心算法层（不依赖 UI）
│       │   ├── __init__.py
│       │   ├── models.py           # 数据模型
│       │   ├── sequence.py         # 序列工具
│       │   ├── pam.py              # PAM 匹配
│       │   ├── scanner.py          # sgRNA 扫描
│       │   ├── target.py           # 目标区域选择
│       │   ├── offtarget.py        # 脱靶搜索
│       │   ├── scoring.py          # 评分系统
│       │   ├── pipeline.py         # 统一 Pipeline ⭐
│       │   ├── profiles.py         # 微生物 Profile
│       │   ├── base_editor.py      # 碱基编辑分析
│       │   └── crispri.py          # CRISPRi 设计
│       │
│       ├── annotation/             # 注释整合层
│       │   ├── __init__.py
│       │   ├── genes.py
│       │   └── bgc.py              # BGC 注释
│       │
│       ├── reports/                # 报告生成层
│       │   ├── __init__.py
│       │   ├── tables.py
│       │   ├── excel.py
│       │   ├── html.py
│       │   └── templates/
│       │       └── report.html.j2
│       │
│       ├── web/                    # NiceGUI 本地 Web
│       │   ├── __init__.py
│       │   ├── app.py
│       │   ├── pages.py
│       │   ├── components.py
│       │   ├── state.py
│       │   └── runner.py
│       │
│       └── db/                     # 数据库层
│           ├── __init__.py
│           ├── models.py
│           ├── crud.py
│           └── init_db.py
│
├── tests/                          # 测试
│   ├── test_models.py
│   ├── test_fasta.py
│   ├── test_gff.py
│   ├── test_gbk.py
│   ├── test_pam.py
│   ├── test_scanner.py
│   ├── test_target.py
│   ├── test_offtarget.py
│   ├── test_scoring.py
│   ├── test_pipeline.py
│   ├── test_profiles.py
│   └── test_reports.py
│
├── examples/                       # 示例数据
│   ├── demo_genome.fasta
│   ├── demo_annotation.gff
│   ├── demo_annotation.gbk
│   ├── config.yaml
│   └── profiles/
│       ├── actinomycete.yaml
│       ├── streptomyces.yaml
│       ├── ecoli.yaml
│       ├── bacillus.yaml
│       ├── yeast.yaml
│       └── custom.yaml
│
├── docs/                           # 文档
│   ├── design.md
│   ├── user_guide.md
│   ├── developer_guide.md
│   ├── web_app.md
│   └── database.md
│
└── scripts/                        # 脚本
    ├── run_web.py
    └── build_local_app.py
```

---

## 验收标准与质量门禁

### 每个 Task 完成前必须通过

```bash
# 运行所有测试
pytest

# 代码质量检查
ruff check .

# 类型检查
mypy src
```

### 各里程碑验收命令

| 里程碑 | 验收命令 |
|--------|----------|
| M1: CLI MVP | `actinoedit design --genome examples/demo_genome.fasta --gff examples/demo_annotation.gff --target geneA --pam NGG --output results/guides.csv` |
| M2: CLI 实用版 | `actinoedit design --genome examples/demo_genome.fasta --gff examples/demo_annotation.gff --target geneA --profile streptomyces --output-prefix results/geneA` |
| M3: 本地 Web MVP | `actinoedit-web` → 浏览器打开 http://127.0.0.1:8080 |
| M4: 本地应用封装 | 双击 ActinoEdit → 自动启动浏览器 |
| M5: 放线菌特色版 | `actinoedit base-edit --genome ... --gff ... --target geneA --editor CBE` |
| M6: 本地数据库版 | `actinoedit db init && actinoedit db import-genome ...` |
| M7: 工业微生物平台 | 配置 `lab_server.yaml`，连接 PostgreSQL |

### 编码规范

| 规范 | 要求 |
|------|------|
| Python 版本 | 3.10+ |
| 类型注解 | 全部使用 type hints |
| 数据模型 | dataclass 或 pydantic |
| 测试框架 | pytest |
| Lint 工具 | ruff |
| 类型检查 | mypy |
| 函数风格 | 小型、确定性函数 |
| 许可证 | 不使用 GPL/AGPL 代码 |
| 算法 | 独立实现，不复制外部代码 |

### 安全与范围

ActinoEdit 是 **计算设计和注释工具**，不包含：
- 湿实验操作流程
- 转化条件
- 培养条件
- 菌株特异性操作说明

---

## 执行建议

### 优先级排序

```
Week 1: ██████████ Task 1-8   （CLI MVP — 必须完成）
Week 2: ██████████ Task 9-13  （CLI 实用版 — 必须完成）
Week 3: ██████████ Task 14-18 （本地 Web MVP — 核心价值）
Week 4: ██████░░░░ Task 19-20 （一键启动 — 用户体验）
Week 5: ██████░░░░ Task 21-23 （放线菌特色 — 差异化）
Week 6: ██████░░░░ Task 24-25 （本地数据库 — 项目管理）
Week 7+: ████░░░░░░ Task 26   （平台化 — 长期目标）
```

### 关键风险点

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| 脱靶搜索性能 | 全基因组扫描可能很慢 | 先实现简单版本，后续优化算法 |
| NiceGUI 学习曲线 | 可能影响 Web 开发进度 | 先用 Streamlit 快速原型 |
| 高 GC 序列特殊处理 | 评分准确性 | 参考文献验证评分逻辑 |
| PyInstaller 打包 | 跨平台兼容性问题 | 优先支持主流平台 |

### 最终推荐路线

```
先 CLI → 再 Pipeline → 再本地 Web → 再一键启动 → 再数据库 → 最后平台化
```

**ActinoEdit 的第一个真正实用版本应该是 `v0.3`（本地 Web MVP），它支持：**

- 用户上传任意微生物 genome.fasta
- 用户上传 GFF/GBK 注释
- 选择或自定义微生物 profile
- 自定义 PAM / spacer / mismatch 参数
- 设计 sgRNA
- 评估脱靶
- 输出 CSV / Excel / HTML 报告

---

*文档生成日期：2026-06-24*
*基于《ActinoEdit Final Development Plan.docx》整理*
