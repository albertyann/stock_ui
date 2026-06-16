from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from pydantic import BaseModel
from typing import Optional
import httpx
import json

from app.database import get_db
from app.models import StockSurvey
from app.config import get_settings


router = APIRouter(prefix="/ai", tags=["ai"])


class ChatRequest(BaseModel):
    ts_code: str
    message: str
    stock_context: Optional[dict] = None


class ChatResponse(BaseModel):
    success: bool
    data: Optional[str] = None
    error: Optional[str] = None


class SurveyCreate(BaseModel):
    ts_code: str
    query: Optional[str] = None
    content: str
    source: Optional[str] = "ai_chat"


def serialize_survey(survey: StockSurvey) -> dict:
    return {
        "id": survey.id,
        "ts_code": survey.ts_code,
        "query": survey.query,
        "content": survey.content,
        "source": survey.source,
        "created_at": survey.created_at.isoformat() if survey.created_at else None,
        "updated_at": survey.updated_at.isoformat() if survey.updated_at else None,
    }


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
):
    settings = get_settings()

    api_key = settings.ai_api_key
    model = settings.ai_model
    base_url = settings.ai_base_url

    if not api_key:
        return ChatResponse(success=False, error="AI API key not configured")
    if not model:
        return ChatResponse(success=False, error="AI model not configured")
    if not base_url:
        return ChatResponse(success=False, error="AI base URL not configured")

    system_prompt = (
        "你是一位专业的A股股票分析师。请根据用户的问题和提供的股票信息，"
        "给出简洁、专业、有数据支撑的分析或资料查询结果。"
    )

    user_content = request.message
    if request.stock_context:
        context_text = json.dumps(request.stock_context, ensure_ascii=False)
        user_content = f"股票 {request.ts_code} 的上下文信息：{context_text}\n\n用户问题：{request.message}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]

    try:
        async with httpx.AsyncClient(timeout=settings.ai_timeout) as client:
            response = await client.post(
                f"{base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": 0.7,
                },
            )
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            return ChatResponse(success=True, data=content)
    except httpx.HTTPStatusError as e:
        return ChatResponse(
            success=False,
            error=f"AI API error: {e.response.status_code} {e.response.text}",
        )
    except Exception as e:
        return ChatResponse(success=False, error=f"AI request failed: {str(e)}")


@router.post("/survey", response_model=dict)
async def create_survey(
    data: SurveyCreate,
    db: AsyncSession = Depends(get_db),
):
    survey = StockSurvey(
        ts_code=data.ts_code,
        query=data.query,
        content=data.content,
        source=data.source,
    )
    db.add(survey)
    await db.commit()
    await db.refresh(survey)
    return {"success": True, "data": serialize_survey(survey)}


@router.get("/surveys/{ts_code}", response_model=dict)
async def list_surveys(
    ts_code: str,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(StockSurvey)
        .where(StockSurvey.ts_code == ts_code)
        .order_by(desc(StockSurvey.created_at))
        .limit(limit)
    )
    result = await db.execute(stmt)
    surveys = result.scalars().all()
    return {"success": True, "data": [serialize_survey(s) for s in surveys]}
