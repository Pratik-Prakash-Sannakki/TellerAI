"""The capability artifact: what discovery saves and replay loads (schema v2). No I/O.

Moved verbatim from the discovery notebook's "Save artifact" cell. Targets are found by rungs:
1 the target's own OCR text, 2 a label + offset (anchor), 3 a template crop, or a table cell.
"""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

SCHEMA_VERSION = 2  # matches Capability.schema_version's Literal; a loader refuses any other


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


Name = Annotated[str, Field(pattern=r"^[a-z][a-z0-9_]*$")]


class OcrText(Strict):  # rung 1: the target's own text
    text: str
    ordinal: int = 1


class Anchor(Strict):  # rung 2: a label, then an offset from its box centre
    label: str
    ordinal: int = 1
    offset: tuple[int, int]


class TableCell(Strict):
    row_key: str
    column: str


class Target(Strict):
    ocr_text: OcrText | None = None
    anchor: Anchor | None = None
    template: str | None = None  # rung 3: crop path, relative to the YAML
    table_cell: TableCell | None = None

    @model_validator(mode="after")
    def findable(self) -> "Target":
        if not (self.anchor or self.template or self.table_cell):
            raise ValueError("a target needs an anchor, a template or a table cell")
        return self


class Navigate(Strict):
    action: Literal["navigate"] = "navigate"
    path: str = Field(pattern=r"^/")


class Click(Strict):
    action: Literal["click"] = "click"
    target: Target
    cleanup: bool = False  # the final logout: replay ends logged out; after the checkpoint


class Type(Strict):
    action: Literal["type"] = "type"
    target: Target
    value: str  # "{{input}}" or "{{secret:name}}", never a literal


class Select(Strict):
    action: Literal["select"] = "select"
    target: Target
    option: str  # "{{input}}"
    index: int | None = None  # Nth <select> on the page (document order); None = by point


class Scroll(Strict):
    action: Literal["scroll"] = "scroll"
    direction: Literal["up", "down"]


class Extract(Strict):
    action: Literal["extract"] = "extract"
    target: Target
    save_as: Name
    # the value is the first match inside the box (a phone in a sentence)
    pattern: str | None = None


class Header(Strict):  # a table's first asked column header, found like a rung 2 label
    label: str
    ordinal: int = 1


class ExtractTable(Strict):
    action: Literal["extract_table"] = "extract_table"
    header: Header
    columns: list[str] = Field(min_length=1)  # header texts; the first is `header`
    save_as: Name
    row_limit: int = Field(50, ge=1)


Step = Annotated[
    Navigate | Click | Type | Select | Scroll | Extract | ExtractTable,
    Field(discriminator="action"),
]


class Input(Strict):
    name: Name
    type: str = "string"
    description: str = ""


class Output(Strict):
    name: Name
    type: str  # a value type, or "table": a list of {column: text} rows
    description: str
    columns: list[str] | None = None  # a table's columns


class Capability(Strict):
    schema_version: Literal[2] = 2
    name: Name
    version: int = 1
    description: str
    base_url: str = Field(pattern=r"^https?://")
    viewport: tuple[int, int]
    device_scale_factor: float = 1
    inputs: list[Input] = []
    outputs: list[Output] = []
    secrets: list[Name] = []
    steps: list[Step] = Field(min_length=1)
    checkpoint: str  # text on the final screen that proves success


class CapabilityMeta(Strict):  # R11: the only part the model writes. Loose on purpose:
    name: str  # slugged by build_capability, so a bad name cannot fail it
    description: str
    inputs: dict[str, str] = {}  # input name -> description; unknown names are ignored
    success_text: str
