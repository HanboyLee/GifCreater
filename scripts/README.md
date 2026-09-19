# 🛠️ GifCreater 工程与自动化脚本索引 (Scripts Index)

本文档是 AI 代理（Agent）与开发人员在日常维护、方案论证、文档核验及构建发布时的**法定工具速查入口**。
**严禁执行全仓库盲目搜索（如无目录限制的 `git grep`），请直接根据本索引调用对应脚本。**

---

## 一、 核心工程辅助工具速查表

| 工具脚本 | 职责与功能 | 标准调用命令示例 |
| :--- | :--- | :--- |
| **`scripts/tools/typesafe_judge.py`** | 🧠 **TypeSafe Jev 语义决策模型**<br>方案讨论、计划选择、歧义裁决 | `python scripts/tools/typesafe_judge.py --state "上下文" --choice-inst "判断问题" -o key1 "描述1" -o key2 "描述2"` |
| **`scripts/tools/check_doc_sync.py`** | 🛡️ **文档与路线图一致性守卫**<br>核验 requirements 与 roadmap 版本对齐 | `python scripts/tools/check_doc_sync.py` |
| **`scripts/tools/extract_ico.py`** | 🎨 **图标生成与多分辨率提取**<br>生成 Windows 原生 16~256px 完整 ICO 链 | `python scripts/tools/extract_ico.py` |
| **`scripts/build/build_release.ps1`** | 📦 **本地 PyInstaller 单文件打包**<br>生成独立的桌面可执行程序 `GifCreater.exe` | `powershell -File scripts/build/build_release.ps1` |

---

## 二、 TypeSafe Jev 极速单行调用规范 (Zero-JSON CLI)

为避免在 Windows PowerShell 中处理复杂 JSON 字符串的引号与转义问题，`typesafe_judge.py` 提供第一公民原生命令行参数：

### 1. Choice 多选裁决（推荐）
```bash
python scripts/tools/typesafe_judge.py \
  --state "当前面临两个方案..." \
  --choice-inst "哪个方案对用户最友好？" \
  -o plan_a "方案 A：彻底拆分" \
  -o plan_b "方案 B：保持现状"
```

### 2. Noul 条件是/否判定
```bash
python scripts/tools/typesafe_judge.py \
  --state "本次提交仅调整了文档和测试" \
  --noul "本次改动是否包含业务逻辑变更？"
```

### 3. Dry-Run 语法预检（不消耗 API / 不发网）
```bash
python scripts/tools/typesafe_judge.py --state "测试" --noul "测试" --dry-run
```

---

## 三、 Windows 环境下的「极速寻址三铁律」

1. **查文件只用索引树，绝不全盘慢扫**：
   - ❌ 严禁 `find /r` 或慢速全盘遍历；
   - ✅ 统一使用 `git ls-files "*keyword*"`（毫秒级基于索引树返回）。
2. **搜内容必须限定子目录，严禁根目录全局拉网**：
   - ❌ 严禁在仓库根目录执行裸命令 `git grep "keyword"`；
   - ✅ 必须指定目标子目录，例如：`git grep "keyword" scripts/` 或 `git grep "keyword" src/`。
3. **环境排查先看配置文件，严禁盲目 import 试错**：
   - 优先查阅 `pyproject.toml` 或 `requirements.txt` 确认当前虚拟环境已安装的包。
