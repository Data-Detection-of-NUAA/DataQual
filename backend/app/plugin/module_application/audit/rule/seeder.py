"""
Utility helpers to seed default GDPR规则到 audit_rule 表.
"""
from __future__ import annotations

import asyncio
import json
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .default_rules import DEFAULT_GDPR_RULES
from .model import AuditRule

_seed_lock = asyncio.Lock()
_seed_initialized = False


async def ensure_default_rules(db: AsyncSession) -> None:
    """
    Insert缺省GDPR规则 when they are missing.

    该函数在进程生命周期内只执行一次，避免重复写入。
    """
    global _seed_initialized
    if _seed_initialized:
        return

    async with _seed_lock:
        if _seed_initialized:
            return

        if not DEFAULT_GDPR_RULES:
            _seed_initialized = True
            return

        codes: List[str] = [rule["rule_code"] for rule in DEFAULT_GDPR_RULES]
        result = await db.execute(
            select(AuditRule.rule_code).where(AuditRule.rule_code.in_(codes))
        )
        existing_codes = {row[0] for row in result.all()}

        missing_rules = [
            rule for rule in DEFAULT_GDPR_RULES if rule["rule_code"] not in existing_codes
        ]

        if missing_rules:
            for payload in missing_rules:
                data = payload.copy()
                expression = data.get("rule_expression")
                if expression and isinstance(expression, dict):
                    data["rule_expression"] = json.dumps(expression, ensure_ascii=False)
                db.add(AuditRule(**data))
            await db.flush()

        _seed_initialized = True
