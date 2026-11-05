from __future__ import annotations

from fastapi import APIRouter, Query, Request

from ..errors import ApiError, not_found
from ..models.recipe import (
    AdjustmentRequest,
    AdjustmentResponse,
    Recipe,
    RecipeCompare,
    RecipeCreateRequest,
    RecipeVersion,
    Tasting,
    TastingRequest,
)

router = APIRouter()


@router.post(
    "/sessions/{session_id}/recipes",
    response_model=Recipe,
    response_model_exclude_none=True,
    status_code=201,
)
async def create_recipe(
    request: Request,
    session_id: str,
    payload: RecipeCreateRequest,
) -> Recipe:
    store = request.app.state.store
    session = await store.load_session(session_id)
    if not session:
        raise not_found("会话不存在。")
    if session["domain"] != "coffee":
        raise ApiError(422, "DOMAIN_MISMATCH", "只有咖啡会话可以创建配方。")
    version = session.get("current_plan_version")
    if version is None:
        raise not_found("该会话还没有计划，不能创建配方。")
    plan = await store.load_plan(session_id, version)
    if not plan:
        raise not_found("该会话还没有计划，不能创建配方。")
    recipe = await request.app.state.recipe_service.create_from_plan(
        session,
        plan,
        payload.base_plan_version,
        use_demo=payload.demo,
    )
    return Recipe.model_validate(recipe)


@router.get(
    "/sessions/{session_id}/recipes",
    response_model=list[Recipe],
    response_model_exclude_none=True,
)
async def list_recipes(request: Request, session_id: str) -> list[Recipe]:
    store = request.app.state.store
    session = await store.load_session(session_id)
    if not session:
        raise not_found("会话不存在。")
    items = await request.app.state.recipe_service.list_for_session(session_id)
    return [Recipe.model_validate(item) for item in items]


@router.get(
    "/recipes/{recipe_id}",
    response_model=Recipe,
    response_model_exclude_none=True,
)
async def get_recipe(request: Request, recipe_id: str) -> Recipe:
    recipe = await request.app.state.recipe_service.get(recipe_id)
    return Recipe.model_validate(recipe)


@router.post(
    "/recipes/{recipe_id}/tastings",
    response_model=Tasting,
    response_model_exclude_none=True,
    status_code=201,
)
async def add_tasting(
    request: Request,
    recipe_id: str,
    payload: TastingRequest,
) -> Tasting:
    tasting = await request.app.state.recipe_service.add_tasting(recipe_id, payload)
    return Tasting.model_validate(tasting)


@router.post(
    "/recipes/{recipe_id}/adjustments",
    response_model=AdjustmentResponse,
    response_model_exclude_none=True,
    status_code=201,
)
async def adjust_recipe(
    request: Request,
    recipe_id: str,
    payload: AdjustmentRequest,
) -> AdjustmentResponse:
    recipe, adjustment = await request.app.state.recipe_service.adjust(recipe_id, payload)
    return AdjustmentResponse(
        recipe=Recipe.model_validate(recipe),
        adjustment=adjustment,
    )


@router.get(
    "/recipes/{recipe_id}/history",
    response_model=list[RecipeVersion],
    response_model_exclude_none=True,
)
async def recipe_history(request: Request, recipe_id: str) -> list[RecipeVersion]:
    items = await request.app.state.recipe_service.history(recipe_id)
    return [RecipeVersion.model_validate(item) for item in items]


@router.get(
    "/recipes/{recipe_id}/compare",
    response_model=RecipeCompare,
    response_model_exclude_none=True,
)
async def compare_recipes(
    request: Request,
    recipe_id: str,
    against: str = Query(min_length=1),
) -> RecipeCompare:
    result = await request.app.state.recipe_service.compare(recipe_id, against)
    return RecipeCompare.model_validate(result)