"""
审计模块通用Controller
提供符合开发规范的统一接口
"""
from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import JSONResponse
from typing import Optional

from app.common.response import SuccessResponse
from app.core.router_class import OperationLogRoute
from app.core.dependencies import AuthPermission
from app.api.v1.module_system.auth.schema import AuthSchema
from app.plugin.module_application.audit.file.storage import save_upload_file


CommonRouter = APIRouter(
    route_class=OperationLogRoute,
    prefix="/audit",
    tags=["审计模块通用接口"]
)


@CommonRouter.post("/upload", summary="通用文件上传")
async def upload_file(
    file_type: str = Form(..., description="文件类型（如：pdf, csv, xlsx等）"),
    category: str = Form(..., description="文件类别（regulation: 法规, dataset: 数据集）"),
    file: UploadFile = File(..., description="上传的文件"),
    task_id: Optional[int] = Form(None, description="关联的任务ID（可选）"),
    auth: AuthSchema = Depends(AuthPermission(["module_application:audit:upload"]))
) -> JSONResponse:
    """
    通用文件上传接口（符合开发规范）

    规范路径：POST /audit/upload

    参数：
    - file_type: 文件类型/扩展名（pdf, csv, xlsx等）
    - category: 文件类别（regulation=法规, dataset=数据集）
    - file: 上传的文件
    - task_id: 可选，关联的任务ID

    返回：
    {
        "file_path": "完整文件路径",
        "original_name": "原始文件名",
        "stored_name": "存储文件名",
        "file_size": 文件大小（字节）,
        "file_extension": "文件扩展名"
    }

    落盘目录：
    backend/static/audit/uploads/{category}/YYYY/MM/DD/{uuid}.{ext}
    """
    saved_file = await save_upload_file(
        file=file,
        file_type=file_type,
        category=category
    )

    result = {
        "file_path": saved_file.file_path,
        "original_name": saved_file.original_name,
        "stored_name": saved_file.stored_name,
        "file_size": saved_file.file_size,
        "file_extension": saved_file.file_extension,
        "task_id": task_id,  # 返回关联的任务ID
        "category": category
    }

    return SuccessResponse(data=result, msg="文件上传成功")
