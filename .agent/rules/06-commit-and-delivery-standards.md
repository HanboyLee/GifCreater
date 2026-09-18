# 06 - AI 代理提交规范与交付契约 (Commit & Delivery Contract)

在 AI 辅助开发与 Agent Vibe Coding 模式下，AI 代理独立承担功能开发、缺陷修复与代码提交。为保障代码演进的高可追溯性、工程严谨性与团队交付质量，所有进入本专案的 AI 代理必须严格遵循本提交规范与交付契约。

---

## 1. 约定式提交规范 (Conventional Commits Standard)

AI 代理在执行 `git commit` 时，**必须严格遵循 Conventional Commits 规范**。严禁提交 `update`、`fix bug`、`wip` 等无实质信息量的提交信息。

### 1.1 语法结构
```text
<type>(<scope>): <简明准确的动宾描述>

[可选的正文描述 (Body)：详细说明修改缘由、架构取舍或关联需求]
[可选的脚注 (Footer)：关联关闭的 Issue 或 PR 编号]
```

### 1.2 Type 类别枚举（严格收口）
| Type | 中文说明 | 典型适用场景 |
| :--- | :--- | :--- |
| **`feat`** | 新增特性 | 实现了新的业务需求、算法能力或界面组件。 |
| **`fix`** | 缺陷修复 | 修复了 Bug、异常边界、内存泄漏或逻辑缺陷。 |
| **`docs`** | 文档变更 | 仅修改文档（需求 Checklist、架构说明、设计文档、README 等）。 |
| **`test`** | 测试相关 | 新增单元测试、完善边界测试用例或调整质量门禁。 |
| **`perf`** | 性能优化 | 编解码提速、内存开销缩减、异步优化或 CI 流水线提速。 |
| **`refactor`** | 代码重构 | 不改变外部行为与 API 约定的代码结构重组或优化。 |
| **`chore`** | 构建/工程 | 依赖升级、配置文件变动、辅助工具脚本更新。 |
| **`ci`** | 持续集成 | 修改 GitHub Actions 工作流、打包脚本或发布流水线。 |

### 1.3 Scope 作用域枚举
提交信息中的 `(<scope>)` 必须明确指出本次变更所处的核心模块：
* **`core`**：核心算法引擎（图像处理、动图切片、调色板、编码合成）。
* **`ui`**：桌面 GUI 交互（Fluent 界面、画板、胶卷、时间轴、主题）。
* **`wechat`**：微信表情包压缩与微信专属合规算法。
* **`docs`**：专案文档体系（需求、架构、设计、路线图）。
* **`test`**：自动化测试套件与覆盖率配置。
* **`ci`**：CI/CD 自动化流水线。
* **`spec`**：立项规划书与规格说明。

### 1.4 规范提交示例
* 正确示例（英文/中英结合）：
  - `feat(core): implement adaptive palette reduction algorithm`
  - `fix(ui): resolve canvas flickering during frame dragging`
  - `docs(req): check off v3.5 preset requirements and update changelog`
  - `perf(ci): decouple heavy packaging from regular branch push`
  - `test(wechat): add in-memory mock tests for 500KB boundary check`
* 错误示例（严禁提交）：
  - `git commit -m "update code"`
  - `git commit -m "fix bug"`
  - `git commit -m "agent commit"`

---

## 2. Agent 交付定义清单 (Definition of Done - DoD)

在 AI 代理声明功能完成并执行提交前，**必须在本地逐项核对并全部满足以下 6 大门禁**。若有任何一项不达标，严禁提交代码，严禁向用户汇报完成：

```markdown
- [ ] 1. 静态检查门禁 (Lint Gate)：本地执行 `ruff check .`，结果必须为 `All checks passed!`（0 警告、0 死导入）。
- [ ] 2. 单元测试门禁 (Test Gate)：本地执行 `pytest tests/` 必须 100% 全部通过，无异常崩溃。
- [ ] 3. 覆盖率硬指标 (Coverage Gate)：核心模块行覆盖率必须严格达到 >= 90%，严禁低于阈值。
- [ ] 4. 防作弊与环境干净度 (Anti-Cheat & Cleanliness)：
      - 严禁假单测（无 `assert True` 等敷衍断言，必须校验真实业务边界）；
      - 测试图像必须在内存（RAM）中动态生成，零磁盘测试媒体提交；
      - `git status` 必须绝对干净，严禁包含 `*.exe`、`dist/`、`build/`、`__pycache__/` 或素材图。
- [ ] 5. 文档强绑定同步 (Doc Sync)：
      - 在 `docs/requirements.md` 中将对应功能状态由 `- [ ]` 推进为 `- [x]` 并追加变更日志；
      - 若涉及模块结构变化，同步更新根目录 `ARCHITECTURE.md`；
      - 若涉及技术实现细节，同步更新 `docs/design.md`。
- [ ] 6. 原子化提交 (Atomic Delivery)：
      - 业务代码、单测脚本与对应文档更新必须放入同一个 Commit 交付，保持状态 100% 吻合。
```

---

## 3. 标准交付汇报模板 (Proof of Delivery Report)

AI 代理在完成功能交付并向用户（开发者）汇报时，**杜绝任何“我已修复”、“功能已完成”等主观黑盒表述**。汇报必须统一采用以下结构化交付凭证：

```markdown
### 交付凭据报告 (Proof of Delivery)

1. **改动文件清单 (Changes Delivered)**:
   - 业务代码：`src/...`
   - 自动化单测：`tests/...`
   - 需求与设计文档：`docs/requirements.md` (`- [x]` 已核销), `docs/design.md`

2. **质量门禁核验证据 (Quality Verification)**:
   - **Ruff 静态扫描**：`ruff check .` -> `All checks passed!`
   - **测试与覆盖率**：`pytest` 通过数量（如 `104 passed`），行覆盖率真实数据（如 `95.78% >= 90%`）。

3. **文档核销凭据 (Requirement Check-off)**:
   - 已将需求文档中的条目从 `- [ ]` 推进为 `- [x]`：
     - `- [x] <需求名称/功能点描述>`

4. **确定性复现与验证指引 (How to Verify)**:
   - 提供明确的 CLI 执行命令或 UI 操作路径，便于用户一键复现和核验效果。
```

---

## 4. CI/CD 提交分流与发版契约 (Release & CD Contract)

AI 代理必须清楚区分“日常功能提交”与“正式大版本发版”的操作边界：

1. **日常功能提交（持续集成 CI）**：
   - 满足 DoD 后，执行普通 Commit 与 Push：
     ```bash
     git add .
     git commit -m "feat(core): ..."
     git push origin main
     ```
   - **行为**：触发 50 秒极速 CI（自动跑 Ruff 检查、文档双向校验、90% 单测覆盖率门禁），**绝不触发重型打包**。
2. **正式版本发布（持续部署 CD）**：
   - 仅当某大版本（如 v3.5.0）在需求文档中的需求全部变为 `- [x]`，且经过路线图回写闭环校验后，方可打版本 Tag：
     ```bash
     git tag vX.Y.Z
     git push origin vX.Y.Z
     ```
   - **行为**：流水线捕获 `v*` 标签，自动编译 Windows 独立 exe 并在纯英文 GitHub Releases 发布。
