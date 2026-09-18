# 03 - 文档生命周期与同步契约 (Documentation Lifecycle & Sync Contract)

文档是软件系统的第一等公民。严禁“代码已修改而文档未同步”的脱节行为。文档维护遵循严格的四阶段闭环触发机制。

---

## 1. 文档更新的四阶段闭环触发机制 (Four-Phase Closed-Loop Trigger)

```text
  【阶段1：路线图与方案对齐】        【阶段2：原子交付与需求核销】      【阶段4：大版本里程碑结项】
  [查验并锚定 docs/roadmap.md]  ──>  [推进 requirements.md (- [x])] ──> [提升 roadmap.md 基线版本]
  [讨论并输出 spec/ & 要求清单]       [代码/单测/设计文档同一 Commit]     [自动化脚本 check_doc_sync 守护]
```

### 阶段 1：改动前与立项锚定 (Pre-Implementation & Roadmap Alignment)
- **触发条件**：
  - 新增独立功能模块；
  - 架构重构或分层调整；
  - 调整公共 API 签名或修改底层数据结构；
  - 引入或调整核心第三方依赖。
- **强制动作**：
  - **严禁直接修改业务代码**；
  - **路线图比对**：核对新需求是否符合 `docs/roadmap.md` 的当前阶段规划；若涉及优先级插队或合并，同步微调路线图演进阶段；
  - 必须先与用户讨论方案思路，确认达成一致；
  - 在专案根目录 `spec/` 目录下输出或更新规格计划书（如 `v3_refactor_plan.md`、`detailed_design.md`），并在 `docs/requirements.md` 中**强制以 Markdown Task List Checkbox（`- [ ]`）格式追加需求条目**；
  - 获得确认后方可开展编码。

### 阶段 2：改动完成后 (Post-Implementation / Atomic Delivery Phase)
- **触发条件**：
  - 代码实现完毕，且自动化测试（覆盖率 $\ge 90\%$）全部 PASS 之后。
- **强制动作（五件套强绑定同步与 Git Push 红线）**：
  1. **需求文档 Checklist 状态推进**：将 `docs/requirements.md` 中已完成落地的条目从 `- [ ]` 更新勾选为 `- [x]`，并在 Changelog 中追加版本/日期变更记录；
  2. **全局架构图更新**：若调整了工程目录、模块依赖或设计模式，**必须无条件同步更新专案根目录的 `ARCHITECTURE.md`**；
  3. **系统设计文档更新**：在 `docs/design.md` 中追加增量技术实现、数据流图与技术决策记录；
  4. **用户手册同步更新**：若涉及启动命令、命令行参数、环境变量或快捷键变化，**必须同步更新 `README.md` 与 `README_zh.md`**；
  5. **Git Push 同步铁律**：**每次执行 `git push` 前必须确认上述文档已全部同步**。**除非本次提交完全未更改任何需求或功能**（如纯工具脚本、环境调试或代码注释微调），否则未更新需求文档严禁执行 `git push`。

### 阶段 3：轻量级缺陷修复 (Bugfix Phase)
- **触发条件**：
  - 单纯的文字微调、拼写修正、单一明确的轻量 Bug 修复。
- **豁免与追加**：
  - 此类改动**允许免除前置讨论**，以保障敏捷修复；
  - 若 Bug 修复改变了隐式逻辑或数值阈值（如容差参数），需在 `docs/design.md` 的变更历史中追加一行记录，并在 `docs/requirements.md` 对应条目状态中确认。

### 阶段 4：大版本里程碑结项与路线图回写 (Milestone Promotion & Tag Release)
- **触发条件**：
  - 某个规划大版本（如 v3.1、v3.4）在 `docs/requirements.md` 中的所有 Checklist 已 100% 勾选为 `- [x]` 并通过验收。
- **强制动作**：
  - **路线图基线提升**：在同一个发布 Commit 中，同步修改 `docs/roadmap.md` 顶部的“当前基线版本号”；
  - **里程碑归档**：将该版本归入已交付稳定基线，并校准下一阶段近景（Next Horizon）的规划目标；
  - **自动化一致性核验**：执行 `python scripts/tools/check_doc_sync.py` 确保两份文档版本基线完全咬合，严禁版本脱节；
  - **版本 Tag 驱动发布**：经确认无误后，通过推送版本标签触发 CD 自动化部署：
    ```bash
    git tag vX.Y.Z
    git push origin vX.Y.Z
    ```
    由云端流水线全自动打包编译 Windows 独立安装包并生成正式 GitHub Release。

---

## 2. 专案文档集中管理目录映射表

| 文档定位 | 物理路径 | 维护职责 |
| :--- | :--- | :--- |
| **全局架构全景图** | `ARCHITECTURE.md`（专案根目录） | 系统分层、技术选型、目录结构、数据流图（全局唯一法定全景文档）。 |
| **产品演进路线图** | `docs/roadmap.md` | 长期演进里程碑、战略愿景、架构扩展插槽、大版本结项基线。 |
| **需求与规格规格书** | `spec/`（专案根目录） | 阶段性大中型方案的立项规划、详细设计、执行路线图与验证方案。 |
| **系统需求与详细设计** | `docs/requirements.md`<br>`docs/design.md` | 业务需求 Checklist（`- [x]` / `- [ ]`）基线文档、详细设计与技术决策收口文档。 |
| **用户与开发者手册** | `README.md`<br>`README_zh.md` | 面向终端用户与开发者的双语安装、运行与使用指南。 |
| **AI 代理协作规则** | `AGENTS.md`<br>`.agent/rules/*.md` | AI 行为红线、质量门禁、Vibe Coding 约束与工程规范。 |

---

## 3. GitHub Releases 国际化语言规范 (English-Only Releases)

- **纯英文红线**：所有面向公众的 GitHub Releases（包括发布标题、Release Notes 正文、Changelog、构建产物描述）**必须 100% 使用纯英文（English）撰写，严禁包含任何中文**。
- **CI/CD 流水线守护**：`.github/workflows/release.yml` 中自动触发的 Rolling Release 及 Milestone Release 模板必须严格保持英文标准。

