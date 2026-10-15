# BIRD Lab 网站维护手册（给管理者）

> 这份手册是给你（网站管理者）看的。它决定你每次维护花多少 token / 多少钱。

---

## 0. 最重要的一件事：怎么"新开对话"才省钱

**费用 ≈ 会话上下文长度 × 轮数。** 历史越长，每一轮越贵（每问一次，前面全部对话都要重新发一遍）。

| 做法 | 结果 |
|---|---|
| ✅ **在左侧工作区（BIRD Lab Web）里「新建会话」** | 全新空上下文；工作区不变，`AGENTS.md` 自动加载 → **这才是省钱的做法** |
| ❌ 点「在新对话中分支」（fork） | 它会把**当前对话的全部历史复制过去** → 上下文一样大甚至更大，**不省钱** |

**记住：要"空"的新会话，不要"带历史"的分支会话。**

新会话里我不记得之前发生的事，所以：
- 重要结论都写在文件里（`AGENTS.md`、本手册、`data/*.json`）
- 你只需开头一句：`按 HOWTO.md 操作，任务：……`

---

## 0.5 两个时点都要同步 main（很重要）

| 时点 | 命令 | 为什么 |
|---|---|---|
| **开工前** | `bash tools/sync.sh` | 让改动基于 main 最新；否则可能基于旧结构改动、甚至覆盖别人已合并的内容 |
| **推送前** | `bash tools/publish.sh "日常推送"` | 脚本内部会自动再同步一次（你干活期间 main 可能又更新了） |

只做一个都不够：**只做推送前** → 整段工作基于旧代码，冲突多还可能悄悄覆盖别人；**只做开工前** → 工作期间 main 又变了，推送时照样落后。

> 顺序建议：`sync.sh`（开工）→ 让助手改内容 → `publish.sh "说明"`（收工，自动生成+自检+同步+提交+推送）

## 1. 完全不用找 AI 的操作（0 成本）

| 你要做的事 | 操作 |
|---|---|
| **改完内容 → 提交并推送（全自动）** | `bash tools/publish.sh "日常推送"` —— 脚本会自动生成页面、跑全站自检、提交、推送 |
| 只想生成页面 | 运行 `tools/build_members.py`、`build_news.py`、`build_publications.py`、`build_chrome.py` |
| 只想体检 | 运行 `tools/check_site.py` |

在 Git Bash / PowerShell 里运行 Python 的写法：

```powershell
# 如果 python 已在 PATH 里
python tools\build_members.py

# 若提示找不到 python，用 DSH 自带的运行时
& "C:\Users\Administrator\.dsh\dsh-runtimes\dsh-primary-runtime\dependencies\python\python.exe" tools\build_members.py
```

---

## 2. 需要找 AI 时的三条原则

1. **开新会话**（见第 0 节，别用 fork）
2. **一次说全**：文件位置 + 要什么 + 期望结果，不要让我去猜或到处找
3. **做完就结束会话**：别在同一个会话里接着聊别的事

另外：
- **验证由你做**（刷新浏览器看一眼），不要让我截图自查（沙箱里不可用，纯浪费）
- 需要"多轮摸索"的大改动，一次一个会话做完就收尾

---

## 2.5 默认规则（一句话指令时我会自动决定的）

当你说「任务：新增成员，材料在 inbox」时，我会按下面的默认规则直接推进，**不再逐项问你**；不合适的地方你在验收时说一句纠正即可。

**成员**
- slug：中文名转拼音（名前姓后，小写连字符），如 胡相南 → `xiangnan-hu`
- 英文名：优先用材料里给的；没有则按拼音写（如 Xiangnan Hu）
- 角色/分组：以你指令里写的为准（「本科」→ Undergraduate Student / 本科生，undergraduate 组）
- 照片：优先取 Word 内嵌照片，其次取 inbox 里的图片
- 简介/研究方向：材料只有一种语言时，我补另一种语言的翻译
- **没写专业/院系**：改用材料里能确定的信息（如「所属院校：华中科技大学」）；确实没有就省略该行（不会留空行）
- **论文只给了 Google Scholar 链接**：论文区显示一行「Google Scholar: 链接」
- 自动生成个人页与成员卡片，按分组排序插入

**新闻**
- 日期：取自文件名或你的指令（`2026.10.9-xxx.png` → 2026.10.09）
- 配图：自动归档到 `images/news/`，PNG 自动转 JPG
- 多张图片：默认「第 1 张完整 + 其余下排叠压」拼成一张（要四宫格等分就说「拼四宫格」）
- 照片偏暗：默认按平均亮度略微调亮（最多 +25%），不需要就说「不要调亮」
- tag：按内容推断（Team Activity / Academic Talk / Exchange Visit 等）
- 上首页：默认上新（不要就说「不上首页」）
- 正文：你给了用你的；没给则我草拟（验收时可改）

**论文**
- 研究方向 / 关键词：按标题与期刊推断；新关键词自动补进筛选下拉
- 成员只有主页链接（Google Scholar / ORCID 等）：写进 `scholar_url`，论文区显示链接

**我仍会集中问你一次的情况**
- 材料没写角色 / 身份（本科生？硕士？访问？）
- 材料没写姓名，或一份材料里有多人
- 缺照片而你要求配图
- 材料内部信息互相矛盾
## 2.6 执行效率要求（准确优先，绝不为省而省）

**总原则：正确性 > 效率。** 宁可多一轮核对，也不要产出错误内容。

**应该做的（这些是省 token 的正确姿势）**
- 把能合并的步骤合并：解析 → 归档 → 写数据源 → 生成 → 自检，尽量用一条命令 / 一次脚本完成
- 不把大文件整份读进上下文：用脚本只提取需要的字段
- 不读图片（视觉 token 贵）；需要确认照片时由你来看
- 变化点不确定（角色 / 姓名拼音 / 日期 / 是否上首页）→ **一次性集中问清楚**，不要猜
- 报告控制在 5 行以内，但必须包含：改了什么 / 你要验证什么 / 待你决策什么

**绝不允许为了省 token 而省略的**
- 生成后跑 `tools/check_site.py` 自检（链接、图片、双语配对、标签配对）
- 关键字段核对：姓名、邮箱、日期、URL 是否有效可访问
- 中英双语必须成对；缺一边要补齐（不得只留一种语言）
- 材料归档与规范命名（`member materials/`、`images/people/<slug>.jpeg`）
- 改动清单与验证点说明
- 不得删改你提供的文案内容（除非你要求调整）

**避免"试探式"调用**：先想清楚再执行，不要"跑一条看看结果再说"。

## 3. 指令模板（复制后改几个字即可）

### 通用执行要求（已写入本手册 2.6 节与 AGENTS.md，**默认生效——无需每次复制**）

**你平时只需一行指令**，例如：

```
按 HOWTO.md 操作。任务：新增成员（本科，英文名 Xuefeng Liu），材料在 inbox/BIRD Lab个人简介-刘学峰.docx
```

下面的模板只是「任务内容怎么写」的参考；执行约束（自检、字段核对、双语补齐、归档、报告长度）都已默认生效。
只有特殊情况才需要额外叮嘱，例如：材料特别大、或明确不要读某张图片。

```
先给我 3 条以内的执行计划；执行时把能合并的步骤合并，避免逐步试错。
以准确为先：该跑的自检、该核对的字段、该补的双语都不能省。
不要读整份大文件、不要读图片；不确定的点集中问我一次。
完成后跑自检，报告 5 行以内（改了什么 / 我验什么 / 待我决策）。
```


### ① 新增成员
```
按 HOWTO.md 操作。新增成员：胡相南（本科，英文名 Xiangnan Hu）
材料在 inbox/BIRD Lab个人简介-胡相南.docx，简介中英已给全
完成后跑生成器与自检，给我变更清单
```

### ② 修改某位成员的信息
```
按 HOWTO.md 操作。把 data/members.json 里 xiangnan-hu 的
bio_zh 改成「……」，bio_en 改成「……」
改完跑 build_members.py 与 check_site.py
```

### ③ 新增新闻
```
按 HOWTO.md 操作。新增新闻：日期 2026.11.02
标题「中文」/「English」，正文「中文」/「English」，tag 用 Team Activity，要上首页
图片在 inbox（1 张）
```

### ④ 改导航 / 页脚
```
按 HOWTO.md 操作。在 tools/chrome.py 的导航里加入「Gallery / 相册」指向 gallery.html，页脚同步
改完跑 build_chrome.py 与 build_members.py
```

### ⑤ 新增论文
```
按 HOWTO.md 操作。在 data/publications.json 增加一篇：
标题「中文」/「English」，DOI …，年份 2026，研究方向 suction-adhesion
关键词 gripping,soft-robotics，作者：……
```

### ⑥ 拼活动照片
```
按 HOWTO.md 操作。把 inbox 里 4 张活动照片拼成一张新闻配图（图 1 完整，其余可叠压）
输出 images/news/2026-11-02.jpg
```

---

## 4. 场景成本对照（估算）

| 场景 | 在新会话里做 | 在已经很长/旧会话里做 |
|---|---|---|
| 改一位成员简介 / 研究方向 | 2–5K | 几十万 |
| 新增一位成员 | 5–15K | 几十万 |
| 新增一条新闻 | 5–10K | 几十万 |
| 改导航 / 页脚（全站） | 3–6K | 几十万 |
| 新增论文 | 3–6K | 几十万 |

（K = 千 token。**同样的活，在哪个会话做，比怎么做更决定成本。**）

---

## 5. 零成本的好习惯

- **材料规范**：Word 命名 `BIRD Lab个人简介-中文名.docx`；照片尽量命名成拼音（如 `xiangnan-hu.jpeg`）→ 省掉我的重命名与判断
- **一次给全**：中英双语、角色、日期、是否上首页
- **攒批**：一周的需求集中到一个会话里做完
- **报告要短**：让我只回“改了什么 / 验证什么 / 下一步”三段
- **不要让我总结历史**（那要把很长的对话读一遍）

---

## 6. 脚本速查

| 脚本 | 用途 |
|---|---|
| `tools/build_members.py` | 由 `data/members.json` 生成成员页 + 成员卡片 |
| `tools/build_news.py` | 由 `data/news.json` 生成新闻页 + 首页卡片 |
| `tools/build_publications.py` | 由 `data/publications.json` 生成论文列表与筛选 |
| `tools/build_chrome.py` | 全站导航栏 / 页脚 / 二维码弹窗同步 |
| `tools/check_site.py` | 全站自检（链接、图片、双语、标签配对） |
| `tools/audit_members.py` | 成员数据字段完整性核对 |
| `tools/inbox_ingest.py` | 解析 `inbox/` 里的成员 Word、归档、生成草稿 |
| `tools/make_collage.py` | 活动照片拼图（主图 + 下排叠压） |
| `tools/make_grid.py` | 活动照片等分宫格拼图（默认 2x2 四宫格，可整体调亮并另存单张） |
| `tools/normalize_eol.py` | 换行统一为 LF（一般不需要手动跑） |
| `tools/publish.sh` | **一键发布（Git Bash 版，推荐）**：`bash tools/publish.sh "增加了成员"` |
| `tools/publish.ps1` | 一键发布（PowerShell 版）；正确运行方式见第 7 节，**不要右键运行**（窗口一闪而过看不到报错） |
| `tools/sync.ps1` | 开工前同步：拉取 main 最新并变基（fetch + rebase） |

数据源（只改这几个文件，不要手改生成的页面）：
- `data/members.json` → 成员
- `data/news.json` → 新闻
- `data/publications.json` → 论文
- `tools/chrome.py` → 导航栏 / 页脚

---

## 7. 发布流程

**① 开工前先同步（管理员的要求，很重要）**

```bash
git fetch origin            # 必须！否则 origin/main 还是旧引用，rebase 等于空转
git status                  # 工作区要干净（有改动先提交）
git checkout update-tianqi
git rebase origin/main      # 把本地提交重放到 main 最新之上
```

- 也可以直接跑脚本：`.\tools\sync.ps1`（自动 fetch → 检查 → 变基，冲突会停下提示）
- 有冲突不要硬来，找管理员或助手

**② 改内容 → 生成 → 自检**

```
改数据/材料 → 跑生成器 → 跑 check_site.py
```

**③ 提交并推送（一行命令，自动生成 + 自检）**
脚本会自动：由数据源重新生成页面 → 跑全站自检（不通过就停下不提交）→ 暂存 → 提交 → 推送

```bash
# 推荐：Git Bash 版（和你平时手动提交一样，只是自动化）
bash tools/publish.sh "增加了成员"

# 或者 PowerShell 版（必须能看到输出；不要用「右键 → 使用 PowerShell 运行」）
powershell -NoProfile -ExecutionPolicy Bypass -File tools/publish.ps1 -Message "增加了成员"
```

- 若脚本没有任何反应 / 窗口一闪而过：改用上面的 Git Bash 版；先跑 `bash -n tools/publish.sh` 只检查语法
- 脚本会：拉取远程 → 规范化换行 → 暂存 → 提交 → 推送（普通推送失败会自动试 `--force-with-lease`）→ 打印给管理员的话术
- **出错时脚本会停下等你看**，把屏幕上的信息截图发给助手即可

- 想减少 main 上的 commit 数：推送前把本地多个提交压成一条
  ```bash
  git reset --soft origin/main     # 撤销提交但保留全部改动
  git commit -m "增加了成员"        # 只留下一条
  ```
- 如果变基改写过已推送的历史，推送用：`git push --force-with-lease`

**④ 通知管理员合并**（`publish.ps1` 会打印可直接转发的话术）

- 你不是仓库 owner：**推送到 `update-tianqi` 分支**，然后请管理员合并到 `main` 并发布
- `publish.ps1` 跑完会直接打印一段可以直接发给管理员的话（含 commit 号）
- **commit message 保持简短中文**（仓库是公开的，人人可见，不要写细节）：
  `增加了成员`、`增加了新闻`、`修改了信息`、`更新了论文`、`调整了页面`；
  不要写 `feat:` / `chore:` 前缀，不要罗列文件名或改动细节；
  一次提交含多类改动时用最概括的一条，如 `增加了成员和新闻`
- 不要推 `main`、不要动 `.git/`、`CNAME`
