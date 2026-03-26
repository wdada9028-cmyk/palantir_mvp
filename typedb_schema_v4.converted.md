# typedb_schema_v4

## Object Types（实体）

### `Project`

中文释义：项目
关键属性：
- `project_id`：所属项目ID
- `project_name`：项目名称
- `project_status`：项目状态
- `product_type`：产品类型
- `cooling_mode`：制冷模式
- `project_scene`：项目场景
- `planned_start_date`：计划启动日期

### `Building`

中文释义：大楼
关键属性：
- `building_id`：所属大楼ID
- `building_name`：大楼名称

### `Floor`

中文释义：楼层
关键属性：
- `floor_id`：所属楼层ID
- `floor_no`：楼层编号
- `install_sequence`：安装顺序

### `Room`

中文释义：机房
关键属性：
- `room_id`：所属机房ID
- `room_type`：机房类型
- `max_pod_capacity`：最大PoD容量
- `required_handover_pod_count`：要求交付PoD数量
- `room_status`：机房状态

### `PoDPosition`

中文释义：PoD落位
关键属性：
- `position_id`：PoD落位ID
- `position_code`：PoD落位编码
- `position_status`：PoD落位状态
- `sequence_no`：顺序号

### `PoD`

中文释义：PoD
关键属性：
- `pod_id`：PoD ID
- `pod_code`：PoD编码
- `pod_type`：PoD类型
- `pod_status`：PoD状态
- `planned_arrival_time`：计划到货时间
- `actual_arrival_time`：实际到货时间
- `planned_install_start_time`：计划安装开始时间
- `actual_install_start_time`：实际安装开始时间
- `planned_handover_time`：计划交付时间
- `actual_handover_time`：实际交付时间

### `Shipment`

中文释义：发货单
关键属性：
- `shipment_id`：发货单ID
- `shipment_no`：发货单号
- `shipment_status`：发货单状态
- `planned_ship_time`：计划发货时间
- `planned_arrival_time`：计划到货时间
- `actual_arrival_time`：实际到货时间

### `ArrivalEvent`

中文释义：到货事件
关键属性：
- `arrival_event_id`：到货事件ID
- `arrival_status`：到货状态
- `actual_arrival_time`：实际到货时间
- `receiving_location`：收货地点
- `confirmed_by`：确认人

### `ArrivalPlan`

中文释义：到货方案
关键属性：
- `arrival_plan_id`：到货方案ID
- `recommended_arrival_time`：建议到货时间
- `latest_safe_arrival_time`：最晚安全到货时间
- `earliest_useful_arrival_time`：最早有效到货时间
- `backlog_risk_level`：积压风险等级
- `plan_status`：方案状态

### `ActivityTemplate`

中文释义：活动模板
关键属性：
- `template_id`：活动模板ID
- `l1_code`：一级编码
- `l1_name`：一级名称
- `l2_code`：二级编码
- `l2_name`：二级名称
- `activity_category`：活动类别
- `completion_flag`：完成标记
- `product_type`：产品类型
- `cooling_mode`：制冷模式
- `project_scene`：项目场景

### `ActivityDependencyTemplate`

中文释义：活动依赖模板
关键属性：
- `dependency_template_id`：活动依赖模板ID
- `dependency_type`：依赖类型

### `SLAStandard`

中文释义：标准SLA
关键属性：
- `sla_id`：SLA ID
- `standard_duration`：标准时长
- `duration_unit`：时长单位
- `crew_capacity_assumption`：施工队产能假设
- `scenario_tag`：场景标签

### `ActivityInstance`

中文释义：活动实例
关键属性：
- `activity_id`：活动ID
- `activity_status`：活动状态
- `planned_start_time`：计划开始时间
- `planned_finish_time`：计划完成时间
- `latest_start_time`：最晚开始时间
- `latest_finish_time`：最晚完成时间
- `actual_start_time`：实际开始时间
- `actual_finish_time`：实际完成时间
- `is_milestone_anchor`：是否里程碑锚点
- `sequence_no`：顺序号

### `PoDSchedule`

中文释义：PoD排期
关键属性：
- `pod_schedule_id`：PoD排期ID
- `schedule_type`：排期类型
- `generated_at`：生成时间
- `is_feasible`：是否可执行

### `Crew`

中文释义：施工队
关键属性：
- `crew_id`：施工队ID
- `crew_status`：施工队状态
- `daily_pod_capacity`：每日PoD产能
- `parallel_limit`：并行上限

### `WorkAssignment`

中文释义：施工分配
关键属性：
- `assignment_id`：施工分配ID
- `assignment_date`：施工分配日期
- `start_time`：开始时间
- `finish_time`：结束时间
- `assignment_status`：施工分配状态

### `PlacementPlan`

中文释义：落位建议方案
关键属性：
- `placement_plan_id`：落位建议方案ID
- `placement_score`：落位建议方案评分
- `plan_status`：方案状态

### `ConstraintViolation`

中文释义：约束冲突
关键属性：
- `violation_id`：冲突ID
- `violation_type`：冲突类型
- `severity`：严重程度
- `message`：冲突说明

### `DecisionRecommendation`

中文释义：决策建议
关键属性：
- `recommendation_id`：建议ID
- `recommendation_type`：建议类型
- `recommendation_text`：建议内容
- `confidence`：置信度
- `created_at`：创建时间

### Milestone

#### `RoomMilestone`

中文释义：机房里程碑
关键属性：
- `milestone_id`：里程碑ID
- `proposed_by`：提出方
- `due_time`：到期时间
- `milestone_status`：里程碑状态
- `target_pod_count`：目标PoD数量
- `completion_event_code`：完成事件编码
- `completion_event_name`：完成事件名称
- `priority`：优先级

#### `FloorMilestone`

中文释义：楼层里程碑
关键属性：
- `milestone_id`：里程碑ID
- `proposed_by`：提出方
- `due_time`：到期时间
- `milestone_status`：里程碑状态
- `required_room_count`：要求机房数量
- `completed_room_count`：已完成机房数量

## Link Types（关系）

- `Project HAS Building`：项目包含大楼
- `Building HAS Floor`：大楼包含楼层
- `Floor HAS Room`：楼层包含机房
- `Room HAS PoDPosition`：机房包含PoD落位
- `Project DELIVERS PoD`：项目交付PoD
- `Project HAS Crew`：项目包含施工队
- `Project HAS Shipment`：项目包含发货单
- `Project HAS RoomMilestone`：项目包含机房里程碑
- `Project HAS FloorMilestone`：项目包含楼层里程碑
- `RoomMilestone CONSTRAINS Room`：机房里程碑约束机房
- `FloorMilestone CONSTRAINS Floor`：楼层里程碑约束楼层
- `FloorMilestone AGGREGATES RoomMilestone`：楼层里程碑聚合机房里程碑
- `PoD ASSIGNED_TO Building`：PoD分配到大楼
- `PoD ASSIGNED_TO Floor`：PoD分配到楼层
- `PoD ASSIGNED_TO Room`：PoD分配到机房
- `PoD ASSIGNED_TO PoDPosition`：PoD分配到PoD落位
- `Shipment SHIPS PoD`：发货单发运PoD
- `PoD HAS ArrivalEvent`：PoD包含到货事件
- `ArrivalPlan APPLIES_TO PoD`：到货方案作用于PoD
- `PoD HAS ActivityInstance`：PoD包含活动实例
- `ActivityTemplate GENERATES ActivityInstance`：活动模板生成活动实例
- `ActivityTemplate USES SLAStandard`：活动模板使用标准SLA
- `ActivityInstance DEPENDS_ON ActivityInstance`：活动实例依赖活动实例
- `ActivityDependencyTemplate DEFINES ActivityInstance`：活动依赖模板定义活动实例
- `PoDSchedule APPLIES_TO PoD`：PoD排期作用于PoD
- `PoDSchedule CONTAINS ActivityInstance`：PoD排期包含活动实例
- `Crew EXECUTES WorkAssignment`：施工队执行施工分配
- `WorkAssignment ASSIGNS PoD`：施工分配分派PoD
- `WorkAssignment OCCURS_IN Room`：施工分配发生在机房
- `WorkAssignment OCCURS_AT PoDPosition`：施工分配发生于PoD落位
- `PlacementPlan APPLIES_TO PoD`：落位建议方案作用于PoD
- `PlacementPlan REFERENCES Building`：落位建议方案关联大楼
- `PlacementPlan REFERENCES Floor`：落位建议方案关联楼层
- `PlacementPlan REFERENCES Room`：落位建议方案关联机房
- `PlacementPlan REFERENCES PoDPosition`：落位建议方案关联PoD落位
- `ConstraintViolation REFERENCES PoD`：约束冲突关联PoD
- `ConstraintViolation REFERENCES RoomMilestone`：约束冲突关联机房里程碑
- `ConstraintViolation REFERENCES FloorMilestone`：约束冲突关联楼层里程碑
- `DecisionRecommendation REFERENCES ArrivalPlan`：决策建议关联到货方案
- `DecisionRecommendation REFERENCES PlacementPlan`：决策建议关联落位建议方案
- `DecisionRecommendation REFERENCES ConstraintViolation`：决策建议关联约束冲突
