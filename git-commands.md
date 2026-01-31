# Git 常用命令备忘录

## 每天开始工作前（同步 develop）
```bash
cd d:/PycharmProjects/FastapiAdmin
git checkout feature/audit-system
git fetch origin develop
git merge origin/develop
```

## 查看状态
```bash
git status                    # 查看修改状态
git log --oneline -5          # 查看最近5次提交
git branch -a                 # 查看所有分支
git diff                      # 查看未暂存的修改
```

## 提交代码
```bash
# 1. 查看修改
git status

# 2. 添加文件
git add .                     # 添加所有修改
git add 文件名                # 添加指定文件

# 3. 提交
git commit -m "feat: 实现xxx功能"

# 4. 推送
git push origin feature/audit-system
```

## 提交信息规范
```bash
feat: 添加新功能
fix: 修复bug
docs: 文档更新
style: 代码格式调整
refactor: 代码重构
perf: 性能优化
test: 测试相关
```

## 撤销操作
```bash
# 撤销工作区修改（未add）
git checkout -- 文件名

# 撤销暂存区修改（已add未commit）
git reset HEAD 文件名

# 查看某次提交的内容
git show commit-id
```

## 解决冲突
```bash
# 1. 合并时遇到冲突
git merge origin/develop

# 2. 手动编辑冲突文件，删除冲突标记
#    <<<<<<< HEAD
#    你的修改
#    =======
#    别人的修改
#    >>>>>>> origin/develop

# 3. 标记为已解决
git add 冲突文件

# 4. 完成合并
git commit -m "merge: 解决与develop的冲突"

# 5. 推送
git push origin feature/audit-system
```

## 查看远程信息
```bash
git remote -v                 # 查看远程仓库地址
git branch -r                 # 查看远程分支
git fetch origin              # 获取远程更新（不合并）
git pull origin develop       # 拉取并合并develop
```

## 暂存工作进度（临时切换分支用）
```bash
# 暂存当前修改
git stash

# 切换到其他分支工作
git checkout other-branch

# 切回来恢复暂存
git checkout feature/audit-system
git stash pop
```

## 项目路径
```
正确的仓库: d:/PycharmProjects/FastapiAdmin/
你的分支: feature/audit-system
```

## GitHub 链接
```
仓库地址: https://github.com/Data-Detection-of-NUAA/DataQual
创建PR: https://github.com/Data-Detection-of-NUAA/DataQual/pull/new/feature/audit-system
```
