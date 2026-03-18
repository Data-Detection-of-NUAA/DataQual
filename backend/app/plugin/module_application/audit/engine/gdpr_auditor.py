"""
GDPR文件智能审计系统 - 集成示例
整合 Extraction + Detection 两阶段处理流程
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional

# 导入两个核心模块
from .content_extractor import ContentExtractor, ExtractedContent
from .content_detector import ContentDetector, GDPRDetectionReport


class GDPRFileAuditor:
    """GDPR文件审计器 - 统一入口"""

    @staticmethod
    def audit_file(file_path: str, file_type: Optional[str] = None) -> Dict[str, Any]:
        """
        审计单个文件的完整流程

        Args:
            file_path: 文件路径
            file_type: 文件类型（可选，自动检测）

        Returns:
            完整审计报告
        """
        print(f"\n{'='*60}")
        print(f"开始审计文件: {file_path}")
        print(f"{'='*60}\n")

        # ==================== 阶段1: 内容抽取 ====================
        print("【阶段1】内容抽取（Extraction）...")

        extracted_content = ContentExtractor.extract(file_path, file_type)

        print(f"✓ 文件类型: {extracted_content.file_type}")
        print(f"✓ 文件大小: {extracted_content.file_size / 1024:.2f} KB")
        print(f"✓ 抽取状态: {extracted_content.status}")

        if extracted_content.text:
            print(f"✓ 文本内容: {len(extracted_content.text)} 字符")
        if extracted_content.structured:
            print(f"✓ 结构化字段: {len(extracted_content.structured)} 个")
        if extracted_content.attachments:
            print(f"✓ 附件数量: {len(extracted_content.attachments)} 个")
        if extracted_content.images:
            print(f"✓ 图片数量: {len(extracted_content.images)} 个")

        if extracted_content.warnings:
            print(f"⚠ 警告: {len(extracted_content.warnings)} 条")
            for warning in extracted_content.warnings[:3]:
                print(f"  - {warning}")

        if extracted_content.errors:
            print(f"❌ 错误: {len(extracted_content.errors)} 条")
            for error in extracted_content.errors:
                print(f"  - {error}")

        # ==================== 阶段2: 内容检测 ====================
        print(f"\n{'='*60}")
        print("【阶段2】内容检测（Detection）...")

        detection_results = ContentDetector.detect(extracted_content.to_dict())

        print(f"✓ 检测到 {len(detection_results)} 项发现")

        # 按风险等级统计
        risk_stats = {}
        for result in detection_results:
            risk = result.risk_level.value
            risk_stats[risk] = risk_stats.get(risk, 0) + 1

        for risk, count in sorted(risk_stats.items()):
            print(f"  - {risk}: {count} 项")

        # ==================== 阶段3: 生成报告 ====================
        print(f"\n{'='*60}")
        print("【阶段3】生成GDPR审计报告...")

        report = GDPRDetectionReport.generate_report(
            detection_results,
            extracted_content.to_dict()
        )

        print(f"✓ 合规分数: {report['compliance_score']:.1f}/100")
        print(f"\n处置建议:")
        for rec in report['recommendations']:
            print(f"  {rec}")

        # 显示前5项严重/高风险发现
        print(f"\n{'='*60}")
        print("【关键发现】")

        critical = report['risk_breakdown']['critical_findings']
        if critical:
            print(f"\n❌ 严重风险 ({len(critical)} 项):")
            for item in critical[:5]:
                print(f"  - {item['detection_type']}: {item['location']}")
                print(f"    建议: {item['recommendation']}")

        high = report['risk_breakdown']['high_findings']
        if high:
            print(f"\n⚠️  高风险 ({len(high)} 项):")
            for item in high[:5]:
                print(f"  - {item['detection_type']}: {item['matched_value'][:50]}")
                print(f"    位置: {item['location']}")

        print(f"\n{'='*60}")
        print("审计完成！")
        print(f"{'='*60}\n")

        return report

    @staticmethod
    def save_report(report: Dict[str, Any], output_path: str):
        """保存报告为JSON文件"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"报告已保存至: {output_path}")


# ==================== 使用示例 ====================

def example_usage():
    """使用示例"""

    # 示例1: 审计CSV文件
    print("\n" + "="*80)
    print("示例1: 审计用户数据CSV")
    print("="*80)

    # 假设有一个用户数据CSV
    csv_report = GDPRFileAuditor.audit_file(
        file_path="/path/to/users.csv"
    )

    # 保存报告
    GDPRFileAuditor.save_report(csv_report, "users_audit_report.json")


    # 示例2: 审计压缩包
    print("\n" + "="*80)
    print("示例2: 审计ZIP压缩包（递归）")
    print("="*80)

    zip_report = GDPRFileAuditor.audit_file(
        file_path="/path/to/data_export.zip"
    )

    # 检查严重风险
    if zip_report['summary']['detection_by_risk']['严重'] > 0:
        print("\n⚠️ 警告：发现严重风险，请立即处理！")


    # 示例3: 审计PDF文档（可能包含扫描页）
    print("\n" + "="*80)
    print("示例3: 审计PDF合同文件")
    print("="*80)

    pdf_report = GDPRFileAuditor.audit_file(
        file_path="/path/to/contract.pdf"
    )

    # 检查是否需要OCR
    extraction_warnings = pdf_report.get('extraction_warnings', [])
    needs_ocr = any('OCR' in w for w in extraction_warnings)

    if needs_ocr:
        print("\n📷 提示：部分页面为扫描件，建议启用OCR以完整检测")


    # 示例4: 审计Word文档（包含元数据）
    print("\n" + "="*80)
    print("示例4: 审计Word文档")
    print("="*80)

    word_report = GDPRFileAuditor.audit_file(
        file_path="/path/to/document.docx"
    )

    # 检查元数据泄露
    if '元数据' in str(word_report['type_breakdown']):
        print("\n📝 提示：文档包含元数据（作者、公司等），建议清除")


def main():
    """主函数 - 实际使用"""
    import sys

    if len(sys.argv) < 2:
        print("用法: python gdpr_auditor.py <file_path> [output_report.json]")
        print("\n支持的文件类型:")
        print("  - 文档: txt, csv, xlsx, doc, docx, ppt, pptx, pdf")
        print("  - 数据: json, xml, yaml, ini")
        print("  - 压缩: zip, rar, 7z, tar, gz")
        print("  - 图片: png, jpg, jpeg (需OCR)")
        print("  - 网页: html, htm")
        return

    file_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else "gdpr_audit_report.json"

    # 执行审计
    report = GDPRFileAuditor.audit_file(file_path)

    # 保存报告
    GDPRFileAuditor.save_report(report, output_path)

    # 返回码（用于CI/CD）
    critical_count = report['summary']['detection_by_risk'].get('严重', 0)
    high_count = report['summary']['detection_by_risk'].get('高', 0)

    if critical_count > 0:
        print(f"\n❌ 审计失败：发现 {critical_count} 项严重风险")
        sys.exit(1)
    elif high_count > 5:
        print(f"\n⚠️  审计警告：发现 {high_count} 项高风险")
        sys.exit(2)
    else:
        print(f"\n✅ 审计通过：合规分数 {report['compliance_score']:.1f}/100")
        sys.exit(0)


if __name__ == "__main__":
    # main()
    example_usage()
