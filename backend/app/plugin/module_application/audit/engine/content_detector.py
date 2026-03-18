"""
内容检测器（Detection Layer）
职责：对抽取后的内容进行PII/敏感数据/安全风险检测
输出：检测结果（类型、位置、置信度、风险等级、处置建议）
"""
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum


class DetectionType(Enum):
    """检测类型枚举"""
    # ① 个人数据 PII
    NAME = "姓名"
    PHONE = "手机号"
    EMAIL = "邮箱"
    IDCARD = "身份证号"
    ADDRESS = "地址"
    IP_ADDRESS = "IP地址"
    MAC_ADDRESS = "MAC地址"
    COOKIE_ID = "Cookie ID"
    DEVICE_ID = "设备标识"
    USER_ID = "用户ID"
    ORDER_ID = "订单号"

    # ② 特殊类别/敏感数据
    HEALTH_DATA = "健康数据"
    BIOMETRIC = "生物识别"
    GENETIC = "基因数据"
    RELIGION = "宗教信仰"
    POLITICAL = "政治观点"
    SEXUAL_ORIENTATION = "性取向"

    # ③ 儿童数据
    AGE = "年龄"
    BIRTH_DATE = "出生日期"
    MINOR_INDICATOR = "未成年人标识"

    # ④ 安全敏感信息
    PASSWORD = "密码"
    API_KEY = "API密钥"
    ACCESS_TOKEN = "访问令牌"
    PRIVATE_KEY = "私钥"
    DATABASE_CONNECTION = "数据库连接串"
    AWS_KEY = "AWS密钥"
    GITHUB_TOKEN = "GitHub Token"
    JWT_TOKEN = "JWT令牌"

    # ⑤ 金融数据
    BANK_CARD = "银行卡号"
    CREDIT_CARD = "信用卡号"
    CVV = "CVV码"

    # ⑥ 其他
    VEHICLE_PLATE = "车牌号"
    PASSPORT = "护照号"
    DRIVER_LICENSE = "驾驶证号"


class RiskLevel(Enum):
    """风险等级"""
    CRITICAL = "严重"  # 密码、私钥、健康数据
    HIGH = "高"        # 身份证、银行卡、生物识别
    MEDIUM = "中"      # 手机号、邮箱、地址
    LOW = "低"         # 用户ID、订单号
    INFO = "信息"      # 年龄、性别


@dataclass
class DetectionResult:
    """单条检测结果"""
    detection_type: DetectionType     # 检测类型
    risk_level: RiskLevel            # 风险等级
    matched_value: str               # 匹配到的值
    location: str                    # 位置（路径/行号/页码）
    context: str                     # 上下文（前后文）
    confidence: float                # 置信度 0-1
    recommendation: str              # 处置建议

    def to_dict(self) -> Dict:
        return {
            "detection_type": self.detection_type.value,
            "risk_level": self.risk_level.value,
            "matched_value": self.matched_value,
            "location": self.location,
            "context": self.context,
            "confidence": self.confidence,
            "recommendation": self.recommendation
        }


class ContentDetector:
    """统一内容检测器"""

    # ==================== 正则模式库 ====================

    # ① 个人数据 PII
    PATTERNS = {
        # 中国手机号：1开头11位（独立数字，不是更长数字的一部分）
        DetectionType.PHONE: r'\b1[3-9]\d{9}\b',

        # 邮箱
        DetectionType.EMAIL: r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',

        # 身份证号：18位（含X）- 优先级高于银行卡号
        DetectionType.IDCARD: r'\b\d{17}[\dXx]\b',

        # IP地址
        DetectionType.IP_ADDRESS: r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b',

        # MAC地址
        DetectionType.MAC_ADDRESS: r'\b([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})\b',

        # IPv6
        'IPV6': r'\b(?:[0-9a-fA-F]{1,4}:){7}[0-9a-fA-F]{1,4}\b',

        # 银行卡号：16-19位（需要Luhn校验，在_assess_detection中处理）
        DetectionType.BANK_CARD: r'\b\d{16,19}\b',

        # 车牌号（中国）
        DetectionType.VEHICLE_PLATE: r'[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼使领][A-Z][A-Z0-9]{5}',

        # 护照号（中国）
        DetectionType.PASSPORT: r'\b[EGP]\d{8}\b',

        # ④ 安全敏感信息（按优先级排序）

        # JWT Token（优先级最高，避免被API_KEY误匹配）
        DetectionType.JWT_TOKEN: r'eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+',

        # GitHub Token
        DetectionType.GITHUB_TOKEN: r'ghp_[0-9a-zA-Z]{36}',

        # AWS Access Key
        DetectionType.AWS_KEY: r'AKIA[0-9A-Z]{16}',

        # 数据库连接串
        DetectionType.DATABASE_CONNECTION: r'(jdbc|mongodb|mysql|postgresql|redis)://[^\s]+',

        # 私钥（PEM格式）
        DetectionType.PRIVATE_KEY: r'-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----',

        # Access Token
        DetectionType.ACCESS_TOKEN: r'(access_token|bearer)\s*[:=]\s*["\']?([A-Za-z0-9_-]+)["\']?',

        # 密码字段（通过字段名判断）
        'PASSWORD_FIELD': r'(password|passwd|pwd|pass|secret)[\s:=]',

        # API Key（通用模式，优先级最低，放在最后）
        DetectionType.API_KEY: r'\b[A-Za-z0-9]{32,}\b',
    }

    # 特殊类别关键词（需要上下文判断）
    SENSITIVE_KEYWORDS = {
        DetectionType.HEALTH_DATA: [
            '病历', '诊断', '治疗', '处方', '病史', '疾病', '血型', '体检', '医院',
            'medical', 'diagnosis', 'prescription', 'disease', 'blood type', 'hospital'
        ],
        DetectionType.RELIGION: [
            '宗教', '信仰', '佛教', '基督教', '伊斯兰教', '天主教',
            'religion', 'faith', 'christian', 'muslim', 'buddhist'
        ],
        DetectionType.POLITICAL: [
            '政治', '党派', '政党', '政治观点', '政治倾向',
            'political', 'party affiliation', 'political view'
        ],
        DetectionType.BIOMETRIC: [
            '指纹', '虹膜', '人脸', '声纹', '掌纹', '生物特征',
            'fingerprint', 'iris', 'facial', 'voiceprint', 'biometric'
        ],
        DetectionType.GENETIC: [
            '基因', 'DNA', 'RNA', '遗传', '染色体', '基因组',
            'gene', 'genetic', 'genome', 'chromosome'
        ]
    }

    @staticmethod
    def detect(extracted_content: Dict[str, Any]) -> List[DetectionResult]:
        """
        对抽取内容进行检测

        Args:
            extracted_content: ExtractedContent.to_dict()

        Returns:
            检测结果列表
        """
        results = []

        # 优先级：结构化数据 > 纯文本
        # 如果有结构化数据，优先检测结构化数据（避免重复）
        has_structured = extracted_content.get('structured') and len(extracted_content.get('structured', {})) > 0

        # 1. 检测结构化数据（优先）
        if has_structured:
            results.extend(ContentDetector._detect_in_structured(
                extracted_content['structured']
            ))

        # 2. 检测纯文本（仅当没有结构化数据时）
        if not has_structured and extracted_content.get('text'):
            results.extend(ContentDetector._detect_in_text(
                extracted_content['text'],
                location_prefix="text"
            ))

        # 3. 检测元数据
        if extracted_content.get('metadata'):
            results.extend(ContentDetector._detect_in_metadata(
                extracted_content['metadata']
            ))

        # 4. 检测附件（递归）
        if extracted_content.get('attachments'):
            for attachment in extracted_content['attachments']:
                if 'extraction_result' in attachment:
                    nested_results = ContentDetector.detect(attachment['extraction_result'])
                    # 添加路径前缀
                    for result in nested_results:
                        result.location = f"attachment:{attachment['path']} -> {result.location}"
                    results.extend(nested_results)

        return results

    @staticmethod
    def _detect_in_text(text: str, location_prefix: str = "text") -> List[DetectionResult]:
        """在纯文本中检测"""
        results = []
        detected_positions = set()  # 记录已检测的位置，避免重复

        # 1. 基于正则的检测（按优先级顺序）
        for detection_type, pattern in ContentDetector.PATTERNS.items():
            if isinstance(detection_type, str):  # 跳过辅助模式
                continue

            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                matched_value = match.group()
                match_start = match.start()
                match_end = match.end()

                # 检查是否已被其他类型检测（避免重复）
                if any(match_start >= start and match_end <= end for start, end in detected_positions):
                    continue

                # 计算位置（行号）
                line_num = text[:match_start].count('\n') + 1
                location = f"{location_prefix}:line_{line_num}"

                # 提取上下文（前后50字符）
                start = max(0, match_start - 50)
                end = min(len(text), match_end + 50)
                context = text[start:end]

                # 置信度和风险等级
                confidence, risk_level = ContentDetector._assess_detection(
                    detection_type, matched_value, context
                )

                # 过滤低置信度结果（< 0.7）
                if confidence < 0.7:
                    continue

                # 生成建议
                recommendation = ContentDetector._generate_recommendation(
                    detection_type, risk_level
                )

                results.append(DetectionResult(
                    detection_type=detection_type,
                    risk_level=risk_level,
                    matched_value=matched_value,
                    location=location,
                    context=context,
                    confidence=confidence,
                    recommendation=recommendation
                ))

                # 记录已检测位置
                detected_positions.add((match_start, match_end))

        # 2. 基于关键词的检测（特殊类别）
        for detection_type, keywords in ContentDetector.SENSITIVE_KEYWORDS.items():
            for keyword in keywords:
                if keyword.lower() in text.lower():
                    # 找到所有出现位置
                    positions = [m.start() for m in re.finditer(re.escape(keyword), text, re.IGNORECASE)]
                    for pos in positions:
                        line_num = text[:pos].count('\n') + 1
                        location = f"{location_prefix}:line_{line_num}"

                        start = max(0, pos - 50)
                        end = min(len(text), pos + len(keyword) + 50)
                        context = text[start:end]

                        results.append(DetectionResult(
                            detection_type=detection_type,
                            risk_level=RiskLevel.HIGH,
                            matched_value=keyword,
                            location=location,
                            context=context,
                            confidence=0.7,  # 关键词匹配置信度较低，需人工确认
                            recommendation="发现特殊类别数据关键词，需人工审查确认上下文"
                        ))

        return results

    @staticmethod
    def _detect_in_structured(structured_data: Dict[str, Any]) -> List[DetectionResult]:
        """在结构化数据中检测（优先使用字段名，避免重复检测）"""
        results = []

        for path, value in structured_data.items():
            if not value:
                continue

            value_str = str(value)
            path_lower = path.lower()
            detected = False  # 标记是否已通过字段名检测

            # ==================== 1. 优先基于字段名检测（高置信度） ====================

            # 姓名字段
            if any(kw in path_lower for kw in ['name', '姓名', '名称']) and not any(x in path_lower for x in ['user', 'file', 'table']):
                if ContentDetector._is_chinese_name(value_str):
                    results.append(DetectionResult(
                        detection_type=DetectionType.NAME,
                        risk_level=RiskLevel.MEDIUM,
                        matched_value=value_str,
                        location=f"field:{path}",
                        context=f"{path} = {value_str}",
                        confidence=0.95,
                        recommendation="姓名字段需脱敏处理"
                    ))
                    detected = True

            # 手机号字段
            elif any(kw in path_lower for kw in ['phone', 'mobile', 'tel', '手机', '电话']):
                if re.match(r'1[3-9]\d{9}', value_str):
                    results.append(DetectionResult(
                        detection_type=DetectionType.PHONE,
                        risk_level=RiskLevel.MEDIUM,
                        matched_value=value_str,
                        location=f"field:{path}",
                        context=f"{path} = {value_str}",
                        confidence=0.98,
                        recommendation="⚡中风险：手机号建议脱敏或限制访问权限"
                    ))
                    detected = True

            # 邮箱字段
            elif any(kw in path_lower for kw in ['email', 'mail', '邮箱']):
                if '@' in value_str:
                    results.append(DetectionResult(
                        detection_type=DetectionType.EMAIL,
                        risk_level=RiskLevel.MEDIUM,
                        matched_value=value_str,
                        location=f"field:{path}",
                        context=f"{path} = {value_str}",
                        confidence=0.98,
                        recommendation="⚡中风险：邮箱建议脱敏或限制访问权限"
                    ))
                    detected = True

            # 身份证字段
            elif any(kw in path_lower for kw in ['idcard', 'id_card', 'identity', '身份证']):
                if re.match(r'\d{17}[\dXx]', value_str):
                    results.append(DetectionResult(
                        detection_type=DetectionType.IDCARD,
                        risk_level=RiskLevel.HIGH,
                        matched_value=value_str,
                        location=f"field:{path}",
                        context=f"{path} = {value_str}",
                        confidence=0.98,
                        recommendation="⚠️高风险：身份证号必须加密存储并严格限制访问"
                    ))
                    detected = True

            # 银行卡字段
            elif any(kw in path_lower for kw in ['bank_card', 'bankcard', 'card_no', '银行卡', '卡号']):
                if re.match(r'\d{16,19}', value_str):
                    results.append(DetectionResult(
                        detection_type=DetectionType.BANK_CARD,
                        risk_level=RiskLevel.HIGH,
                        matched_value=value_str,
                        location=f"field:{path}",
                        context=f"{path} = {value_str}",
                        confidence=0.98,
                        recommendation="⚠️高风险：银行卡号必须加密存储并严格限制访问"
                    ))
                    detected = True

            # 地址字段
            elif any(kw in path_lower for kw in ['address', 'addr', '地址', '住址']):
                results.append(DetectionResult(
                    detection_type=DetectionType.ADDRESS,
                    risk_level=RiskLevel.MEDIUM,
                    matched_value=value_str[:50],  # 限制长度
                    location=f"field:{path}",
                    context=f"{path} = {value_str[:50]}...",
                    confidence=0.95,
                    recommendation="⚡中风险：地址信息建议脱敏处理"
                ))
                detected = True

            # IP地址字段
            elif any(kw in path_lower for kw in ['ip_address', 'ip', 'ipaddr']):
                if re.match(r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}', value_str):
                    results.append(DetectionResult(
                        detection_type=DetectionType.IP_ADDRESS,
                        risk_level=RiskLevel.LOW,
                        matched_value=value_str,
                        location=f"field:{path}",
                        context=f"{path} = {value_str}",
                        confidence=0.98,
                        recommendation="💡低风险：IP地址可能用于用户追踪"
                    ))
                    detected = True

            # 设备ID字段
            elif any(kw in path_lower for kw in ['device_id', 'deviceid', 'imei', 'udid', '设备']):
                results.append(DetectionResult(
                    detection_type=DetectionType.DEVICE_ID,
                    risk_level=RiskLevel.MEDIUM,
                    matched_value=value_str[:50],
                    location=f"field:{path}",
                    context=f"{path} = {value_str[:50]}",
                    confidence=0.95,
                    recommendation="⚡中风险：设备标识可能用于用户追踪"
                ))
                detected = True

            # 健康信息字段
            elif any(kw in path_lower for kw in ['health', 'medical', 'disease', '健康', '病历', '疾病']):
                if value_str and value_str != '无':
                    results.append(DetectionResult(
                        detection_type=DetectionType.HEALTH_DATA,
                        risk_level=RiskLevel.CRITICAL,
                        matched_value=value_str[:50],
                        location=f"field:{path}",
                        context=f"{path} = {value_str[:50]}",
                        confidence=0.95,
                        recommendation="❌严重：健康数据属于特殊类别，必须获得明确同意并加密存储"
                    ))
                    detected = True

            # 密码字段（高风险！）
            elif any(kw in path_lower for kw in ['password', 'passwd', 'pwd', 'secret', '密码']):
                results.append(DetectionResult(
                    detection_type=DetectionType.PASSWORD,
                    risk_level=RiskLevel.CRITICAL,
                    matched_value="***REDACTED***",  # 不记录明文
                    location=f"field:{path}",
                    context=f"{path} = [REDACTED]",
                    confidence=1.0,
                    recommendation="❌严重：密码字段不应出现在数据集中，立即删除！"
                ))
                detected = True

            # API Key字段
            elif any(kw in path_lower for kw in ['api_key', 'apikey', 'access_key', 'secret_key']):
                results.append(DetectionResult(
                    detection_type=DetectionType.API_KEY,
                    risk_level=RiskLevel.CRITICAL,
                    matched_value="***REDACTED***",
                    location=f"field:{path}",
                    context=f"{path} = [REDACTED]",
                    confidence=1.0,
                    recommendation="❌严重：API密钥泄露，立即轮换！"
                ))
                detected = True

            # Token字段
            elif any(kw in path_lower for kw in ['token', 'bearer', 'authorization', 'auth']):
                results.append(DetectionResult(
                    detection_type=DetectionType.ACCESS_TOKEN,
                    risk_level=RiskLevel.CRITICAL,
                    matched_value="***REDACTED***",
                    location=f"field:{path}",
                    context=f"{path} = [REDACTED]",
                    confidence=0.95,
                    recommendation="❌严重：访问令牌泄露，立即撤销！"
                ))
                detected = True

            # 年龄字段
            elif any(kw in path_lower for kw in ['age', '年龄']):
                try:
                    age_val = int(value_str)
                    if age_val < 18:
                        results.append(DetectionResult(
                            detection_type=DetectionType.AGE,
                            risk_level=RiskLevel.HIGH,
                            matched_value=value_str,
                            location=f"field:{path}",
                            context=f"{path} = {value_str} (未成年人)",
                            confidence=0.98,
                            recommendation="⚠️高风险：未成年人数据需获得监护人同意"
                        ))
                    else:
                        results.append(DetectionResult(
                            detection_type=DetectionType.AGE,
                            risk_level=RiskLevel.LOW,
                            matched_value=value_str,
                            location=f"field:{path}",
                            context=f"{path} = {value_str}",
                            confidence=0.98,
                            recommendation="💡低风险：年龄信息可能用于用户画像"
                        ))
                    detected = True
                except ValueError:
                    pass

            # 出生日期字段
            elif any(kw in path_lower for kw in ['birth', 'birthday', 'dob', '出生']):
                results.append(DetectionResult(
                    detection_type=DetectionType.BIRTH_DATE,
                    risk_level=RiskLevel.MEDIUM,
                    matched_value=value_str,
                    location=f"field:{path}",
                    context=f"{path} = {value_str}",
                    confidence=0.95,
                    recommendation="⚡中风险：出生日期可能用于身份识别"
                ))
                detected = True

            # ==================== 2. 如果字段名未匹配，使用正则检测（较低置信度） ====================
            if not detected:
                for detection_type, pattern in ContentDetector.PATTERNS.items():
                    if isinstance(detection_type, str):
                        continue

                    match = re.search(pattern, value_str)
                    if match:
                        confidence, risk_level = ContentDetector._assess_detection(
                            detection_type, match.group(), f"{path}={value_str}"
                        )

                        results.append(DetectionResult(
                            detection_type=detection_type,
                            risk_level=risk_level,
                            matched_value=match.group(),
                            location=f"field:{path}",
                            context=f"{path} = {value_str}",
                            confidence=confidence * 0.8,  # 降低置信度（因为没有字段名提示）
                            recommendation=ContentDetector._generate_recommendation(detection_type, risk_level)
                        ))
                        break  # 只取第一个匹配，避免重复

        return results

    @staticmethod
    def _detect_in_metadata(metadata: Dict[str, Any]) -> List[DetectionResult]:
        """在元数据中检测（作者、GPS等）"""
        results = []

        # 作者信息
        if 'author' in metadata and metadata['author']:
            results.append(DetectionResult(
                detection_type=DetectionType.NAME,
                risk_level=RiskLevel.LOW,
                matched_value=str(metadata['author']),
                location="metadata:author",
                context=f"文档作者: {metadata['author']}",
                confidence=0.8,
                recommendation="元数据包含作者信息，建议清除"
            ))

        # GPS定位信息（EXIF）
        if 'exif' in metadata and metadata['exif']:
            exif = metadata['exif']
            if 'GPSInfo' in exif or 'GPS' in str(exif):
                results.append(DetectionResult(
                    detection_type=DetectionType.ADDRESS,
                    risk_level=RiskLevel.HIGH,
                    matched_value="GPS坐标",
                    location="metadata:EXIF:GPS",
                    context="图片包含GPS定位信息",
                    confidence=1.0,
                    recommendation="⚠️高风险：图片包含精确定位信息，建议删除EXIF"
                ))

        # 公司/组织信息
        if 'company' in metadata and metadata['company']:
            results.append(DetectionResult(
                detection_type=DetectionType.USER_ID,  # 暂用USER_ID类型
                risk_level=RiskLevel.LOW,
                matched_value=str(metadata['company']),
                location="metadata:company",
                context=f"公司: {metadata['company']}",
                confidence=0.7,
                recommendation="元数据包含公司信息"
            ))

        return results

    @staticmethod
    def _assess_detection(detection_type: DetectionType, value: str, context: str) -> Tuple[float, RiskLevel]:
        """
        评估检测置信度和风险等级

        Returns:
            (confidence, risk_level)
        """
        # 基础风险等级
        risk_mapping = {
            # 严重
            DetectionType.PASSWORD: RiskLevel.CRITICAL,
            DetectionType.API_KEY: RiskLevel.CRITICAL,
            DetectionType.PRIVATE_KEY: RiskLevel.CRITICAL,
            DetectionType.ACCESS_TOKEN: RiskLevel.CRITICAL,
            DetectionType.DATABASE_CONNECTION: RiskLevel.CRITICAL,
            DetectionType.HEALTH_DATA: RiskLevel.CRITICAL,
            DetectionType.BIOMETRIC: RiskLevel.CRITICAL,

            # 高
            DetectionType.IDCARD: RiskLevel.HIGH,
            DetectionType.BANK_CARD: RiskLevel.HIGH,
            DetectionType.PASSPORT: RiskLevel.HIGH,
            DetectionType.GENETIC: RiskLevel.HIGH,

            # 中
            DetectionType.PHONE: RiskLevel.MEDIUM,
            DetectionType.EMAIL: RiskLevel.MEDIUM,
            DetectionType.ADDRESS: RiskLevel.MEDIUM,
            DetectionType.NAME: RiskLevel.MEDIUM,

            # 低
            DetectionType.USER_ID: RiskLevel.LOW,
            DetectionType.ORDER_ID: RiskLevel.LOW,
            DetectionType.IP_ADDRESS: RiskLevel.LOW,
        }

        risk_level = risk_mapping.get(detection_type, RiskLevel.MEDIUM)

        # 置信度计算
        confidence = 0.8  # 默认

        # 身份证号：校验位验证
        if detection_type == DetectionType.IDCARD:
            confidence = ContentDetector._validate_idcard(value)

        # 银行卡号：Luhn算法
        elif detection_type == DetectionType.BANK_CARD:
            confidence = ContentDetector._validate_bank_card(value)

        # 手机号：号段验证
        elif detection_type == DetectionType.PHONE:
            if value[0] == '1' and value[1] in '3456789':
                confidence = 0.95
            else:
                confidence = 0.7

        # 邮箱：常见域名
        elif detection_type == DetectionType.EMAIL:
            common_domains = ['gmail.com', 'qq.com', '163.com', '126.com', 'sina.com', 'hotmail.com']
            if any(domain in value.lower() for domain in common_domains):
                confidence = 0.95
            else:
                confidence = 0.8

        # 私钥/密码等：字段名确认
        elif detection_type in [DetectionType.PASSWORD, DetectionType.PRIVATE_KEY, DetectionType.API_KEY]:
            if re.search(r'(key|token|password|secret)', context, re.IGNORECASE):
                confidence = 0.99
            else:
                confidence = 0.7

        return confidence, risk_level

    @staticmethod
    def _validate_idcard(idcard: str) -> float:
        """
        身份证号校验位验证

        Returns:
            置信度
        """
        if len(idcard) != 18:
            return 0.5

        # 校验位算法
        coefficients = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
        check_codes = '10X98765432'

        try:
            total = sum(int(idcard[i]) * coefficients[i] for i in range(17))
            check_digit = check_codes[total % 11]
            if idcard[17].upper() == check_digit:
                return 0.99  # 校验通过
            else:
                return 0.6   # 校验失败，可能是假数据
        except:
            return 0.5

    @staticmethod
    def _validate_bank_card(card_number: str) -> float:
        """
        银行卡Luhn算法验证

        Returns:
            置信度
        """
        try:
            digits = [int(d) for d in card_number]
            checksum = 0
            for i, digit in enumerate(reversed(digits)):
                if i % 2 == 1:
                    digit *= 2
                    if digit > 9:
                        digit -= 9
                checksum += digit

            if checksum % 10 == 0:
                return 0.95
            else:
                return 0.6
        except:
            return 0.5

    @staticmethod
    def _is_chinese_name(text: str) -> bool:
        """判断是否为中文姓名（2-4个汉字）"""
        return bool(re.match(r'^[\u4e00-\u9fa5]{2,4}$', text.strip()))

    @staticmethod
    def _generate_recommendation(detection_type: DetectionType, risk_level: RiskLevel) -> str:
        """生成处置建议"""
        if risk_level == RiskLevel.CRITICAL:
            return f"❌严重风险：{detection_type.value}不应出现，立即删除或脱敏！"
        elif risk_level == RiskLevel.HIGH:
            return f"⚠️高风险：{detection_type.value}需加密存储或脱敏处理"
        elif risk_level == RiskLevel.MEDIUM:
            return f"⚡中风险：{detection_type.value}建议脱敏或限制访问权限"
        elif risk_level == RiskLevel.LOW:
            return f"ℹ️低风险：{detection_type.value}建议记录访问日志"
        else:
            return f"信息：{detection_type.value}已记录"


class GDPRDetectionReport:
    """GDPR检测报告生成器"""

    @staticmethod
    def generate_report(detection_results: List[DetectionResult], extracted_content: Dict) -> Dict[str, Any]:
        """
        生成GDPR审计报告

        Args:
            detection_results: 检测结果列表
            extracted_content: 原始抽取内容

        Returns:
            报告字典
        """
        # 按类型分组
        by_type = {}
        for result in detection_results:
            type_name = result.detection_type.value
            if type_name not in by_type:
                by_type[type_name] = []
            by_type[type_name].append(result)

        # 按风险等级分组
        by_risk = {
            RiskLevel.CRITICAL.value: [],
            RiskLevel.HIGH.value: [],
            RiskLevel.MEDIUM.value: [],
            RiskLevel.LOW.value: [],
            RiskLevel.INFO.value: []
        }
        for result in detection_results:
            by_risk[result.risk_level.value].append(result)

        # 统计
        report = {
            "summary": {
                "file_path": extracted_content.get('file_path'),
                "file_type": extracted_content.get('file_type'),
                "file_size": extracted_content.get('file_size'),
                "extraction_status": extracted_content.get('status'),
                "total_detections": len(detection_results),
                "detection_by_risk": {
                    risk: len(items) for risk, items in by_risk.items()
                },
                "detection_by_type": {
                    type_name: len(items) for type_name, items in by_type.items()
                }
            },
            "risk_breakdown": {
                "critical_findings": [r.to_dict() for r in by_risk[RiskLevel.CRITICAL.value]],
                "high_findings": [r.to_dict() for r in by_risk[RiskLevel.HIGH.value]],
                "medium_findings": [r.to_dict() for r in by_risk[RiskLevel.MEDIUM.value]],
                "low_findings": [r.to_dict() for r in by_risk[RiskLevel.LOW.value]],
            },
            "type_breakdown": {
                type_name: [r.to_dict() for r in items]
                for type_name, items in by_type.items()
            },
            "recommendations": GDPRDetectionReport._generate_recommendations(by_risk),
            "compliance_score": GDPRDetectionReport._calculate_compliance_score(by_risk),
            "extraction_warnings": extracted_content.get('warnings', []),
            "extraction_errors": extracted_content.get('errors', [])
        }

        return report

    @staticmethod
    def _generate_recommendations(by_risk: Dict[str, List]) -> List[str]:
        """生成总体建议"""
        recommendations = []

        critical_count = len(by_risk[RiskLevel.CRITICAL.value])
        high_count = len(by_risk[RiskLevel.HIGH.value])
        medium_count = len(by_risk[RiskLevel.MEDIUM.value])

        if critical_count > 0:
            recommendations.append(
                f"❌发现{critical_count}项严重风险（密码/密钥/健康数据等），必须立即处理！"
            )

        if high_count > 0:
            recommendations.append(
                f"⚠️发现{high_count}项高风险（身份证/银行卡/生物识别等），需加密或脱敏"
            )

        if medium_count > 0:
            recommendations.append(
                f"⚡发现{medium_count}项中风险（手机号/邮箱/地址等），建议脱敏处理"
            )

        if critical_count == 0 and high_count == 0:
            recommendations.append("✅未发现严重或高风险敏感数据")

        return recommendations

    @staticmethod
    def _calculate_compliance_score(by_risk: Dict[str, List]) -> float:
        """
        计算合规分数 0-100

        严重风险：-20分/项
        高风险：-10分/项
        中风险：-5分/项
        低风险：-1分/项
        """
        score = 100.0

        score -= len(by_risk[RiskLevel.CRITICAL.value]) * 20
        score -= len(by_risk[RiskLevel.HIGH.value]) * 10
        score -= len(by_risk[RiskLevel.MEDIUM.value]) * 5
        score -= len(by_risk[RiskLevel.LOW.value]) * 1

        return max(0.0, score)
