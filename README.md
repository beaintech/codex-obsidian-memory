# Codex Obsidian Memory

一个由 Markdown 文件组成、可在 Obsidian 中直接查看和维护的 Codex 跨项目记忆库。

## 在 Obsidian 中使用

### 当前电脑

1. 打开 Obsidian。
2. 选择 **Open folder as vault / 将文件夹作为仓库打开**。
3. 选择 `/Users/bea/Desktop/obsidian`。
4. 打开 `Codex Memory/00 - Start Here.md`。

不需要导入或转换文件；Obsidian 会直接把文件夹中的 Markdown 当作笔记。

### 另一台电脑

```bash
git clone https://github.com/beaintech/codex-obsidian-memory.git
```

然后在 Obsidian 中选择克隆得到的 `codex-obsidian-memory` 文件夹作为 vault。

## Codex 全局入口

本机的 `~/.codex/AGENTS.md` 应包含一条指向本地 `Codex Memory/00 - Start Here.md` 的指令。换电脑或改变克隆位置后，需要把该绝对路径更新为新位置。

## 安全

不要在仓库中保存密码、API 密钥、访问令牌、私钥或恢复码。即使 GitHub 仓库设为私有，也应使用系统钥匙串或专用密码管理器保存认证秘密。

