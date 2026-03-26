
ENTITY_ZH_MAP = {
    "pod": "pod", "building": "大楼", "arrival-plan": "到达计划",
    "placement-plan": "落位建议方案", "work-assignment": "施工分配",
    "pod-schedule": "pod排期", "sla-standard": "标准SLA",
    "activity-template": "活动模板", "activity-instance": "活动实例",
    "milestone": "里程碑", "room": "机房", "floor": "楼层",
    "project": "项目", "shipment": "发货单", "crew": "施工队",
    "arrival-event": "到货事件", "activity-dependency-template": "活动依赖模板",
    "constraint-violation": "约束冲突", "decision-recommendation": "决策建议"
}

RELATION_RULES = {
    "REFERENCES": [("decision-recommendation", "arrival-plan"), ("constraint-violation", "pod")],
    "VIOLATION": [("constraint-violation", "pod")],
    "PLANS": [("arrival-plan", "pod"), ("placement-plan", "pod")],
    "ASSIGNS-TO": [("work-assignment", "pod")],
    "CONTAINS": [("pod-schedule", "activity-instance")],
    "APPLIES-TO": [("sla-standard", "activity-template"), ("pod-schedule", "pod")],
    "CONSTRAINS": [("milestone", "room")],
    "AGGREGATES": [("floor", "room"), ("project", "pod")],
    "SHIPS": [("shipment", "pod")],
    "ASSIGNED-TO": [("pod", "building")],
    "EXECUTES": [("crew", "work-assignment")],
    "GENERATES": [("activity-template", "activity-instance")],
    "HAS-EVENT": [("pod", "arrival-event")],
    "HAS-ACTIVITY": [("pod", "activity-instance")],
    "PRECEDES": [("activity-instance", "activity-instance")],
    "REFERENCES_PRE": [("activity-dependency-template", "activity-template")],
    "REFERENCES_SUC": [("activity-dependency-template", "activity-template")]
}