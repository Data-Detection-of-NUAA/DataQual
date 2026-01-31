"""
审计报告生成器
生成Excel格式的审计报告
"""
import os
from datetime import datetime
from typing import Dict, Any, List
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from app.config.path_conf import UPLOAD_DIR


class ReportGenerator:
    """报告生成器类"""

    @staticmethod
    async def generate_report(task_id: int, audit_result: Dict[str, Any], rules: List) -> str:
        """
        生成Excel格式的审计报告

        Args:
            task_id: 任务ID
            audit_result: 审计结果
            rules: 使用的规则列表

        Returns:
            报告文件路径
        """
        # 创建工作簿
        wb = openpyxl.Workbook()

        # 创建概览表
        ws_summary = wb.active
        ws_summary.title = "审计概览"
        ReportGenerator._create_summary_sheet(ws_summary, task_id, audit_result, rules)

        # 创建数据错误表
        ws_data_errors = wb.create_sheet("数据错误")
        data_errors = [e for e in audit_result['errors'] if e['error_type'] == 'data']
        ReportGenerator._create_error_sheet(ws_data_errors, data_errors)

        # 创建标签错误表
        ws_label_errors = wb.create_sheet("标签错误")
        label_errors = [e for e in audit_result['errors'] if e['error_type'] == 'label']
        ReportGenerator._create_error_sheet(ws_label_errors, label_errors)

        # 创建规则证据表
        ws_rule_evidence = wb.create_sheet("规则证据")
        ReportGenerator._create_rule_evidence_sheet(ws_rule_evidence, audit_result.get('rule_statistics', []))

        # 保存文件
        today = datetime.now()
        dir_path = os.path.join(
            UPLOAD_DIR,
            "audit",
            "reports",
            str(today.year),
            f"{today.month:02d}"
        )
        os.makedirs(dir_path, exist_ok=True)

        file_name = f"audit_report_{task_id}_{today.strftime('%Y%m%d_%H%M%S')}.xlsx"
        file_path = os.path.join(dir_path, file_name)

        wb.save(file_path)
        return file_path

    @staticmethod
    def _create_summary_sheet(ws, task_id: int, audit_result: Dict[str, Any], rules: List):
        """创建概览表"""
        # 标题样式
        title_font = Font(name='微软雅黑', size=16, bold=True)
        header_font = Font(name='微软雅黑', size=12, bold=True, color='FFFFFF')
        header_fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
        header_alignment = Alignment(horizontal='center', vertical='center')

        # 添加标题
        ws['A1'] = '数据集合规审计报告'
        ws['A1'].font = title_font
        ws.merge_cells('A1:D1')
        ws['A1'].alignment = Alignment(horizontal='center', vertical='center')

        # 添加任务信息
        row = 3
        info_items = [
            ('任务ID:', task_id),
            ('审计时间:', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            ('总记录数:', audit_result['total_records']),
            ('错误记录数:', audit_result['error_records']),
        ]

        for label, value in info_items:
            ws[f'A{row}'] = label
            ws[f'A{row}'].font = Font(name='微软雅黑', bold=True)
            ws[f'B{row}'] = value
            row += 1

        # 计算错误率
        error_rate = (audit_result['error_records'] / audit_result['total_records'] * 100) if audit_result['total_records'] > 0 else 0
        ws[f'A{row}'] = '错误率:'
        ws[f'A{row}'].font = Font(name='微软雅黑', bold=True)
        ws[f'B{row}'] = f"{error_rate:.2f}%"

        # 添加使用的规则
        row += 2
        ws[f'A{row}'] = '使用的审计规则'
        ws[f'A{row}'].font = header_font
        ws[f'A{row}'].fill = header_fill
        ws[f'A{row}'].alignment = header_alignment
        ws.merge_cells(f'A{row}:D{row}')

        row += 1
        headers = ['规则编码', '规则名称', '规则类型', '严重级别']
        for col, header in enumerate(headers, start=1):
            cell = ws.cell(row=row, column=col)
            cell.value = header
            cell.font = Font(name='微软雅黑', bold=True)
            cell.fill = PatternFill(start_color='D9E1F2', end_color='D9E1F2', fill_type='solid')
            cell.alignment = Alignment(horizontal='center', vertical='center')

        for rule in rules:
            row += 1
            ws[f'A{row}'] = rule.rule_code
            ws[f'B{row}'] = rule.rule_name
            ws[f'C{row}'] = rule.rule_type
            ws[f'D{row}'] = rule.severity

        # 设置列宽
        ws.column_dimensions['A'].width = 20
        ws.column_dimensions['B'].width = 30
        ws.column_dimensions['C'].width = 15
        ws.column_dimensions['D'].width = 15

    @staticmethod
    def _create_error_sheet(ws, errors: List[Dict[str, Any]]):
        """创建错误详情表"""
        # 样式定义
        header_font = Font(name='微软雅黑', bold=True, color='FFFFFF')
        header_fill = PatternFill(start_color='4472C4', end_color='4472C4', fill_type='solid')
        header_alignment = Alignment(horizontal='center', vertical='center')

        # 添加表头
        headers = ['行号', '字段名', '错误值', '错误描述', '严重级别']
        for col, header in enumerate(headers, start=1):
            cell = ws.cell(row=1, column=col)
            cell.value = header
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = header_alignment

        # 添加错误数据
        for row, error in enumerate(errors, start=2):
            ws[f'A{row}'] = error.get('row_number', '')
            ws[f'B{row}'] = error.get('column_name') or error.get('field_name', '')
            ws[f'C{row}'] = str(error.get('original_value', ''))
            ws[f'D{row}'] = error.get('error_message', '')
            ws[f'E{row}'] = error.get('severity', '')

            # 根据严重级别设置颜色
            severity = error.get('severity', 'info')
            if severity == 'error':
                fill_color = 'FFC7CE'  # 红色
            elif severity == 'warning':
                fill_color = 'FFEB9C'  # 黄色
            else:
                fill_color = 'C6EFCE'  # 绿色

            for col in range(1, 6):
                cell = ws.cell(row=row, column=col)
                cell.fill = PatternFill(start_color=fill_color, end_color=fill_color, fill_type='solid')
                cell.alignment = Alignment(horizontal='left', vertical='center', wrap_text=True)

        # 如果没有错误数据，添加提示
        if not errors:
            ws['A2'] = '暂无错误数据'
            ws.merge_cells('A2:E2')
            ws['A2'].alignment = Alignment(horizontal='center', vertical='center')
            ws['A2'].font = Font(name='微软雅黑', size=11, italic=True)

        # 设置列宽
        ws.column_dimensions['A'].width = 10
        ws.column_dimensions['B'].width = 20
        ws.column_dimensions['C'].width = 30
        ws.column_dimensions['D'].width = 50
        ws.column_dimensions['E'].width = 15

        # 设置行高
        for row in range(2, len(errors) + 2):
            ws.row_dimensions[row].height = 30

    @staticmethod
    def _create_rule_evidence_sheet(ws, rule_statistics: List[Dict[str, Any]]):
        """???????"""
        title_font = Font(name='??????', size=14, bold=True)
        header_font = Font(name='??????', bold=True)
        row = 1

        if not rule_statistics:
            ws['A1'] = '????????'
            ws['A1'].font = title_font
            return

        for stat in rule_statistics:
            ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=6)
            ws[f'A{row}'] = f"{stat.get('rule_code')} - {stat.get('rule_name')}"
            ws[f'A{row}'].font = title_font
            row += 2

            metrics = stat.get('metrics') or {}
            for label, value in metrics.items():
                ws[f'A{row}'] = label
                ws[f'B{row}'] = value
                ws[f'A{row}'].font = header_font
                row += 1

            tables = stat.get('tables') or []
            for table in tables:
                headers = table.get('headers') or []
                rows = table.get('rows') or []
                row = ReportGenerator._write_table(ws, row + 1, table.get('title', ''), headers, rows)

            samples = stat.get('samples') or []
            if samples:
                sample_headers = ['??', '??', '?', '??', '??ID', '??ID', '??ID']
                sample_rows = []
                for sample in samples[:20]:
                    sample_rows.append([
                        sample.get('row_number'),
                        sample.get('field'),
                        sample.get('value'),
                        sample.get('message'),
                        sample.get('record_id'),
                        sample.get('subject_id'),
                        sample.get('dsar_request_id')
                    ])
                row = ReportGenerator._write_table(ws, row + 1, '????', sample_headers, sample_rows)

            row += 2

    @staticmethod
    def _write_table(ws, start_row: int, title: str, headers: List[str], rows: List[List[Any]]) -> int:
        """??????"""
        if title:
            ws[f'A{start_row}'] = title
            ws[f'A{start_row}'].font = Font(name='??????', bold=True)
            start_row += 1

        header_font = Font(name='??????', bold=True, color='FFFFFF')
        header_fill = PatternFill(start_color='5B9BD5', end_color='5B9BD5', fill_type='solid')
        for col, header in enumerate(headers, start=1):
            cell = ws.cell(row=start_row, column=col)
            cell.value = header
            cell.font = header_font
            cell.fill = header_fill
            cell.alignment = Alignment(horizontal='center', vertical='center')

        for data_row in rows:
            start_row += 1
            for col, value in enumerate(data_row, start=1):
                cell = ws.cell(row=start_row, column=col)
                cell.value = value
                cell.alignment = Alignment(horizontal='left', vertical='center')

        return start_row + 2

