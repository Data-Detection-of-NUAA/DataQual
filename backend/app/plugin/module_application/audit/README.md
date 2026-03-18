# GDPR文件智能审计系统 - 快速开始

## 🚀 5分钟快速上手

### 安装依赖

```bash
# 核心依赖（必须）
pip install pandas openpyxl python-docx python-pptx pdfplumber

# 压缩包支持
pip install rarfile py7zr

# 图片/HTML支持
pip install Pillow beautifulsoup4

# 可选：OCR支持
pip install pytesseract  # 需先安装Tesseract-OCR
```

### 基础使用

```python
from audit.engine.gdpr_auditor import GDPRFileAuditor

# 一键审计文件
report = GDPRFileAuditor.audit_file("users.csv")

# 保存报告
GDPRFileAuditor.save_report(report, "audit_report.json")

# 检查合规分数
print(f"合规分数: {report['compliance_score']}/100")
```

### 命令行使用

```bash
# 审计单个文件
python -m audit.engine.gdpr_auditor data/users.csv report.json

# 返回码说明：
# 0 = 通过（合规分数≥70）
# 1 = 失败（发现严重风险）
# 2 = 警告（高风险>5项）
```

---

## 📊 审计结果示例

### 示例输出

```
============================================================
开始审计文件: users.csv
============================================================

【阶段1】内容抽取（Extraction）...
✓ 文件类型: csv
✓ 文件大小: 5120.00 KB
✓ 抽取状态: success
✓ 文本内容: 256000 字符
✓ 结构化字段: 600 个

============================================================
【阶段2】内容检测（Detection）...
✓ 检测到 15 项发现
  - 严重: 0 项
  - 高: 3 项
  - 中: 10 项
  - 低: 2 项

============================================================
【阶段3】生成GDPR审计报告...
✓ 合规分数: 75.0/100

处置建议:
  ⚠️发现3项高风险（身份证号），需加密或脱敏
  ⚡发现10项中风险（手机号/邮箱），建议脱敏处理

============================================================
【关键发现】

⚠️  高风险 (3 项):
  - 身份证号: 11010119900101001X
    位置: field:row.0.idcard
  - 身份证号: 11010119900101002X
    位置: field:row.1.idcard
  - 身份证号: 11010119900101003X
    位置: field:row.2.idcard

============================================================
审计完成！
============================================================
```

---

## 📋 支持的文件类型

### 全部30+种格式

| 类别 | 格式 | 说明 |
|------|------|------|
| **文档** | txt, md, log | 纯文本 |
| **数据** | csv, tsv, json, yaml, xml, ini, toml | 结构化数据 |
| **Office** | doc, docx, xls, xlsx, ppt, pptx | 含元数据、表格、批注 |
| **PDF** | pdf | 文本型+扫描型（标记需OCR） |
| **图片** | png, jpg, jpeg, bmp, tiff, gif | EXIF+OCR |
| **压缩** | zip, rar, 7z, tar, gz | 递归解压 |
| **网页** | html, htm | 表单字段提取 |
| **其他** | rtf | 富文本 |

---

## 🔍 检测的敏感数据类型

### 4大类40+种检测

#### ① 个人数据PII
- ✅ 姓名、手机号、邮箱、身份证号、地址
- ✅ IP地址、MAC地址、Cookie ID、设备ID
- ✅ 用户ID、订单号

#### ② 特殊类别（GDPR Art.9）
- ✅ 健康数据、生物识别、基因数据
- ✅ 宗教信仰、政治观点、性取向

#### ③ 儿童数据
- ✅ 年龄、出生日期、未成年人标识

#### ④ 安全敏感⚠️重点
- ❌ 密码、API Key、AWS密钥、GitHub Token
- ❌ JWT令牌、私钥、数据库连接串、Access Token

⑤ 金融数据
- ✅ 银行卡号、信用卡号、CVV码

⑥ 其他
- ✅ 车牌号、护照号、驾驶证号

---

## 🎯 使用场景

### 场景1: 数据导出前检查

```python
# 审计CSV导出文件
report = GDPRFileAuditor.audit_file("user_export.csv")

# 如果发现严重风险，阻止导出
if report['summary']['detection_by_risk'].get('严重', 0) > 0:
    raise Exception("发现严重风险，禁止导出")
```

### 场景2: 压缩包批量审计

```python
# 递归审计ZIP压缩包
report = GDPRFileAuditor.audit_file("data_export.zip")

# 查看哪些文件包含敏感数据
for finding in report['risk_breakdown']['high_findings']:
    print(f"{finding['location']}: {finding['detection_type']}")
```

### 场景3: CI/CD集成

```bash
#!/bin/bash
# 在CI流水线中运行

python -m audit.engine.gdpr_auditor data/*.csv audit_report.json

if [ $? -eq 1 ]; then
    echo "❌ GDPR审计失败：发现严重风险"
    exit 1
fi

echo "✅ GDPR审计通过"
```

---

## 📖 详细文档

- [完整技术文档](GDPR_AUDIT_SYSTEM.md) - 系统架构、算法详解
- [项目进度汇报](PROJECT_PROGRESS_REPORT.md) - 案例、效果评估

---

## ⚙️ 配置说明

### 调整安全限制

```python
from audit.engine.content_extractor import ContentExtractor

# 修改配置（可选）
ContentExtractor.MAX_TEXT_LENGTH = 20_000_000  # 文本大小限制
ContentExtractor.MAX_ARCHIVE_SIZE = 1_000_000_000  # 压缩包大小限制
ContentExtractor.MAX_ARCHIVE_FILES = 20000  # 压缩包文件数限制
ContentExtractor.MAX_RECURSION_DEPTH = 3  # 递归深度限制
```

---

## 🐛 常见问题

### Q1: 报错"请安装 pdfplumber"
```bash
pip install pdfplumber
```

### Q2: 压缩包解压失败
```bash
# RAR格式需要额外安装
pip install rarfile

# 7z格式需要
pip install py7zr
```

### Q3: OCR识别失败
```bash
# 安装Tesseract OCR引擎
# Windows: https://github.com/UB-Mannheim/tesseract/wiki
# Linux: sudo apt-get install tesseract-ocr
# Mac: brew install tesseract

pip install pytesseract
```

### Q4: 旧版Office文件（.doc/.ppt）无法解析
```bash
pip install textract  # 支持旧版Office

# Linux额外需要：
sudo apt-get install antiword
```

---

## 📊 性能参考

| 文件大小 | 文件类型 | 预计耗时 |
|---------|---------|---------|
| 10MB | CSV | 3-5秒 |
| 10MB | XLSX | 5-8秒 |
| 10MB | PDF（文本型） | 10-15秒 |
| 10MB | PDF（扫描型） | 3-5分钟（需OCR） |
| 100MB | ZIP（100个文件） | 30-60秒 |

**瓶颈**: PDF扫描件OCR识别较慢（20秒/页）

---

## 🔒 安全性说明

### 密码/密钥脱敏
系统检测到密码、API Key等严重风险时，**不会记录明文**：

```python
{
  "detection_type": "密码",
  "matched_value": "***REDACTED***",  # 已脱敏
  "recommendation": "❌严重：密码字段不应出现，立即删除！"
}
```

### 防Zip Bomb
三重防护机制：
- ✅ 压缩包大小限制（默认500MB）
- ✅ 文件数量限制（默认10000个）
- ✅ 递归深度限制（默认5层）

---

## 📞 技术支持

- **完整文档**: `GDPR_AUDIT_SYSTEM.md`
- **进度汇报**: `PROJECT_PROGRESS_REPORT.md`

---

## 📝 License

内部使用
