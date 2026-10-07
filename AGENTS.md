# June Smart English General Studynote — 仓库维护规则

本目录是 `june-smart-english-general-studynote` 的完整维护源，同时是独立 Git 仓库的根目录。GitHub 仓库为 [EnglishJune/june-english-studynotes](https://github.com/EnglishJune/june-english-studynotes)。仓库名称与 skill 名称不同；保留 `SKILL.md` 中的 skill 名称及内部相对路径。

## 文件职责与修改范围

- `README.md` 面向 GitHub 使用者；`SKILL.md` 定义 agent 执行学习笔记任务的流程；本文件定义源码维护规则。
- `scripts/`、`references/`、`config/`、`schemas/`、`assets/` 和 `agents/` 是本 skill 的运行源码或功能资产。`tests/` 和 `scripts/render/pdf_smoke_test.py` 是只留在本地的维护测试，必须保留，但不纳入 Git 跟踪和上传。数据库、字体、模板及人工修改必须保留。
- 修改本 skill 不自动修改其他 skill、plugin、个人安装或网站，也不自动执行跨体系同步。
- 保留 General 自己的教学、翻译、词汇、IPA、CEFR、HTML/PDF 与格式行为。只有用户明确要求时才改变功能；不因其他 TE skill 或 plugin 的变化自动替换本 skill 的实现。
- 按改动验证相关消费者。纯文档修改检查文档和 skill 入口；程序、契约或排版修改执行对应检查，排版修改查看实际渲染结果。

## 位于本地 AI_Skills 项目内时

本机维护位置是 `AI_Skills/skills/src/june-smart-english-general-studynote/`。此时本 skill 同时受项目根目录 `AGENTS.md` 和 `skills/AGENTS.md` 管理；独立 Git 仓库不解除这些上层规则。若 Git 工具或 agent 只识别当前仓库根目录，仍需读取实际存在的这两份上层说明。

从 skill 目录向上三级进入 `AI_Skills` 根目录，使用项目维护工具。修改前保存本 skill 的编辑前状态：

```bash
./update-release skill june-smart-english-general-studynote --backup-only
```

验证后只打包、不更新个人安装：

```bash
./update-release skill june-smart-english-general-studynote --no-install
```

用户明确要求更新个人安装时，执行：

```bash
./update-release skill june-smart-english-general-studynote
```

项目的 `skills/releases/`、`skills/backups/` 和 `skills/verification/` 保存本 skill 的发布、备份与验证资料，位于这个 Git 仓库之外。日常修改本目录的维护源；不在生成 ZIP 或个人安装副本中单独修复。

## 独立 GitHub 管理与独立克隆

- 在本目录进行 Git 提交、拉取与推送，只同步本仓库文件。默认分支为 `main`，远程为 `origin`。保留远程已有历史，先检查本地改动再整合远程变更；不要用强制推送覆盖历史。
- GitHub 同步保存源码版本；本地打包、安装以及 GitHub Release 是各自独立的操作。提交或推送不代表已经更新个人安装或发布 ZIP。
- `.gitignore` 排除本地测试、调试和生成资料；不要强制添加这些文件。`.gitattributes` 控制 GitHub 自动生成的源码 ZIP，只保留 skill 运行内容和必要许可，排除 README、AGENTS 和 Git 配置等仓库维护文件。发布 tag 必须指向包含这些规则的提交；旧 tag 的下载包不会自动更新。
- 发布 ZIP 内不包含本地测试脚本，公开的 SKILL 和 references 不得要求调用它们。PDF 环境验证使用实际生成的文档完成；保留运行前检查、数据校验、编译错误处理和必要日志能力。
- 克隆到 `AI_Skills` 之外时，本仓库可独立维护，不假设存在上层管理文件、项目发布工具或私人 plugin。依照本仓库的 `SKILL.md` 和相关 references 运行及验证；安装时保留 skill 名称 `june-smart-english-general-studynote`。
- 运行输入、学习笔记输出、缓存、本地环境、个人配置和 secrets 不纳入源码提交。第三方资源保留原有许可说明，不擅自改变作者的许可选择。
- 本机 shell 使用 `/bin/bash`；命令依赖配置的 PATH、Python、Homebrew、pyenv 或 Conda 时，在同一次 Bash 调用中先 `source ~/.bashrc`，路径重要时以 `command -v` 核实。运行 Python 检查使用 `-B`，避免生成源码缓存。其他独立克隆环境按实际可用 runtime 验证路径。
