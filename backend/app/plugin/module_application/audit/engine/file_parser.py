"""
文件解析器
支持多种文件格式的解析：txt, csv, xlsx, json, xml, docx, pdf
"""
import csv
import json
import xml.etree.ElementTree as ET
from typing import Any, List, Dict
import pandas as pd


class FileParser:
    """文件解析器类"""

    @staticmethod
    def parse_file(file_path: str, file_type: str) -> Any:
        """
        根据文件类型解析文件

        Args:
            file_path: 文件路径
            file_type: 文件类型 (txt/csv/xlsx/json/xml/docx/pdf)

        Returns:
            解析后的数据
        """
        file_type = file_type.lower().replace('.', '')

        if file_type == 'txt':
            return FileParser._parse_txt(file_path)
        elif file_type == 'csv':
            return FileParser._parse_csv(file_path)
        elif file_type in ['xlsx', 'xls']:
            return FileParser._parse_xlsx(file_path)
        elif file_type == 'json':
            return FileParser._parse_json(file_path)
        elif file_type == 'xml':
            return FileParser._parse_xml(file_path)
        elif file_type == 'docx':
            return FileParser._parse_docx(file_path)
        elif file_type == 'pdf':
            return FileParser._parse_pdf(file_path)
        else:
            raise ValueError(f"不支持的文件类型: {file_type}")

    @staticmethod
    def _parse_txt(file_path: str) -> str:
        """解析TXT文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # 尝试其他编码
            with open(file_path, 'r', encoding='gbk') as f:
                return f.read()

    @staticmethod
    def _parse_csv(file_path: str) -> List[Dict[str, Any]]:
        """解析CSV文件"""
        try:
            df = pd.read_csv(file_path, encoding='utf-8')
        except UnicodeDecodeError:
            df = pd.read_csv(file_path, encoding='gbk')

        # 替换 NaN 为 None
        df = df.where(pd.notna(df), None)
        return df.to_dict('records')

    @staticmethod
    def _parse_xlsx(file_path: str) -> List[Dict[str, Any]]:
        """解析Excel文件"""
        df = pd.read_excel(file_path)
        # 替换 NaN 为 None
        df = df.where(pd.notna(df), None)
        return df.to_dict('records')

    @staticmethod
    def _parse_json(file_path: str) -> Any:
        """解析JSON文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    @staticmethod
    def _parse_xml(file_path: str) -> str:
        """解析XML文件"""
        tree = ET.parse(file_path)
        root = tree.getroot()
        return ET.tostring(root, encoding='unicode')

    @staticmethod
    def _parse_docx(file_path: str) -> str:
        """解析DOCX文件"""
        try:
            from docx import Document
            doc = Document(file_path)
            return '\n'.join([para.text for para in doc.paragraphs])
        except ImportError:
            raise ImportError("请安装 python-docx: pip install python-docx")

    @staticmethod
    def _parse_pdf(file_path: str) -> str:
        """解析PDF文件"""
        try:
            import pdfplumber
            with pdfplumber.open(file_path) as pdf:
                text = ''
                for page in pdf.pages:
                    text += page.extract_text() or ''
                return text
        except ImportError:
            raise ImportError("请安装 pdfplumber: pip install pdfplumber")
