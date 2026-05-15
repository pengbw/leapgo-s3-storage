# GitHub 推送工作流

## 前提

本地 git 已配置用户名和邮箱，且 `git remote` 指向目标仓库。

## 推送前检查

```bash
# 1. 查看远程仓库地址
git remote -v

# 2. 查看待提交文件
git status

# 3. 查看改动
git diff --stat
```

## 首次推送

```bash
git init                           # 初始化（已有 .git 则跳过）
git add -A                         # 暂存所有文件
git commit -m "Initial commit"     # 提交

# 设置远程仓库（如果还没设置）
git remote add origin git@github.com:pengbw/仓库名.git

git branch -M main                 # 改名为 main
git push -u origin main            # 推送并设置上游
```

## 常见报错

### ERROR: Repository not found

**原因**：远程仓库不存在，或 URL 错误。

**解法**：
1. 先在 GitHub 网页手动创建空仓库
2. 或提供 GitHub Token 用 API 自动创建：
   ```bash
   curl -X POST https://api.github.com/user/repos \
     -H "Authorization: token ghp_xxx" \
     -d '{"name":"仓库名","description":"..."}'
   ```

### Permission denied (publickey)

**原因**：没有 SSH 公钥，或 SSH 密钥路径不对。

**解法**：
```bash
# 检查 SSH 密钥
ls ~/.ssh/

# 测试 GitHub 连接
ssh -T git@github.com

# 如果用的是 HTTPS 而非 SSH，切换 URL
git remote set-url origin git@github.com:user/repo.git
```

### Updates were rejected because the remote contains work that you do not have

**原因**：远程有本地没有的提交。

**解法**（非强制推送，不要用 --force）：
```bash
git pull origin main --rebase
git push origin main
```
