from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

VARIABLE_NAMES = (
    "dose_g",
    "water_g",
    "ratio",
    "water_temp_c",
    "grind_setting",
    "brew_time_s",
    "milk_ml",
    "ice_g",
    "sweetener_g",
)

EDITABLE_VARIABLE_NAMES = (
    "dose_g",
    "water_g",
    "water_temp_c",
    "grind_setting",
    "brew_time_s",
    "milk_ml",
    "ice_g",
    "sweetener_g",
)


class RecipeVariables(BaseModel):
    model_config = ConfigDict(extra="forbid")

    dose_g: float | None = Field(default=None, ge=5, le=100, allow_inf_nan=False)
    water_g: float | None = Field(default=None, ge=10, le=2000, allow_inf_nan=False)
    ratio: float | None = Field(default=None, ge=1, le=30, allow_inf_nan=False)
    water_temp_c: float | None = Field(default=None, ge=0, le=100, allow_inf_nan=False)
    grind_setting: str | None = Field(default=None, min_length=1, max_length=40)
    brew_time_s: int | None = Field(default=None, ge=10, le=900)
    milk_ml: float | None = Field(default=None, ge=0, le=1000, allow_inf_nan=False)
    ice_g: float | None = Field(default=None, ge=0, le=500, allow_inf_nan=False)
    sweetener_g: float | None = Field(default=None, ge=0, le=200, allow_inf_nan=False)

    @model_validator(mode="after")
    def ratio_matches_water_dose(self) -> "RecipeVariables":
        if (
            self.dose_g is not None
            and self.water_g is not None
            and self.ratio is not None
            and abs(self.ratio - (self.water_g / self.dose_g)) > 0.2
        ):
            raise ValueError("ratio must match water_g / dose_g within 0.2")
        return self


class RecipeIngredient(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(min_length=1, max_length=100)
    amount: float = Field(ge=0, allow_inf_nan=False)
    unit: str = Field(min_length=1, max_length=20)


class RecipeStep(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^rst_")
    order: int = Field(ge=1, le=20)
    instruction: str = Field(min_length=1, max_length=500)
    duration_s: int = Field(ge=0, le=7200)
    target: str = Field(min_length=1, max_length=300)


class Recipe(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^recipe_")
    session_id: str
    version: int = Field(ge=1)
    name: str = Field(min_length=1, max_length=120)
    brewer: str = Field(min_length=1, max_length=80)
    method: Literal["pour_over", "espresso", "immersion", "other"]
    servings: int = Field(ge=1, le=10)
    variables: RecipeVariables
    ingredients: list[RecipeIngredient] = Field(min_length=1, max_length=20)
    steps: list[RecipeStep] = Field(min_length=1, max_length=20)
    source_plan_version: int = Field(ge=1)
    total_sources: dict[str, Any] | None = None
    created_at: str


class Tasting(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^taste_")
    recipe_id: str = Field(pattern=r"^recipe_")
    recipe_version: int = Field(ge=1)
    sourness: int = Field(ge=1, le=5)
    sweetness: int = Field(ge=1, le=5)
    bitterness: int = Field(ge=1, le=5)
    body: int = Field(ge=1, le=5)
    aroma: int = Field(ge=1, le=5)
    aftertaste: int = Field(ge=1, le=5)
    overall: int = Field(ge=1, le=5)
    notes: str = Field(default="", max_length=500)
    created_at: str


class Adjustment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(pattern=r"^adj_")
    recipe_id: str = Field(pattern=r"^recipe_")
    base_version: int = Field(ge=1)
    new_version: int = Field(ge=2)
    variable: str
    from_value: float | str
    to_value: float | str
    reason: str = Field(min_length=1, max_length=300)
    expected_effect: str = Field(default="", max_length=300)
    tasting_id: str | None = None
    created_at: str


class RecipeVersion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recipe_id: str = Field(pattern=r"^recipe_")
    version: int = Field(ge=1)
    name: str
    brewer: str
    method: Literal["pour_over", "espresso", "immersion", "other"]
    servings: int = Field(ge=1, le=10)
    variables: RecipeVariables
    created_at: str
    tasting: Tasting | None = None
    adjustment: Adjustment | None = None


class RecipeRef(BaseModel):
    recipe_id: str
    version: int


class VariableDiff(BaseModel):
    variable: str
    base_value: float | str | None = None
    target_value: float | str | None = None
    delta: float | None = None


class TastingComparison(BaseModel):
    base_tasting_id: str
    target_tasting_id: str
    deltas: dict[str, int]


class RecipeCompare(BaseModel):
    base: RecipeRef
    target: RecipeRef
    variable_diffs: list[VariableDiff]
    tasting_comparison: TastingComparison | None = None
    notes: list[str]


class RecipeCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    base_plan_version: int = Field(ge=1)
    demo: bool = False


class TastingRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sourness: int = Field(ge=1, le=5)
    sweetness: int = Field(ge=1, le=5)
    bitterness: int = Field(ge=1, le=5)
    body: int = Field(ge=1, le=5)
    aroma: int = Field(ge=1, le=5)
    aftertaste: int = Field(ge=1, le=5)
    overall: int = Field(ge=1, le=5)
    notes: str = Field(default="", max_length=500)


class AdjustmentRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    base_version: int = Field(ge=1)
    variable: str | None = None
    to_value: Any | None = None
    variables: dict[str, Any] | None = None
    water_source_confirmation: dict[str, Any] | None = None
    reason: str = Field(min_length=1, max_length=300)
    tasting_id: str | None = None


class AdjustmentResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    recipe: Recipe
    adjustment: Adjustment