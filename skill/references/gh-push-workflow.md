# GitHub Push Workflow

Assumes local git is configured with username/email and `git remote` points to the target repo.

## Standard Push

```bash
# 1. Check remote URL
git remote -v

# 2. Check staged files
git status

# 3. Review changes
git diff --stat

# 4. Stage all
git add -A

# 5. Commit
git commit -m "commit message"

# 6. Push
git push
```

## New Repo Setup

```bash
git remote add origin git@github.com:pengbw/repo-name.git
git branch -M main
git push -u origin main
```

## Common Errors

### ERROR: Repository not found

**Cause**: Remote repo does not exist or URL is wrong.

**Fix**:
1. Create an empty repo on GitHub web UI first, or
2. Create via API with a GitHub Token:
```bash
curl -X POST https://api.github.com/user/repos \
  -H "Authorization: token ghp_xxx" \
  -d '{"name":"repo-name","description":"..."}'
```

### Permission denied (publickey)

**Cause**: No SSH public key, or SSH key path is wrong.

**Fix**:
```bash
# Check SSH key
ls ~/.ssh/

# Test GitHub connection
ssh -T git@github.com

# If using HTTPS instead of SSH, switch to SSH
git remote set-url origin git@github.com:user/repo.git
```

### Updates were rejected because the remote contains work that you do not have

**Fix** (never use `--force`):
```bash
git pull origin main --rebase
git push origin main
```
