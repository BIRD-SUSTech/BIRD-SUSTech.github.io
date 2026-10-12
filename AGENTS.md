# BIRD Lab 网站维护说明（助手必读）

> 本文件面向 AI 助手。开始任何任务前先读本文件，按此处的约定与工作流执行，不要重新探查项目结构。

## 1. 项目概况

- BIRD Lab（南方科技大学仿生智能机器人设计实验室）官网，**纯静态站点**：HTML + CSS + JS，无框架、无构建步骤、无 npm 依赖
- 托管：GitHub Pages，仓库 `BIRD-SUSTech/BIRD-SUSTech.github.io`
- 双语：默认英文，`.i18n` + `data-lang` 切换（`localStorage` 记忆）
- 页面：`index.html`、`people.html`、`research.html`、`publications.html`、`news.html`、`join.html` + `members/*.html`（成员个人页）
- 工作区：`D:\BIRD Lab - Tianqi Yue\working path\DeepSeek Harness\BIRD Lab Web`

## 2. 硬性约束（不可违反）

- **不修改** `.git/`、`CNAME`、`.nojekyll`
- **不执行 git 写操作**（add/commit/push/checkout/分支）：由用户本人在 Git Bash 完成；用户会自己提交
- 用户是仓库协作者、**非 owner**：发布流程是「用户推送 `update-tianqi` 分支 → 通知管理员合并到 `main`」
- **换行统一 LF**（`.gitattributes` 已强制）；写文件时用 LF，不要写 CRLF
- 所有面向访客的文案**必须中英成对**：
  `<span class="i18n"><span data-lang="en">…</span><span data-lang="zh">…</span></span>`
- 代码风格、缩进、结构一律**照抄现有文件**（成员页基准模板：`members/dong-ruilin.html`）

## 3. 目录结构

| 路径 | 说明 |
|---|---|
| `data/members.json` | **成员唯一数据源**（见第 4 节） |
| `data/publications.json` | **论文唯一数据源**（见第 4 节） |
| `tools/build_members.py` | 由数据源生成成员页与成员卡片区（`--check` 预演不写入） |
| `tools/audit_members.py` | 核对数据源字段完整性（照片/双语/教育缺失） |
| `tools/build_publications.py` | 生成 `publications.html` 的论文列表与三个筛选下拉（`--check` 预演） |
| `tools/extract_publications.py` | 由 `publications.html` 反向提取论文数据（`--from-git` 从 HEAD 读） |
| `tools/check_site.py` | 全站自检：链接 / 图片 / 双语配对 / 标签配对 / 生成锚点 |
| `tools/normalize_eol.py` | 把文本文件换行统一为 LF（`--check` 只列出） |
| `tools/extract_members_from_html.py` | 由现有 HTML 反向提取数据（一次性迁移用） |
| `members/<slug>.html` | 成员个人页（**由生成器产出，不要手工改**） |
| `people.html` | 成员列表页；其中 `member-grid` 区块**由生成器产出，不要手工改** |
| `images/people/<slug>.jpeg` | 成员头像 |
| `images/logos/`、`images/news/`、`images/papers/`、`images/join/`、`images/social/` | 其他素材 |
| `member materials/BIRD Lab个人简介-<中文名>.docx` | 成员提交的原始简介（归档位置） |
| `inbox/` | **材料暂存区**：用户把杂乱材料丢这里 |

## 4. 核心工作流：单一数据源 + 生成器

```
用户收集的杂乱材料（inbox/ 或 member materials/）
   ↓  助手：解析（python-docx）、补全中英双语、提取照片、归档
data/members.json
   ↓  python tools/build_members.py
members/*.html  +  people.html 的成员卡片区
```

**规则**
- 成员信息（简介、研究方向、年级、邮箱、教育经历、论文、照片、排序）**只改 `data/members.json`**
- 改完必须运行生成器：`python tools/build_members.py`
- **不要手工编辑** `members/*.html` 和 `people.html` 的 `member-grid` 区块（会被下次生成覆盖）
- 生成器锚点：`people.html` 中的 `<div class="member-grid">…</div>` 区块（整个区块由生成器替换，勿手工编辑）
- `publications.html` 的**论文列表与筛选下拉**由 `data/publications.json` 生成（锚点 `<!-- PUBLICATIONS:START --> … <!-- PUBLICATIONS:END -->`），页面其余部分手工维护
- 其他页面（index / research / news / join）目前仍是手工维护

## 5. 常见任务

### A. 新增成员
1. 定位材料（`inbox/` 或用户指定）；用 python-docx 读文本，`word/media/` 里取照片
2. 照片存 `images/people/<slug>.jpeg`；Word 归档为 `member materials/BIRD Lab个人简介-<中文名>.docx`
3. 在 `data/members.json` 增加一条记录（字段见第 6 节，中英双语都要填）
4. 运行 `python tools/build_members.py`
5. 汇报改动清单，请用户刷新 `people.html` 验证

### B. 更新成员信息（简介 / 研究方向 / 年级 / 邮箱 / 论文）
同 A 的 3–5 步，只改数据源里对应字段。

### C. 更新论文（publications.html）
1. 在 `data/publications.json` 的 `items` 中增改条目（标题中英、DOI 链接、作者、期刊、年份、研究方向、关键词、标签）
2. 如出现新关键词，同时加入 `keyword_options`（筛选下拉与论文标签共用）
3. 运行 `python tools/build_publications.py`
4. 运行 `python tools/check_site.py` 自检后汇报

### D. 其他页面改动（新闻、全站样式）
直接编辑对应文件；全站性改动注意逐页同步（或用脚本批量处理）。

## 6. `data/members.json` 字段

```jsonc
{
  "members": [
    {
      "slug": "peiran-song",              // 文件名与链接用；拼音小写连字符
      "name_en": "Peiran Song",           // 名前姓后
      "name_zh": "宋沛燃",
      "role_en": "Undergraduate Student", // 角色（见下方角色用语表）
      "role_zh": "本科生",
      "group": "undergraduate",           // 排序分组，见第 7 节
      "photo": "peiran-song.jpeg",        // images/people/ 下文件名
      "email": "3338218287@qq.com",       // 可空字符串
      "meta_label_en": "Major:",          // 第二行信息标签，可空
      "meta_label_zh": "专业：",
      "meta_value_en": "Robotics Engineering, SUSTech",
      "meta_value_zh": "南方科技大学，机器人工程",
      "bio_en": "…",                       // 个人简介（纯文本）
      "bio_zh": "…",
      "research_en": "Artificial muscles; bioinspired robotics.",
      "research_zh": "人工肌肉；仿生机器人。",
      "education": [                       // 教育经历列表
        { "en": "2023 – 2027 · …", "zh": "2023~2027 · …" }
      ],
      "publications": [                    // 可空数组
        { "title_en": "…", "title_zh": "…", "venue": "…", "badge_en": "…", "badge_zh": "…" }
      ]
    }
  ]
}
```

## 7. 命名与分组规范

- **slug**：`名-姓` 拼音，小写，连字符（如 `peiran-song`、`tianqi-yue`）
- **照片**：`images/people/<slug>.jpeg`，长边建议 ≥400px、文件 ≤300KB
- **分组成员顺序**（生成器按此排序）：
  `pi`（PI，首页/成员页单独区块）→ `postdoc` → `phd` → `master` → `visiting` → `undergraduate` → `admin`
- **角色用语**（沿用现有页面）：
  Postdoctoral Fellow / 博士后；PhD Student / 博士研究生；Master Student / 硕士研究生；
  Visiting Student / 访问学生；Undergraduate Student / 本科生；Lab Administrator / 行政人员

## 8. 运行环境与命令

- Python（含 python-docx、Pillow、lxml）：
  `C:\Users\Administrator\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe`
- 生成成员页与卡片：`tools/build_members.py`（加 `--check` 只预演）
- 从 git 版本重建数据源：`tools/extract_members_from_html.py --from-git`
- 生成论文列表与筛选：`tools/build_publications.py`（加 `--check` 只预演）
- 核对数据完整性：`tools/audit_members.py`
- 全站自检：`tools/check_site.py`
- 统一换行：`tools/normalize_eol.py`
- 无需安装任何依赖；不要引入 npm / 构建工具

## 9. 与用户协作的约定

- **需要用户拍板时，用选择对话框（ask_user_question）**，不要只用文字提问
- 用户验证页面靠**本地刷新浏览器**；不要尝试用浏览器截图自查（沙箱不可用，浪费 token）
- 用户会自己执行 git 提交；助手只在被要求时提供「变更清单 / commit 建议 / 给管理员的话术」
- 改动完成后：给**简略变更清单** + 建议的验证点
- 用户对布局与文案细节要求严格：涉及文案措辞或布局调整时，**先给方案让用户过目**，再动手
- 报告用中文
