from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class IdentifierRef:
    attribute: str
    value: str


@dataclass(frozen=True, slots=True)
class AnchorRef:
    entity: str
    identifier: IdentifierRef | None = None
    surface: str = ''


@dataclass(frozen=True, slots=True)
class DurationRef:
    value: int
    unit: str


@dataclass(frozen=True, slots=True)
class ScenarioRef:
    event_type: str
    duration: DurationRef | None = None
    start_time: str | None = None
    severity: str | None = None
    raw_event: str = ''


@dataclass(frozen=True, slots=True)
class GoalRef:
    type: str
    target_entity: str | None = None
    target_metric: str | None = None
    deadline: str | None = None


@dataclass(frozen=True, slots=True)
class ConstraintRef:
    statuses: list[str] = field(default_factory=list)
    time_window: str | None = None
    limit: int = 20


@dataclass(frozen=True, slots=True)
class QuestionDSL:
    mode: str
    anchor: AnchorRef
    scenario: ScenarioRef | None
    goal: GoalRef
    constraints: ConstraintRef = field(default_factory=ConstraintRef)
    reasoning_scope: str = 'expand_graph'
    target_attributes: list[str] = field(default_factory=list)
