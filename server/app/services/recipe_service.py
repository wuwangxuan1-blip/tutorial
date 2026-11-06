from __future__ import annotations

import copy
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from pydantic import ValidationError

from ..errors import ApiError, invalid_request, not_found
from ..ids import new_id
from ..models.recipe import (
    EDITABLE_VARIABLE_NAMES,
    VARIABLE_NAMES,
    Adjustment,
    AdjustmentRequest,
    Recipe,
    RecipeCompare,
    RecipeIngredient,
    RecipeRef,
    RecipeStep,
    RecipeVariables,
    RecipeVersion,
    Tasting,
    TastingComparison,
    TastingRequest,
    VariableDiff,
)
from .store import JsonStore

_TASTING_DIMENSIONS = (
    "sourness",
    "sweetness",
    "bitterness",
    "body",
    "aroma",
    "aftertaste",
    "overall",
)

_WATER_EXPLICIT_LABELS = frozenset(
    {
        "总水量",
        "总注水",
        "注水总量",
        "总水",
        "总量",
        "总计",
        "合计",
        "最终注水",
        "最终水量",
    }
)
_WATER_TERMINAL_LABELS = frozenset(
    {
        "继续注水至",
        "继续注水到",
        "注水至",
        "注水到",
        "加水至",
        "加到",
        "累计注水",
        "累计水量",
    }
)
_WATER_LOCAL_LABELS = frozenset(
    {
        "闷蒸注水",
        "闷蒸用水",
        "闷蒸水量",
        "闷蒸",
        "洗滤纸用水",
        "温杯用水",
        "润洗用水",
        "预热水",
    }
)
_WATER_GENERAL_LABELS = frozenset({"水", "水量"})
_WATER_MENTION_PATTERN = re.compile(
    r"(?P<label>"
    r"继续注水至|继续注水到|"
    r"总水量|总注水|注水总量|总水|总量|总计|合计|最终注水|最终水量|"
    r"闷蒸注水|闷蒸用水|闷蒸水量|闷蒸|洗滤纸用水|温杯用水|润洗用水|预热水|"
    r"注水至|注水到|加水至|加到|累计注水|累计水量|"
    r"注水|水量|(?<![用温洗预])水"
    r")\s*[:：]?\s*(?:约\s*)?(?:至|到)?\s*"
    r"(?P<value>[0-9]+(?:\.[0-9]+)?)\s*(?:g|克)"
)

_TIME_EXPRESSION = (
    r"(?P<expression>"
    r"(?P<minutes>[0-9]+)\s*分(?:钟)?\s*(?P<part_seconds>[0-9]+)?\s*秒?"
    r"|(?P<seconds>[0-9]+)\s*秒"
    r")"
)
_TOTAL_TIME_PATTERN = re.compile(
    r"(?P<label>总时长|总时间)\s*[:：]?\s*约?\s*" + _TIME_EXPRESSION
)
_STEP_TIME_PATTERN = re.compile(
    r"(?P<label>(?<![置蒸步])(?:时长|用时))\s*[:：]?\s*约?\s*" + _TIME_EXPRESSION
)
_FALLBACK_TIME_PATTERNS = (
    (r"约\s*([0-9]+)\s*分(?:钟)?\s*([0-9]+)?\s*秒?", "minutes"),
    (r"约\s*([0-9]+)\s*秒", "seconds"),
    (r"([0-9]+)\s*分\s*([0-9]+)\s*秒", "minutes"),
    (r"([0-9]+)\s*分(?:钟)?", "minutes"),
    (r"([0-9]+)\s*秒", "seconds"),
)


@dataclass(frozen=True)
class _WaterMention:
    label: str
    value: float
    kind: str
    value_start: int
    value_end: int


@dataclass(frozen=True)
class _TimeMatch:
    label: str
    seconds: int
    expression_start: int
    expression_end: int


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _clean_text(value: Any, limit: int) -> str:
    return str(value or "").strip()[:limit]


def _format_number(value: Any) -> str:
    number = float(value)
    return str(int(number)) if number.is_integer() else str(number)


def _match_seconds(match: re.Match[str]) -> int:
    minutes = match.group("minutes")
    if minutes is not None:
        seconds = int(minutes) * 60
        part = match.group("part_seconds")
        if part is not None:
            seconds += int(part)
        return seconds
    return int(float(match.group("seconds")))


class RecipeService:
    def __init__(self, store: JsonStore) -> None:
        self.store = store

    async def create_from_plan(
        self,
        session: dict[str, Any],
        plan: dict[str, Any],
        base_plan_version: int,
        *,
        use_demo: bool = False,
    ) -> dict[str, Any]:
        if session["domain"] != "coffee":
            raise ApiError(422, "DOMAIN_MISMATCH", "只有咖啡会话可以创建配方。")
        current = session.get("current_plan_version")
        if current is None:
            raise not_found("该会话还没有计划，不能创建配方。")
        if base_plan_version != current:
            raise ApiError(
                409,
                "VERSION_CONFLICT",
                "计划版本已变化，请刷新后重试。",
                details={"current_plan_version": current},
            )
        existing = await self.store.list_recipes(session["id"])
        if existing:
            return existing[-1]

        variables = self._variables_from_plan(plan, use_demo=use_demo)
        recipe_id = new_id("recipe")
        recipe = {
            "id": recipe_id,
            "session_id": session["id"],
            "version": 1,
            "name": _clean_text(plan.get("title") or "V60 手冲", 120),
            "brewer": _clean_text(
                (session.get("conditions") or {}).get("brewer") or "V60 02",
                80,
            ),
            "method": self._method_for(session, plan),
            "servings": 1,
            "variables": variables,
            "ingredients": self._ingredients(variables),
            "steps": self._steps_from_plan(plan),
            "source_plan_version": plan["version"],
            "created_at": _now(),
        }
        Recipe.model_validate(recipe)
        await self.store.save_recipe(recipe)
        return recipe

    def _demo_variables(self) -> dict[str, Any]:
        return RecipeVariables(
            dose_g=15,
            water_g=225,
            ratio=15.0,
            water_temp_c=92,
            grind_setting="中细",
            brew_time_s=150,
        ).model_dump(exclude_none=True)

    def _plan_text(self, plan: dict[str, Any]) -> str:
        return " ".join(
            [
                str(plan.get("title") or ""),
                str(plan.get("summary") or ""),
                " ".join(str(step.get("instruction") or "") for step in plan["steps"]),
                " ".join(
                    str(item)
                    for step in plan["steps"]
                    for item in (step.get("completion_criteria") or [])
                ),
            ]
        )

    def _time_matches(self, text: str, pattern: re.Pattern[str]) -> list[_TimeMatch]:
        return [
            _TimeMatch(
                label=match.group("label"),
                seconds=_match_seconds(match),
                expression_start=match.start("expression"),
                expression_end=match.end("expression"),
            )
            for match in pattern.finditer(text)
        ]

    def _parse_brew_time(self, text: str) -> int | None:
        explicit = {match.seconds for match in self._time_matches(text, _TOTAL_TIME_PATTERN)}
        if len(explicit) > 1:
            raise ApiError(
                422,
                "INVALID_REQUEST",
                "计划中出现多个不同的总时长；未创建配方，请明确唯一总时长。",
                details={
                    "reason": "brew_time_ambiguous",
                    "candidates": sorted(explicit),
                },
            )
        if explicit:
            return explicit.pop()
        step = self._time_matches(text, _STEP_TIME_PATTERN)
        if step:
            return step[0].seconds
        for pattern, kind in _FALLBACK_TIME_PATTERNS:
            match = re.search(pattern, text)
            if not match:
                continue
            if kind == "minutes":
                seconds = int(match.group(1)) * 60
                if match.lastindex and match.lastindex >= 2 and match.group(2) is not None:
                    seconds += int(match.group(2))
                return seconds
            return int(float(match.group(1)))
        return None

    def _water_mentions(self, text: str) -> list[_WaterMention]:
        mentions: list[_WaterMention] = []
        for match in _WATER_MENTION_PATTERN.finditer(text):
            label = match.group("label")
            if label in _WATER_EXPLICIT_LABELS:
                kind = "explicit"
            elif label in _WATER_TERMINAL_LABELS:
                kind = "terminal"
            elif label in _WATER_LOCAL_LABELS:
                kind = "local"
            else:
                kind = "other"
            mentions.append(
                _WaterMention(
                    label=label,
                    value=float(match.group("value")),
                    kind=kind,
                    value_start=match.start("value"),
                    value_end=match.end("value"),
                )
            )
        return mentions

    def _parse_water_total(self, text: str) -> float | None:
        mentions = self._water_mentions(text)
        explicit = {mention.value for mention in mentions if mention.kind == "explicit"}
        terminal = {mention.value for mention in mentions if mention.kind == "terminal"}
        stage = {
            mention.value
            for mention in mentions
            if mention.kind in {"other", "local"}
        }

        def ambiguous(values: set[float], source: str) -> ApiError:
            return ApiError(
                422,
                "INVALID_REQUEST",
                "计划中出现多个不同的水量，无法确定总水量；未创建配方，请明确总水量。",
                details={
                    "reason": "water_total_ambiguous",
                    "candidates": sorted(values),
                    "source": source,
                },
            )

        if len(explicit) > 1:
            raise ambiguous(explicit, "explicit_total")
        if explicit:
            return explicit.pop()
        if len(terminal) > 1:
            raise ambiguous(terminal, "terminal_pour")
        if terminal:
            return terminal.pop()
        if len(stage) > 1:
            raise ambiguous(stage, "stage_amount")
        if len(stage) == 1:
            value = stage.pop()
            if all(mention.kind == "local" for mention in mentions):
                raise ApiError(
                    422,
                    "INVALID_REQUEST",
                    "计划中只有闷蒸/局部用水量，无法确定总水量；未创建配方，请明确总水量。",
                    details={
                        "reason": "water_total_ambiguous",
                        "candidates": sorted({value}),
                        "source": "local_only",
                    },
                )
            return value
        return None

    def _water_total_spans(self, text: str, old_value: float) -> list[tuple[int, int]]:
        mentions = self._water_mentions(text)
        explicit = [mention for mention in mentions if mention.kind == "explicit"]
        terminal = [mention for mention in mentions if mention.kind == "terminal"]
        general = [
            mention
            for mention in mentions
            if mention.kind == "other"
            and mention.label in _WATER_GENERAL_LABELS
            and mention.value == old_value
        ]
        selected: list[_WaterMention] = []
        if explicit:
            values = {mention.value for mention in explicit}
            if len(values) != 1 or next(iter(values)) != old_value:
                return []
            selected = explicit
        elif terminal:
            values = {mention.value for mention in terminal}
            if len(values) != 1 or next(iter(values)) != old_value:
                return []
            selected = terminal
        return [
            (mention.value_start, mention.value_end)
            for mention in selected + general
        ]

    def _brew_time_spans(self, text: str, old_seconds: int) -> list[tuple[int, int]]:
        explicit = self._time_matches(text, _TOTAL_TIME_PATTERN)
        if explicit:
            values = {match.seconds for match in explicit}
            if len(values) != 1 or next(iter(values)) != old_seconds:
                return []
            return [(match.expression_start, match.expression_end) for match in explicit]
        step = self._time_matches(text, _STEP_TIME_PATTERN)
        values = {match.seconds for match in step}
        if len(values) == 1 and next(iter(values)) == old_seconds:
            return [(match.expression_start, match.expression_end) for match in step]
        return []

    @staticmethod
    def _replace_spans(text: str, spans: list[tuple[int, int]], new_text: str) -> str:
        for start, end in sorted(spans, reverse=True):
            text = text[:start] + new_text + text[end:]
        return text

    def _parse_plan_variables(self, plan: dict[str, Any]) -> dict[str, Any]:
        text = self._plan_text(plan)
        dose = re.search(
            r"咖啡(?:粉|豆)?\s*[:：]?\s*([0-9]+(?:\.[0-9]+)?)\s*(?:g|克)",
            text,
        )
        water_g = self._parse_water_total(text)
        temp = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*(?:°C|℃|度)", text)
        brew_time_s = self._parse_brew_time(text)
        grind = re.search(r"中细|中粗|细砂糖|粗砂糖|细|粗", text)
        if not grind:
            grind = re.search(r"(?:研磨|研磨度|磨豆|粗细)[^。；，,]{0,8}?(中)", text)
        if not all((dose, temp)) or water_g is None or brew_time_s is None:
            raise ApiError(
                422,
                "INVALID_REQUEST",
                "计划中没有用户已确认的完整配方参数；未创建配方，请确认粉量、总水量、水温与时长，或明确选择演示配方。",
                details={"reason": "recipe_parameters_missing"},
            )
        dose_g = float(dose.group(1))
        base_values = {
            "dose_g": dose_g,
            "water_g": water_g,
            "water_temp_c": float(temp.group(1)),
            "brew_time_s": brew_time_s,
        }
        if grind:
            base_values["grind_setting"] = grind.group(0)
        try:
            RecipeVariables.model_validate(base_values)
        except ValidationError as exc:
            raise invalid_request(
                "计划中的配方参数超出允许范围。",
                {"reason": "recipe_parameters_invalid"},
            ) from exc
        parsed = {
            **base_values,
            "ratio": round(water_g / dose_g, 2),
        }
        try:
            return RecipeVariables.model_validate(parsed).model_dump(exclude_none=True)
        except ValidationError as exc:
            raise invalid_request(
                "计划中的配方参数超出允许范围。",
                {"reason": "recipe_parameters_invalid"},
            ) from exc

    def _variables_from_plan(
        self,
        plan: dict[str, Any],
        *,
        use_demo: bool,
    ) -> dict[str, Any]:
        parsed = self._parse_plan_variables(plan)
        if not use_demo:
            return parsed
        demo = self._demo_variables()
        required = ("dose_g", "water_g", "water_temp_c", "brew_time_s")
        mismatched = [
            name for name in required if parsed.get(name) != demo.get(name)
        ]
        if parsed.get("grind_setting") and parsed.get("grind_setting") != demo.get("grind_setting"):
            mismatched.append("grind_setting")
        if mismatched:
            raise ApiError(
                422,
                "INVALID_REQUEST",
                "所选演示配方与当前计划已确认的参数不一致；请按计划参数创建，或重新生成演示计划。",
                details={
                    "reason": "demo_parameters_mismatch",
                    "mismatched": mismatched,
                },
            )
        return demo

    def _method_for(self, session: dict[str, Any], plan: dict[str, Any]) -> str:
        combined = " ".join(
            [
                str((session.get("conditions") or {}).get("brewer") or ""),
                str(plan.get("title") or ""),
                str(plan.get("summary") or ""),
            ]
        ).lower()
        if "v60" in combined or "手冲" in combined:
            return "pour_over"
        return "other"

    def _ingredients(self, variables: dict[str, Any]) -> list[dict[str, Any]]:
        items = [
            {
                "name": "咖啡豆",
                "amount": variables.get("dose_g", 0),
                "unit": "g",
            },
            {
                "name": "水",
                "amount": variables.get("water_g", 0),
                "unit": "g",
            },
        ]
        if "milk_ml" in variables:
            items.append({"name": "牛奶", "amount": variables["milk_ml"], "unit": "ml"})
        if "ice_g" in variables:
            items.append({"name": "冰", "amount": variables["ice_g"], "unit": "g"})
        if "sweetener_g" in variables:
            items.append({"name": "甜味剂", "amount": variables["sweetener_g"], "unit": "g"})
        return items

    def _steps_from_plan(self, plan: dict[str, Any]) -> list[dict[str, Any]]:
        steps = []
        for index, step in enumerate(plan["steps"], start=1):
            target = "；".join(step.get("completion_criteria") or []) or "按步骤说明完成。"
            steps.append(
                {
                    "id": f"rst_{index}",
                    "order": index,
                    "instruction": _clean_text(step.get("instruction"), 500),
                    "duration_s": int(step.get("duration_s") or 0),
                    "target": _clean_text(target, 300),
                }
            )
        return steps

    def _rewrite_steps(
        self,
        steps: list[dict[str, Any]],
        old_variables: dict[str, Any],
        new_variables: dict[str, Any],
    ) -> list[dict[str, Any]]:
        operations: list[tuple[re.Pattern[str], str, str]] = []

        def old_pattern(name: str) -> str | None:
            old_value = old_variables.get(name)
            new_value = new_variables.get(name)
            if old_value is None or new_value is None:
                return None
            old_text = _format_number(old_value)
            new_text = _format_number(new_value)
            if old_text == new_text:
                return None
            return f"{re.escape(old_text)}(?:\\.0+)?"

        separator = r"(?P<sep>\s*[:：]?\s*(?:至|到)?\s*约?\s*)"
        dose_old = old_pattern("dose_g")
        if dose_old:
            operations.append(
                (
                    re.compile(
                        rf"(?P<label>咖啡粉|咖啡豆|粉量|粉重){separator}{dose_old}(?P<unit>\s*(?:g|克))"
                    ),
                    _format_number(new_variables["dose_g"]),
                    "value",
                )
            )
        water_old = old_variables.get("water_g")
        water_new = new_variables.get("water_g")
        water_changed = (
            water_old is not None
            and water_new is not None
            and _format_number(water_old) != _format_number(water_new)
        )
        temp_old = old_pattern("water_temp_c")
        if temp_old:
            operations.append(
                (
                    re.compile(
                        rf"(?P<label>水温|温度){separator}{temp_old}(?P<unit>\s*(?:°C|℃|度))"
                    ),
                    _format_number(new_variables["water_temp_c"]),
                    "value",
                )
            )
        old_time = old_variables.get("brew_time_s")
        new_time = new_variables.get("brew_time_s")
        time_changed = (
            old_time is not None
            and new_time is not None
            and int(old_time) != int(new_time)
        )
        ratio_old = old_pattern("ratio")
        if ratio_old:
            operations.append(
                (
                    re.compile(
                        rf"(?P<label>粉水比|比例)(?P<sep>\s*[:：]?\s*)(?P<prefix>1[:：]){ratio_old}"
                    ),
                    _format_number(new_variables["ratio"]),
                    "ratio",
                )
            )

        def replace(text: str, pattern: re.Pattern[str], new_text: str, kind: str) -> str:
            def repl(match: re.Match[str]) -> str:
                if kind == "ratio":
                    return (
                        match.group("label")
                        + match.group("sep")
                        + match.group("prefix")
                        + new_text
                    )
                return (
                    match.group("label")
                    + match.group("sep")
                    + new_text
                    + match.group("unit")
                )

            return pattern.sub(repl, text)

        updated = copy.deepcopy(steps)
        for step in updated:
            for field in ("instruction", "target"):
                text = str(step.get(field) or "")
                for pattern, new_text, kind in operations:
                    text = replace(text, pattern, new_text, kind)
                if water_changed:
                    text = self._replace_spans(
                        text,
                        self._water_total_spans(text, float(water_old)),
                        _format_number(water_new),
                    )
                if time_changed:
                    text = self._replace_spans(
                        text,
                        self._brew_time_spans(text, int(old_time)),
                        f"{_format_number(new_time)} 秒",
                    )
                step[field] = text
        return updated

    async def get(self, recipe_id: str) -> dict[str, Any]:
        recipe = await self.store.find_recipe(recipe_id)
        if not recipe:
            raise not_found("配方不存在。")
        return recipe

    async def list_for_session(self, session_id: str) -> list[dict[str, Any]]:
        return await self.store.list_recipes(session_id)

    async def add_tasting(
        self,
        recipe_id: str,
        payload: TastingRequest,
    ) -> dict[str, Any]:
        recipe = await self.get(recipe_id)
        tasting = {
            "id": new_id("tasting"),
            "recipe_id": recipe_id,
            "recipe_version": recipe["version"],
            **payload.model_dump(mode="json"),
            "created_at": _now(),
        }
        Tasting.model_validate(tasting)
        await self.store.save_tasting(tasting)
        return tasting

    async def _latest_tasting(
        self,
        recipe_id: str,
        version: int,
    ) -> dict[str, Any] | None:
        for tasting in await self.store.list_tastings(recipe_id):
            if tasting.get("recipe_version") == version:
                return tasting
        return None

    async def adjust(
        self,
        recipe_id: str,
        payload: AdjustmentRequest,
    ) -> tuple[dict[str, Any], dict[str, Any]]:
        base = await self.get(recipe_id)
        recipes = await self.store.list_recipes(base["session_id"])
        latest = recipes[-1] if recipes else base
        if payload.base_version != latest["version"] or base["version"] != latest["version"]:
            raise ApiError(
                409,
                "VERSION_CONFLICT",
                "配方版本已变化，请刷新后重试。",
                details={"current_version": latest["version"]},
            )

        changes = dict(payload.variables or {})
        if payload.variable is not None:
            if payload.to_value is None:
                raise invalid_request(
                    "缺少 to_value。",
                    {"field": "to_value", "reason": "missing_adjustment_value"},
                )
            changes[payload.variable] = payload.to_value
        if not changes:
            raise invalid_request(
                "没有提供调整值。",
                {"field": "variable", "reason": "missing_adjustment_value"},
            )
        base_variables = dict(base["variables"])
        for name, value in changes.items():
            if name not in VARIABLE_NAMES:
                raise invalid_request(
                    "不支持的配方变量。",
                    {"field": "variable", "reason": "unknown_variable"},
                )
            if name not in EDITABLE_VARIABLE_NAMES:
                raise invalid_request(
                    "粉水比是派生变量，不能直接调整；请调整粉量或水量。",
                    {"field": "variable", "reason": "derived_variable"},
                )
            if name not in base_variables:
                raise invalid_request(
                    "该变量不在当前配方中。",
                    {"field": "variable", "reason": "variable_not_present"},
                )
            if value is None:
                raise invalid_request(
                    "调整值不能为空。",
                    {"field": "variable", "reason": "invalid_adjustment_value"},
                )

        active_diff = [
            name
            for name, value in changes.items()
            if name in EDITABLE_VARIABLE_NAMES and value != base_variables.get(name)
        ]
        if len(active_diff) > 1:
            raise ApiError(
                422,
                "SINGLE_VARIABLE_REQUIRED",
                "每次只能主动调整一个变量。",
                details={"changed_variables": active_diff},
            )
        if not active_diff:
            raise invalid_request(
                "新参数与当前版本相同，没有实际变化。",
                {"field": "variable", "reason": "no_parameter_change"},
            )
        variable = active_diff[0]

        try:
            RecipeVariables.model_validate({variable: changes[variable]})
        except ValidationError as exc:
            raise invalid_request(
                "调整值类型或范围不合法。",
                {
                    "field": variable,
                    "reason": "invalid_adjustment_value",
                },
            ) from exc

        candidate = dict(base_variables)
        candidate.update(changes)
        if candidate.get("dose_g") is not None and candidate.get("water_g") is not None:
            candidate["ratio"] = round(
                float(candidate["water_g"]) / float(candidate["dose_g"]),
                2,
            )
        try:
            variables = RecipeVariables.model_validate(candidate)
        except ValidationError as exc:
            raise invalid_request(
                "调整后的配方参数不合法。",
                {
                    "field": variable,
                    "reason": "invalid_adjustment_value",
                },
            ) from exc
        validated_variables = variables.model_dump(exclude_none=True)

        if payload.tasting_id:
            tasting = await self.store.load_tasting(recipe_id, payload.tasting_id)
            if not tasting:
                raise invalid_request(
                    "口味记录不存在。",
                    {"field": "tasting_id", "reason": "unknown_tasting"},
                )
            if tasting.get("recipe_version") != base["version"]:
                raise invalid_request(
                    "口味记录不属于该配方版本。",
                    {"field": "tasting_id", "reason": "tasting_version_mismatch"},
                )

        new_recipe_id = new_id("recipe")
        new_recipe = {
            **base,
            "id": new_recipe_id,
            "version": base["version"] + 1,
            "variables": validated_variables,
            "ingredients": self._ingredients(validated_variables),
            "steps": self._rewrite_steps(
                base.get("steps") or [],
                base_variables,
                validated_variables,
            ),
            "created_at": _now(),
        }
        Recipe.model_validate(new_recipe)
        from_value = base_variables[variable]
        new_value = new_recipe["variables"][variable]
        expected_effect = (
            f"仅主动调整 {variable}；粉水比由实际粉量/水量派生更新。"
            if variable in ("dose_g", "water_g")
            else f"仅调整 {variable}，其他变量保持不变。"
        )
        adjustment = {
            "id": new_id("adjustment"),
            "recipe_id": recipe_id,
            "base_version": base["version"],
            "new_version": new_recipe["version"],
            "variable": variable,
            "from_value": from_value,
            "to_value": new_value,
            "reason": payload.reason.strip(),
            "expected_effect": expected_effect,
            "tasting_id": payload.tasting_id,
            "created_at": _now(),
        }
        Adjustment.model_validate(adjustment)
        await self.store.save_recipe(new_recipe)
        await self.store.save_adjustment(adjustment)
        return new_recipe, adjustment

    async def history(self, recipe_id: str) -> list[dict[str, Any]]:
        recipe = await self.get(recipe_id)
        recipes = await self.store.list_recipes(recipe["session_id"])
        adjustments: dict[int, dict[str, Any]] = {}
        for item in recipes:
            for adjustment in await self.store.list_adjustments(item["id"]):
                adjustments[adjustment["new_version"]] = adjustment
        versions = []
        for item in recipes:
            version = {
                "recipe_id": item["id"],
                "version": item["version"],
                "name": item["name"],
                "brewer": item["brewer"],
                "method": item["method"],
                "servings": item["servings"],
                "variables": item["variables"],
                "created_at": item["created_at"],
                "tasting": await self._latest_tasting(item["id"], item["version"]),
                "adjustment": adjustments.get(item["version"]),
            }
            versions.append(RecipeVersion.model_validate(version).model_dump(mode="json"))
        return versions

    async def compare(
        self,
        recipe_id: str,
        against_id: str,
    ) -> dict[str, Any]:
        base = await self.get(recipe_id)
        target = await self.get(against_id)
        if base["session_id"] != target["session_id"]:
            raise invalid_request(
                "两个配方不属于同一会话，不能对比。",
                {"reason": "recipe_chain_mismatch"},
            )
        base_vars = dict(base["variables"])
        target_vars = dict(target["variables"])
        diffs = []
        for name in VARIABLE_NAMES:
            if name not in base_vars and name not in target_vars:
                continue
            base_value = base_vars.get(name)
            target_value = target_vars.get(name)
            if base_value == target_value:
                continue
            delta = None
            if isinstance(base_value, (int, float)) and isinstance(target_value, (int, float)):
                delta = round(float(target_value) - float(base_value), 3)
            diffs.append(
                VariableDiff(
                    variable=name,
                    base_value=base_value,
                    target_value=target_value,
                    delta=delta,
                ).model_dump(mode="json")
            )

        base_tasting = await self._latest_tasting(base["id"], base["version"])
        target_tasting = await self._latest_tasting(target["id"], target["version"])
        tasting_comparison = None
        if base_tasting and target_tasting:
            tasting_comparison = TastingComparison(
                base_tasting_id=base_tasting["id"],
                target_tasting_id=target_tasting["id"],
                deltas={
                    name: target_tasting[name] - base_tasting[name]
                    for name in _TASTING_DIMENSIONS
                },
            ).model_dump(mode="json")

        active_adjustment = None
        for item in await self.store.list_recipes(base["session_id"]):
            for adjustment in await self.store.list_adjustments(item["id"]):
                if (
                    adjustment.get("new_version") == target["version"]
                    and adjustment.get("base_version") == base["version"]
                ):
                    active_adjustment = adjustment
                    break
            if active_adjustment:
                break

        notes = ["只比较用户主观评分与参数，不代表客观质量结论。"]
        if active_adjustment:
            variable = active_adjustment["variable"]
            if variable in ("dose_g", "water_g"):
                notes.append(
                    f"本次主动改变 {variable}；粉水比由实际粉量/水量派生更新，不算第二个主动调整。"
                )
            else:
                notes.append(f"本次主动改变 {variable}，其他变量保持一致。")
        elif len(diffs) == 1:
            notes.append(f"本次只改变 {diffs[0]['variable']}，其他变量保持一致。")
        elif not diffs:
            notes.append("两个版本的参数一致。")
        if base_tasting is None or target_tasting is None:
            notes.append("至少一个版本缺少用户口味记录，未做评分对比。")

        comparison = RecipeCompare(
            base=RecipeRef(recipe_id=base["id"], version=base["version"]),
            target=RecipeRef(recipe_id=target["id"], version=target["version"]),
            variable_diffs=[VariableDiff.model_validate(item) for item in diffs],
            tasting_comparison=(
                TastingComparison.model_validate(tasting_comparison)
                if tasting_comparison
                else None
            ),
            notes=notes,
        )
        return comparison.model_dump(mode="json")