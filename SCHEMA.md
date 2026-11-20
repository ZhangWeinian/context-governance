# SCHEMA — context 通用约定（agent 优先）

> 这是两个 context 仓的**唯一通用版本**，位于 `governance` submodule。
> 各仓根目录的 `SCHEMA.md` 只写**本仓差异**（范围、目录、示例），不重复本文件。
> 预算数字统一在 `governance/budgets.toml`，本文件不复述具体阈值。

## 目录模型

| 路径 | 放什么 | 格式 | 必需 |
|---|---|---|---|
| `STATE.yaml` | 当前状态：focus/doing/blocked/next | YAML | 是 |
| `OPEN.yaml` | 未决项（id/question/since/status/project/resolution） | YAML | 是 |
| `INDEX.md` | 路由表：任务关键词 → 文件 | Markdown 表格 | 是（自动生成） |
| `DECISIONS/NNNN-*.md` | 不可变决策（MADR） | md + front matter | 是 |
| `NOTES/<topic>.md` | 可验证事实、坑、速查 | md + front matter | 是 |
| `PROJECTS/<name>.md` | 项目状态（有项目的仓才需要） | md + front matter | 视仓而定 |
| `bin/` | 本仓工具脚本（可执行，入 git，不在 PATH） | bash/python | 视仓而定 |
| `data/` | 二进制/大件（不入 git） | 任意 | 否 |

## 读取协议（开场按此顺序，勿通读）

| 步 | 读什么 | 预算 | 目的 |
|---|---|---|---|
| 1 | `STATE.yaml` + `OPEN.yaml`（+ 车道） | `state.recent_max` 等，见 budgets | 现在在做什么、有哪些未决 |
| 2 | `INDEX.md` | `index.max_bytes` | 关键词 → 文件路由 |
| 3 | 当前项目的会话接力块（若有） | 目标 ≤1KB（人工约定） | 上一次做到哪、下一步 |
| 4 | 按需：相关 `DECISIONS/`、`NOTES/` | 按任务 | 避免与既有决策冲突 |
| 5 | 需要历史时才 `git log/show` | — | 正文只写当前有效事实 |

原则：**先定址再展开**。不要一次读完整个 context；体量以 `ctx-check` 输出为准，不写死数字。

## front matter（所有 md 必须）

```yaml
---
id: D-0001            # D- 决策 / N- 笔记 / P- 项目；全局唯一
title: 一句话标题
status: active|accepted|superseded|archived
updated: 2026-11-18
tags: [toolchain, gcc]
links: [NOTES/build-env.md]   # 可选，相对路径，必须存在
supersedes: D-0007            # 可选：仅 DECISIONS，被取代的旧决策
---
```

## 写法

- 一个文件一个主题；单文件大小受 `budgets.toml` 约束；单节保持在 60 行内（人工约定）。
- 决策只增不改；变更写新篇并标 `supersedes`，旧篇置 `superseded`。
- 正文只写当前有效事实；历史用 `git log/show` 查，不抄进正文。
- 引用用相对路径链接，不复制内容。
- 状态只写 `STATE.yaml` / `OPEN.yaml`，不建 TODO.md 之类平行文件。
- **并发编号**：`OPEN.yaml` 的 `O-NNN` 与 `DECISIONS/` 的 `D-NNNN`，写入前取当前最大号 +1，写入与提交在同一轮完成（2026-11-18 发生过 O-011 撞车）。
- **ADR 克制**：只记**有争议或不可逆**的选择（含反转）；参数微调、流程细化直接改 SCHEMA/NOTES。
- **规则与事实分离**：`AGENTS.md` 只放规则；路径、命令、端口、状态进 context（D-0012）。

## PROJECTS 页面骨架（本仓有 `PROJECTS/` 时适用）

叶子项目页必须在 front matter 之后第一段给出：

```markdown
## 会话接力
- 上次：2026-11-18｜<焦点>｜<一句话结论>
- 下一步：<1–3 条，可执行>
```

- 结构页在 front matter 写 `role: structure`（`ctx-lint` 据此豁免）；其余页缺块即失败。
- 父页只写结构、跨项目约定与子系统索引，不写具体项目进度。

## OPEN.yaml 条目字段

| 字段 | 必填 | 说明 |
|---|---|---|
| `id` | 是 | `O-NNN`，写入前取最大号 +1 |
| `question` | 是 | 一句话，必须可判定 |
| `since` | 是 | 起始日期 |
| `status` | 是 | `open` / `blocked` / `resolved` |
| `project` | 否 | 关联项目页 |
| `links` | 否 | 关联 DECISIONS/NOTES 相对路径 |
| `resolution` | 否 | `resolved` 时必填 |

## 维护：四条机制

### 1) 近因优先

- 「会话接力」块 = 该项目唯一的最新事实；`STATE.recent` = 全局最近事实（上限 `state.recent_max`）。
- 不按时间通读；需要历史才 `git log -p -- <file>` 或 grep。

### 2) 就地更新 vs 新开一篇

| 类型 | 更新方式 | 为什么 |
|---|---|---|
| `NOTES/*`、`PROJECTS/*` | 就地改正文，旧值交给 git | 同一事实只留一个当前版本 |
| `DECISIONS/*` | 新开一篇 + `supersedes`，旧篇置 `superseded` | 决策要留理由，不能被静默改写 |
| `STATE/OPEN` | 直接改（sweep 兜底提交） | 描述"现在" |

结论反转时，正文首行留：`> 2026-11-18 更新：<旧结论> 已作废 → <新结论>`。

### 3) 写前查重

- 先 `ls NOTES/` + `grep -ril '<关键词>' .`，命中同主题就改那篇。
- 文件名以主题域开头，便于判断归属；同一事实只写一处，跨文件用链接。

### 4) 规模与体检

- 超 `budgets.toml` 的 `*_max_lines` / `*_max_bytes` → 拆分（`ctx-budgets` 会报）。
- `INDEX.md` 由 `ctx-index` 生成，禁止手改；`ctx-sweep` 提交前自动重生成，`ctx-check` 校验一致性。
- 收尾跑 `ctx-check`：未提交文件、lint、INDEX 一致性、STATE 一致性、待推送、重复标题、陈旧项一屏看完。

## OPEN 的写入：只用 `ctx-open`

```bash
ctx-open add "<问题>" [project]
ctx-open edit <O-NNN> --question "…" --resolution "…"
ctx-open done <O-NNN> "<说明>"
ctx-open block <O-NNN> "<原因>"
ctx-open list [open|resolved|all]
ctx-open show <O-NNN>
# 一次改多条（单次加锁、单提交），字段限 question/status/resolution/project
echo '[{"id":"O-006","project":"swarm-service"},{"id":"O-007","status":"resolved","resolution":"…"}]' \
  | ctx-open batch --dry-run
```

- 内部 `flock` 加锁；只提交 `OPEN.yaml` 这一个文件；编号与字段由脚本保证，`ctx-lint` 再独立校验。
- 默认根由 cwd 推断：显式 `CTX_ROOT` > 当前目录（有 `OPEN.yaml` + `SCHEMA.md`）> `~/profile/context`；在 workspace 里裸调不会误写 profile。

## 车道（GitHub Issues）

一条车道 = 一个 issue（label `lane` + 项目标签），标题形如 `lane: <project> — <focus>`。

| 概念 | Issues 表达 |
|---|---|
| project | 标题前缀 + label |
| focus | 标题 `—` 之后 |
| by | assignee |
| lease | label `lease` + 评论 `claim by … at … · TTL 24h` |
| 释放 | 去 label/assignee + 评论 `release at …` |
| 过期接管 | 评论 `takeover by … · 原持有者 …`（一律显式） |

```bash
lane list | lane show N | lane claim N | lane release N
```

- 开工：claim 自己的 issue；命中别人在跑的车道直接读，不必问。
- 「下一步」写项目页，不写 issue 标题。
- **不要新建 `LANES/*.yaml`**：YAML 车道 2026-11-20 已停用，`ctx-claim`/`ctx-release` 只报错指向 `lane`。

## 决策格式（MADR 4.0 + adrinaline）

- 路径 `DECISIONS/NNNN-slug.md`，front matter：`id / title / status / date / updated / tags / links`。
- 正文标题：`Context and Problem Statement`、`Considered Options`、`Decision Outcome`、`### Consequences`、`More Information`。
- 关系：`supersedes: [18]`、`superseded-by: [22]`（数字数组），双向必须成对；`adr check` 与 `ctx-domain` 都查。
- 新建：`adr new "<english-slug-title>" --dir DECISIONS`。标题用英文（adrinaline 只对 ASCII 造文件名）。
- **必须走 `~/profile/bin/adr`**（PATH 最前，覆盖 uv 装的原版）：`new` 前按 `max(<100 的编号)+1` 选号并跳过已占用，生成后重命名 + 写回 `id: D-00NN`；其余子命令透传。原版只按全局 max+1 续号，遇到 0100 这类异常编号会产出 0101。
- `DECISIONS/` 里编号 ≥0100 属异常，`ctx-domain` **R8** 直接 ERROR；历史异常请归档到 `DECISIONS/archive/` 而不是 renumber。
- 编号允许缺口，不 renumber（会让 `D-00NN` 引用失效）；number-gap 属预期 warning。

## 读写边界

- 同机多会话没有 git merge：后写覆盖前写。并发安全靠文件隔离（INDEX 自动生成、车道在 Issues）与共享文件只做局部 edit 后立刻 `ctx-commit`。
- 写：一个事实一个 `ctx-commit`；跨多文件长事务先 `touch .git/ctx-lock`。
- 读：按读取协议；不要为了"了解全貌"读完整个 context。

## STATE.yaml 字段

| 字段 | 含义 |
|---|---|
| `owner` | 当前负责人（人） |
| `updated_by` | 最后写入者 `<host>/<agent>` |
| `updated` | 最后更新时间（ISO 8601） |
| `recent` | 全局最近事实（上限 `state.recent_max`） |
| `blocked` | 阻塞项（等用户/等外部） |
