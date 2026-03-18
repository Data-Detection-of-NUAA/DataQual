"""
内容抽取器（Extraction Layer）
职责：将各种文件格式统一抽取为标准化结构
输出：text / structured / attachments / images
"""
import os
import json
import tempfile
import shutil
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class ExtractedContent:
    """标准化的抽取结果"""
    # 基本信息
    file_path: str
    file_type: str
    file_size: int
    extraction_timestamp: str

    # 抽取内容（四大类）
    text: Optional[str] = None                    # 纯文本内容
    structured: Optional[Dict[str, Any]] = None   # 结构化数据（字段路径 → 值）
    attachments: Optional[List[Dict]] = None      # 嵌套文件列表
    images: Optional[List[Dict]] = None           # 图片/扫描页列表

    # 元数据
    metadata: Optional[Dict[str, Any]] = None     # 文档元信息

    # 状态
    status: str = "success"                       # success / partial / failed
    errors: Optional[List[str]] = None            # 错误信息列表
    warnings: Optional[List[str]] = None          # 警告信息列表

    def to_dict(self) -> Dict:
        """转换为字典"""
        return asdict(self)


class ContentExtractor:
    """统一内容抽取器"""

    # 配置项
    MAX_TEXT_LENGTH = 10_000_000  # 10MB文本
    MAX_ARCHIVE_SIZE = 500_000_000  # 500MB压缩包
    MAX_ARCHIVE_FILES = 10000  # 压缩包最大文件数
    MAX_RECURSION_DEPTH = 5  # 递归解压最大深度

    @staticmethod
    def extract(file_path: str, file_type: str = None, recursion_depth: int = 0) -> ExtractedContent:
        """
        统一抽取入口

        Args:
            file_path: 文件路径
            file_type: 文件类型（可选，自动检测）
            recursion_depth: 当前递归深度

        Returns:
            ExtractedContent: 标准化抽取结果
        """
        # 初始化结果
        file_size = os.path.getsize(file_path)
        if not file_type:
            file_type = Path(file_path).suffix.lower().replace('.', '')

        result = ExtractedContent(
            file_path=file_path,
            file_type=file_type,
            file_size=file_size,
            extraction_timestamp=datetime.now().isoformat(),
            errors=[],
            warnings=[]
        )

        try:
            # 检查递归深度
            if recursion_depth > ContentExtractor.MAX_RECURSION_DEPTH:
                result.status = "failed"
                result.errors.append(f"递归深度超过限制 {ContentExtractor.MAX_RECURSION_DEPTH}")
                return result

            # 根据文件类型分发
            if file_type in ['zip', 'rar', '7z', 'tar', 'gz', 'tgz']:
                return ContentExtractor._extract_archive(file_path, file_type, recursion_depth, result)

            elif file_type in ['txt', 'log', 'md', 'csv', 'tsv']:
                return ContentExtractor._extract_text(file_path, file_type, result)

            elif file_type in ['json', 'yaml', 'yml', 'toml', 'ini', 'conf', 'cfg']:
                return ContentExtractor._extract_structured_text(file_path, file_type, result)

            elif file_type == 'xml':
                return ContentExtractor._extract_xml(file_path, result)

            elif file_type in ['xlsx', 'xls', 'xlsm']:
                return ContentExtractor._extract_excel(file_path, result)

            elif file_type in ['docx', 'doc']:
                return ContentExtractor._extract_word(file_path, file_type, result)

            elif file_type in ['pptx', 'ppt']:
                return ContentExtractor._extract_powerpoint(file_path, file_type, result)

            elif file_type == 'pdf':
                return ContentExtractor._extract_pdf(file_path, result)

            elif file_type in ['png', 'jpg', 'jpeg', 'bmp', 'tiff', 'gif']:
                return ContentExtractor._extract_image(file_path, result)

            elif file_type in ['html', 'htm']:
                return ContentExtractor._extract_html(file_path, result)

            else:
                # 未知类型，尝试作为文本读取
                result.warnings.append(f"未知文件类型 {file_type}，尝试按文本处理")
                return ContentExtractor._extract_text(file_path, file_type, result)

        except Exception as e:
            result.status = "failed"
            result.errors.append(f"抽取失败: {str(e)}")
            return result

    # ==================== A. 纯文本/结构化文本 ====================

    @staticmethod
    def _extract_text(file_path: str, file_type: str, result: ExtractedContent) -> ExtractedContent:
        """抽取纯文本文件"""
        encodings = ['utf-8', 'gbk', 'gb2312', 'latin1', 'cp1252']

        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    text = f.read(ContentExtractor.MAX_TEXT_LENGTH)
                    result.text = text

                    # CSV需要额外处理为结构化
                    if file_type in ['csv', 'tsv']:
                        result.structured = ContentExtractor._csv_to_structured(text, file_type)

                    result.status = "success"
                    return result
            except UnicodeDecodeError:
                continue

        # 所有编码失败，使用二进制模式
        with open(file_path, 'rb') as f:
            raw = f.read(ContentExtractor.MAX_TEXT_LENGTH)
            result.text = raw.decode('utf-8', errors='ignore')
            result.warnings.append("使用容错模式读取，可能存在乱码")

        return result

    @staticmethod
    def _csv_to_structured(text: str, file_type: str) -> Dict[str, Any]:
        """CSV转结构化数据（扁平字典格式）"""
        import csv
        import io

        delimiter = '\t' if file_type == 'tsv' else ','
        reader = csv.DictReader(io.StringIO(text), delimiter=delimiter)

        # 返回扁平字典：path -> value
        structured = {}
        for i, row in enumerate(reader):
            if i >= 10000:  # 限制行数
                break
            # 扁平化结构：row.0.field_name = value
            for key, value in row.items():
                if key:  # 跳过空列名
                    structured[f"row.{i}.{key}"] = value

        return structured

    @staticmethod
    def _extract_structured_text(file_path: str, file_type: str, result: ExtractedContent) -> ExtractedContent:
        """抽取结构化文本（JSON/YAML等）"""
        # 先读取原文
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read(ContentExtractor.MAX_TEXT_LENGTH)
            result.text = text

        # 解析为结构化
        try:
            if file_type == 'json':
                data = json.loads(text)
                result.structured = ContentExtractor._flatten_dict(data, prefix="")

            elif file_type in ['yaml', 'yml']:
                import yaml
                data = yaml.safe_load(text)
                result.structured = ContentExtractor._flatten_dict(data, prefix="")

            elif file_type == 'toml':
                import toml
                data = toml.loads(text)
                result.structured = ContentExtractor._flatten_dict(data, prefix="")

            elif file_type in ['ini', 'conf', 'cfg']:
                import configparser
                config = configparser.ConfigParser()
                config.read_string(text)
                data = {section: dict(config[section]) for section in config.sections()}
                result.structured = ContentExtractor._flatten_dict(data, prefix="")

        except Exception as e:
            result.warnings.append(f"结构化解析失败: {str(e)}，仅保留文本")

        return result

    @staticmethod
    def _flatten_dict(data: Any, prefix: str = "", max_depth: int = 10) -> Dict[str, Any]:
        """
        递归扁平化字典，保留路径
        user.address.city = "Beijing"
        """
        if max_depth <= 0:
            return {prefix: str(data)}

        result = {}

        if isinstance(data, dict):
            for key, value in data.items():
                new_prefix = f"{prefix}.{key}" if prefix else key
                if isinstance(value, (dict, list)):
                    result.update(ContentExtractor._flatten_dict(value, new_prefix, max_depth - 1))
                else:
                    result[new_prefix] = value

        elif isinstance(data, list):
            for i, item in enumerate(data):
                new_prefix = f"{prefix}[{i}]"
                if isinstance(item, (dict, list)):
                    result.update(ContentExtractor._flatten_dict(item, new_prefix, max_depth - 1))
                else:
                    result[new_prefix] = item
        else:
            result[prefix] = data

        return result

    @staticmethod
    def _extract_xml(file_path: str, result: ExtractedContent) -> ExtractedContent:
        """抽取XML（保留结构路径）"""
        import xml.etree.ElementTree as ET

        tree = ET.parse(file_path)
        root = tree.getroot()

        # 提取文本
        result.text = ET.tostring(root, encoding='unicode')

        # 提取结构化路径
        def xml_to_paths(element, path=""):
            paths = {}
            current_path = f"{path}/{element.tag}" if path else element.tag

            # 属性
            for attr, value in element.attrib.items():
                paths[f"{current_path}@{attr}"] = value

            # 文本内容
            if element.text and element.text.strip():
                paths[f"{current_path}#text"] = element.text.strip()

            # 子元素
            for child in element:
                paths.update(xml_to_paths(child, current_path))

            return paths

        result.structured = xml_to_paths(root)
        return result

    # ==================== B. Office 文档 ====================

    @staticmethod
    def _extract_excel(file_path: str, result: ExtractedContent) -> ExtractedContent:
        """抽取Excel（表格+元数据）"""
        import pandas as pd
        import openpyxl

        # 1. 提取所有工作表的数据
        excel_file = pd.ExcelFile(file_path)
        all_text = []
        structured_data = {}

        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(file_path, sheet_name=sheet_name)

            # 文本形式
            sheet_text = f"=== Sheet: {sheet_name} ===\n"
            sheet_text += df.to_string(index=False)
            all_text.append(sheet_text)

            # 结构化形式（路径：sheet.row.column）
            for row_idx, row in df.iterrows():
                for col_name, value in row.items():
                    if pd.notna(value):
                        path = f"{sheet_name}.row{row_idx}.{col_name}"
                        structured_data[path] = value

        result.text = "\n\n".join(all_text)
        result.structured = structured_data

        # 2. 提取元数据
        try:
            wb = openpyxl.load_workbook(file_path, read_only=True)
            result.metadata = {
                "creator": wb.properties.creator,
                "last_modified_by": wb.properties.lastModifiedBy,
                "created": str(wb.properties.created),
                "modified": str(wb.properties.modified),
                "title": wb.properties.title,
                "subject": wb.properties.subject,
                "keywords": wb.properties.keywords,
                "company": wb.properties.company
            }
        except Exception as e:
            result.warnings.append(f"元数据提取失败: {str(e)}")

        return result

    @staticmethod
    def _extract_word(file_path: str, file_type: str, result: ExtractedContent) -> ExtractedContent:
        """抽取Word文档（正文+表格+批注+修订+元数据）"""
        if file_type == 'docx':
            from docx import Document
            doc = Document(file_path)

            # 1. 正文段落
            paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]

            # 2. 表格
            tables_text = []
            structured_tables = {}
            for table_idx, table in enumerate(doc.tables):
                table_text = f"=== Table {table_idx} ===\n"
                for row_idx, row in enumerate(table.rows):
                    row_cells = [cell.text for cell in row.cells]
                    table_text += "\t".join(row_cells) + "\n"

                    # 结构化
                    for col_idx, cell in enumerate(row.cells):
                        path = f"table{table_idx}.row{row_idx}.col{col_idx}"
                        structured_tables[path] = cell.text

                tables_text.append(table_text)

            # 3. 页眉页脚
            headers_footers = []
            for section in doc.sections:
                if section.header.paragraphs:
                    header_text = "\n".join([p.text for p in section.header.paragraphs if p.text.strip()])
                    if header_text:
                        headers_footers.append(f"Header: {header_text}")
                if section.footer.paragraphs:
                    footer_text = "\n".join([p.text for p in section.footer.paragraphs if p.text.strip()])
                    if footer_text:
                        headers_footers.append(f"Footer: {footer_text}")

            # 组合文本
            all_text = "\n\n".join(paragraphs)
            if tables_text:
                all_text += "\n\n" + "\n\n".join(tables_text)
            if headers_footers:
                all_text += "\n\n=== Headers/Footers ===\n" + "\n".join(headers_footers)

            result.text = all_text
            result.structured = structured_tables

            # 4. 元数据
            core_props = doc.core_properties
            result.metadata = {
                "author": core_props.author,
                "created": str(core_props.created),
                "modified": str(core_props.modified),
                "last_modified_by": core_props.last_modified_by,
                "title": core_props.title,
                "subject": core_props.subject,
                "keywords": core_props.keywords,
                "comments": core_props.comments
            }

        elif file_type == 'doc':
            # 旧版Word，使用textract
            try:
                import textract
                text = textract.process(file_path).decode('utf-8', errors='ignore')
                result.text = text
                result.warnings.append("旧版Word格式，无法提取元数据和结构化信息")
            except ImportError:
                raise ImportError("请安装 textract: pip install textract")

        return result

    @staticmethod
    def _extract_powerpoint(file_path: str, file_type: str, result: ExtractedContent) -> ExtractedContent:
        """抽取PPT（幻灯片文本+备注+元数据）"""
        if file_type == 'pptx':
            from pptx import Presentation
            prs = Presentation(file_path)

            slides_text = []
            structured_data = {}

            for slide_idx, slide in enumerate(prs.slides):
                slide_text = f"=== Slide {slide_idx + 1} ===\n"

                # 幻灯片内容
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text:
                        slide_text += shape.text + "\n"
                        path = f"slide{slide_idx}.shape{shape.shape_id}"
                        structured_data[path] = shape.text

                # 备注
                if slide.has_notes_slide:
                    notes_text = slide.notes_slide.notes_text_frame.text
                    if notes_text:
                        slide_text += f"\n[Notes]: {notes_text}\n"
                        structured_data[f"slide{slide_idx}.notes"] = notes_text

                slides_text.append(slide_text)

            result.text = "\n\n".join(slides_text)
            result.structured = structured_data

            # 元数据
            core_props = prs.core_properties
            result.metadata = {
                "author": core_props.author,
                "created": str(core_props.created),
                "modified": str(core_props.modified),
                "last_modified_by": core_props.last_modified_by,
                "title": core_props.title,
                "subject": core_props.subject
            }

        else:
            # 旧版PPT
            try:
                import textract
                text = textract.process(file_path).decode('utf-8', errors='ignore')
                result.text = text
                result.warnings.append("旧版PPT格式，无法提取元数据")
            except ImportError:
                raise ImportError("请安装 textract")

        return result

    # ==================== C. PDF（重点） ====================

    @staticmethod
    def _extract_pdf(file_path: str, result: ExtractedContent) -> ExtractedContent:
        """抽取PDF（文本型+扫描型+表格+附件+元数据）"""
        import pdfplumber
        from PIL import Image
        import io

        text_pages = []
        images_list = []
        tables_data = {}

        with pdfplumber.open(file_path) as pdf:
            # 元数据
            result.metadata = {
                "pages": len(pdf.pages),
                "metadata": pdf.metadata
            }

            for page_num, page in enumerate(pdf.pages, 1):
                page_text = f"=== Page {page_num} ===\n"

                # 1. 提取文本
                extracted_text = page.extract_text()
                if extracted_text and extracted_text.strip():
                    page_text += extracted_text
                    text_pages.append(page_text)
                else:
                    # 可能是扫描页，需要OCR
                    result.warnings.append(f"第{page_num}页无文本，可能需要OCR")

                    # 将页面转为图片
                    try:
                        page_image = page.to_image(resolution=150)
                        img_bytes = io.BytesIO()
                        page_image.save(img_bytes, format='PNG')

                        images_list.append({
                            "source": f"page_{page_num}",
                            "type": "scanned_page",
                            "size": len(img_bytes.getvalue()),
                            "requires_ocr": True
                        })
                    except Exception as e:
                        result.warnings.append(f"第{page_num}页图片提取失败: {str(e)}")

                # 2. 提取表格
                tables = page.extract_tables()
                for table_idx, table in enumerate(tables):
                    if table:
                        table_key = f"page{page_num}.table{table_idx}"
                        for row_idx, row in enumerate(table):
                            for col_idx, cell in enumerate(row):
                                if cell:
                                    path = f"{table_key}.row{row_idx}.col{col_idx}"
                                    tables_data[path] = cell

        result.text = "\n\n".join(text_pages)
        if tables_data:
            result.structured = tables_data
        if images_list:
            result.images = images_list

        # 3. 检查PDF附件
        try:
            import PyPDF2
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                if '/Names' in pdf_reader.trailer['/Root']:
                    result.warnings.append("PDF包含嵌入附件，需要专门提取")
        except Exception:
            pass

        return result

    # ==================== D. 图片（OCR） ====================

    @staticmethod
    def _extract_image(file_path: str, result: ExtractedContent) -> ExtractedContent:
        """抽取图片（OCR文字+EXIF元数据）"""
        from PIL import Image
        from PIL.ExifTags import TAGS

        # 1. EXIF元数据
        try:
            image = Image.open(file_path)
            exif_data = {}

            if hasattr(image, '_getexif') and image._getexif():
                exif = image._getexif()
                for tag_id, value in exif.items():
                    tag = TAGS.get(tag_id, tag_id)
                    exif_data[tag] = str(value)

            result.metadata = {
                "format": image.format,
                "mode": image.mode,
                "size": image.size,
                "exif": exif_data
            }

            # GPS信息单独标记（高风险）
            if 'GPSInfo' in exif_data:
                result.warnings.append("图片包含GPS定位信息")

        except Exception as e:
            result.warnings.append(f"EXIF提取失败: {str(e)}")

        # 2. OCR文字识别
        result.images = [{
            "path": file_path,
            "type": "standalone_image",
            "requires_ocr": True,
            "note": "需要OCR识别（身份证、银行卡、车牌等）"
        }]

        # 如果安装了OCR引擎，直接识别
        try:
            import pytesseract
            text = pytesseract.image_to_string(Image.open(file_path), lang='chi_sim+eng')
            if text.strip():
                result.text = text
                result.warnings.append("已通过OCR识别文字")
        except ImportError:
            result.warnings.append("未安装OCR引擎，无法识别图片文字。安装：pip install pytesseract")
        except Exception as e:
            result.warnings.append(f"OCR识别失败: {str(e)}")

        return result

    # ==================== E. 压缩包（递归） ====================

    @staticmethod
    def _extract_archive(file_path: str, archive_type: str, recursion_depth: int,
                        result: ExtractedContent) -> ExtractedContent:
        """抽取压缩包（递归解压+防bomb）"""

        # 安全检查
        file_size = os.path.getsize(file_path)
        if file_size > ContentExtractor.MAX_ARCHIVE_SIZE:
            result.status = "failed"
            result.errors.append(f"压缩包超过大小限制 {ContentExtractor.MAX_ARCHIVE_SIZE / 1024 / 1024}MB")
            return result

        temp_dir = tempfile.mkdtemp()
        attachments_list = []
        total_extracted_size = 0
        file_count = 0

        try:
            # 解压
            if archive_type == 'zip':
                import zipfile
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    # 检查加密
                    for info in zip_ref.filelist:
                        if info.flag_bits & 0x1:  # 加密标志
                            result.warnings.append(f"压缩包包含加密文件: {info.filename}")
                            continue

                        # 检查bomb（解压后大小）
                        total_extracted_size += info.file_size
                        if total_extracted_size > ContentExtractor.MAX_ARCHIVE_SIZE * 10:
                            raise Exception("检测到zip bomb，解压后文件过大")

                        file_count += 1
                        if file_count > ContentExtractor.MAX_ARCHIVE_FILES:
                            raise Exception(f"文件数量超过限制 {ContentExtractor.MAX_ARCHIVE_FILES}")

                    zip_ref.extractall(temp_dir)

            elif archive_type == 'rar':
                import rarfile
                with rarfile.RarFile(file_path, 'r') as rar_ref:
                    file_list = rar_ref.namelist()
                    if len(file_list) > ContentExtractor.MAX_ARCHIVE_FILES:
                        raise Exception(f"文件数量超过限制")
                    rar_ref.extractall(temp_dir)

            elif archive_type == '7z':
                import py7zr
                with py7zr.SevenZipFile(file_path, 'r') as archive:
                    file_list = archive.getnames()
                    if len(file_list) > ContentExtractor.MAX_ARCHIVE_FILES:
                        raise Exception(f"文件数量超过限制")
                    archive.extractall(temp_dir)

            elif archive_type in ['tar', 'gz', 'tgz']:
                import tarfile
                with tarfile.open(file_path, 'r:*') as tar_ref:
                    members = tar_ref.getmembers()
                    if len(members) > ContentExtractor.MAX_ARCHIVE_FILES:
                        raise Exception(f"文件数量超过限制")
                    tar_ref.extractall(temp_dir)

            # 递归处理每个文件
            for root, dirs, files in os.walk(temp_dir):
                for filename in files:
                    file_full_path = os.path.join(root, filename)
                    relative_path = os.path.relpath(file_full_path, temp_dir)

                    # 检查文件名本身（可能包含敏感信息）
                    attachment_meta = {
                        "path": relative_path,
                        "filename": filename,
                        "size": os.path.getsize(file_full_path)
                    }

                    try:
                        # 递归抽取
                        nested_result = ContentExtractor.extract(
                            file_full_path,
                            recursion_depth=recursion_depth + 1
                        )
                        attachment_meta["extraction_result"] = nested_result.to_dict()
                    except Exception as e:
                        attachment_meta["error"] = str(e)

                    attachments_list.append(attachment_meta)

            result.attachments = attachments_list
            result.metadata = {
                "archive_type": archive_type,
                "total_files": len(attachments_list),
                "total_size": total_extracted_size
            }

        except Exception as e:
            result.status = "failed"
            result.errors.append(f"压缩包处理失败: {str(e)}")

        finally:
            # 清理临时目录
            shutil.rmtree(temp_dir, ignore_errors=True)

        return result

    # ==================== F. HTML ====================

    @staticmethod
    def _extract_html(file_path: str, result: ExtractedContent) -> ExtractedContent:
        """抽取HTML（纯文本+链接+表单字段）"""
        try:
            from bs4 import BeautifulSoup
            has_bs4 = True
        except ImportError:
            has_bs4 = False
            result.warnings.append("BeautifulSoup未安装，使用简化HTML解析")

        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            html_content = f.read()

        if has_bs4:
            # 使用BeautifulSoup解析（推荐）
            soup = BeautifulSoup(html_content, 'html.parser')

            # 移除脚本和样式
            for script in soup(["script", "style"]):
                script.decompose()

            # 提取文本
            text = soup.get_text()
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            result.text = '\n'.join(chunk for chunk in chunks if chunk)

            # 结构化：表单字段（可能包含PII）
            structured_data = {}
            for form in soup.find_all('form'):
                form_id = form.get('id', 'unknown')
                for input_tag in form.find_all(['input', 'textarea', 'select']):
                    field_name = input_tag.get('name', input_tag.get('id', 'unknown'))
                    field_type = input_tag.get('type', 'text')
                    path = f"form.{form_id}.{field_name}"
                    structured_data[path] = {
                        "type": field_type,
                        "placeholder": input_tag.get('placeholder'),
                        "value": input_tag.get('value')
                    }
        else:
            # 降级方案：使用正则表达式简单提取（不推荐，但能工作）
            import re

            # 移除script和style标签
            html_content = re.sub(r'<script[^>]*>.*?</script>', '', html_content, flags=re.DOTALL | re.IGNORECASE)
            html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL | re.IGNORECASE)

            # 移除HTML标签
            text = re.sub(r'<[^>]+>', ' ', html_content)

            # 清理空白
            text = re.sub(r'\s+', ' ', text)
            text = text.strip()

            result.text = text
            structured_data = {}
            result.warnings.append("HTML解析使用简化模式，可能遗漏部分结构化数据")

        if structured_data:
            result.structured = structured_data

        return result
