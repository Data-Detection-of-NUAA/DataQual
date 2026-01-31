"""
瀹¤浠诲姟妯″瀷
"""
from sqlalchemy import String, Text, Integer, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.core.base_model import ModelMixin, MappedBase


class AuditTask(ModelMixin, MappedBase):
    """瀹¤浠诲姟琛?"""
    __tablename__ = 'audit_task'
    __table_args__ = {'comment': '瀹¤浠诲姟琛?'}

    task_name: Mapped[str] = mapped_column(String(200), nullable=False, comment='浠诲姟鍚嶇О')
    task_status: Mapped[str] = mapped_column(String(20), default='pending',
                                             comment='浠诲姟鐘舵€侊細pending/processing/completed/failed')

    # 姝ラ1: 娉曡鏂囦欢
    regulation_file_type: Mapped[str | None] = mapped_column(String(50), comment='娉曡鏂囦欢绫诲瀷锛歵xt/xml/docx/pdf')
    regulation_file_path: Mapped[str | None] = mapped_column(String(500), comment='娉曡鏂囦欢璺緞')
    regulation_file_name: Mapped[str | None] = mapped_column(String(200), comment='娉曡鏂囦欢鍚?')
    regulation_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('audit_regulation.id', ondelete="SET NULL"),
        comment='寮曡繘鍦ㄨ祫璁缓鐨勮鍒橧D',
        index=True
    )

    # 姝ラ2: AI鍖归厤鐨勮鍒?
    matched_rules: Mapped[dict | None] = mapped_column(JSON, comment='AI鍖归厤鐨勮鍒橧D鍒楄〃')
    selected_rules: Mapped[dict | None] = mapped_column(JSON, comment='鐢ㄦ埛鏈€缁堥€夋嫨鐨勮鍒橧D鍒楄〃')

    # 姝ラ3: 鏁版嵁闆嗘枃浠?
    dataset_file_type: Mapped[str | None] = mapped_column(String(50), comment='鏁版嵁闆嗘枃浠剁被鍨?')
    dataset_file_path: Mapped[str | None] = mapped_column(String(500), comment='鏁版嵁闆嗘枃浠惰矾寰?')
    dataset_file_name: Mapped[str | None] = mapped_column(String(200), comment='鏁版嵁闆嗘枃浠跺悕')

    # 瀹¤缁撴灉
    total_records: Mapped[int] = mapped_column(Integer, default=0, comment='鎬昏褰曟暟')
    error_records: Mapped[int] = mapped_column(Integer, default=0, comment='閿欒璁板綍鏁?')
    data_errors: Mapped[dict | None] = mapped_column(JSON, comment='鏁版嵁閿欒璇︽儏')
    label_errors: Mapped[dict | None] = mapped_column(JSON, comment='鏍囩閿欒璇︽儏')
    audit_report_path: Mapped[str | None] = mapped_column(String(500), comment='瀹¤鎶ュ憡璺緞')


class AuditError(ModelMixin, MappedBase):
    """瀹¤閿欒璇︽儏琛?"""
    __tablename__ = 'audit_error'
    __table_args__ = {'comment': '瀹¤閿欒璇︽儏琛?'}

    task_id: Mapped[int] = mapped_column(Integer, nullable=False, comment='浠诲姟ID', index=True)
    error_type: Mapped[str] = mapped_column(String(20), nullable=False, comment='閿欒绫诲瀷锛歞ata/label', index=True)

    # 閿欒浣嶇疆
    row_number: Mapped[int | None] = mapped_column(Integer, comment='琛屽彿')
    column_name: Mapped[str | None] = mapped_column(String(100), comment='鍒楀悕')
    field_name: Mapped[str | None] = mapped_column(String(100), comment='瀛楁鍚?')

    # 閿欒鍐呭
    original_value: Mapped[str | None] = mapped_column(Text, comment='鍘熷鍊?')
    error_message: Mapped[str | None] = mapped_column(Text, comment='閿欒鎻忚堪')
    rule_id: Mapped[int | None] = mapped_column(Integer, comment='杩濆弽鐨勮鍒橧D')
    severity: Mapped[str | None] = mapped_column(String(20), comment='涓ラ噸绾у埆')

    # 閿欒鏍囪浣嶇疆锛堢敤浜庡墠绔尝娴嚎鏍囪锛?
    start_position: Mapped[int | None] = mapped_column(Integer, comment='閿欒寮€濮嬩綅缃?')
    end_position: Mapped[int | None] = mapped_column(Integer, comment='閿欒缁撴潫浣嶇疆')
