#!/usr/bin/env python3
"""修复train模块的导入路径"""

import re
from pathlib import Path

def fix_imports_in_file(file_path: Path):
    """修复单个文件中的导入路径"""
    if not file_path.exists():
        print(f"⚠️  文件不存在: {file_path}")
        return False

    content = file_path.read_text(encoding='utf-8')
    original_content = content

    # 替换导入路径模式
    patterns = [
        # 绝对导入：from app.plugin.module_train.train
        (
            r'from app\.plugin\.module_train\.train import',
            'from app.plugin.module_application.train import'
        ),
        (
            r'from app\.plugin\.module_train\.train\.',
            'from app.plugin.module_application.train.'
        ),
        # 相对导入：from ..module_train.train
        (
            r'from \.\.module_train\.train import',
            'from ..module_application.train import'
        ),
        (
            r'from \.\.module_train\.train\.',
            'from ..module_application.train.'
        ),
        # 直接导入：import app.plugin.module_train.train
        (
            r'import app\.plugin\.module_train\.train',
            'import app.plugin.module_application.train'
        ),
    ]

    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)

    # 只有内容变化时才写入
    if content != original_content:
        file_path.write_text(content, encoding='utf-8')
        print(f"✅ 已修复: {file_path.name}")
        return True
    else:
        print(f"⏭️  无需修复: {file_path.name}")
        return False

def main():
    """主函数"""
    train_dir = Path("backend/app/plugin/module_application/train/")

    if not train_dir.exists():
        print("❌ 目录不存在:", train_dir)
        return

    # 处理所有Python文件
    py_files = [f for f in train_dir.glob("*.py") if f.name != '__pycache__']
    fixed_count = 0

    print("=" * 50)
    print("开始修复train模块的导入路径")
    print("=" * 50)
    print()

    for py_file in sorted(py_files):
        if fix_imports_in_file(py_file):
            fixed_count += 1

    print()
    print("=" * 50)
    print(f"总计: 检查 {len(py_files)} 个文件，修复 {fixed_count} 个文件")
    print("=" * 50)

if __name__ == "__main__":
    main()
