
    const graphPayload = {"elements": [{"data": {"id": "object_type:Project", "label": "Project\n项目与目标层", "display_name": "Project", "type": "ObjectType", "attributes": {"group": "4.1 项目与目标层", "chinese_description": "项目。表示一个面向客户的交付项目，是所有对象的业务聚合根。", "semantic_definition": null, "key_properties": [{"name": "project_id", "description": "项目ID", "line_no": 69}, {"name": "project_name", "description": "项目名称", "line_no": 70}, {"name": "project_status", "description": "项目状态", "line_no": 71}, {"name": "product_type", "description": "产品形态", "line_no": 72}, {"name": "cooling_mode", "description": "冷却方式", "line_no": 73}, {"name": "project_scene", "description": "项目场景", "line_no": 74}, {"name": "planned_start_date", "description": "计划开始日期", "line_no": 75}], "status_values": [], "rules": [], "notes": [], "suggested_violation_types": [], "source_lines": {"start": 64, "end": 76}, "display_group": "项目与目标层", "key_property_lines": ["project_id：项目ID", "project_name：项目名称", "project_status：项目状态", "product_type：产品形态", "cooling_mode：冷却方式", "project_scene：项目场景", "planned_start_date：计划开始日期"], "status_value_lines": [], "rule_lines": [], "note_lines": []}, "color": "#f59e0b", "search_text": "project 项目与目标层 4.1 项目与目标层 {\"group\": \"4.1 项目与目标层\", \"chinese_description\": \"项目。表示一个面向客户的交付项目，是所有对象的业务聚合根。\", \"semantic_definition\": null, \"key_properties\": [{\"name\": \"project_id\", \"description\": \"项目id\", \"line_no\": 69}, {\"name\": \"project_name\", \"description\": \"项目名称\", \"line_no\": 70}, {\"name\": \"project_status\", \"description\": \"项目状态\", \"line_no\": 71}, {\"name\": \"product_type\", \"description\": \"产品形态\", \"line_no\": 72}, {\"name\": \"cooling_mode\", \"description\": \"冷却方式\", \"line_no\": 73}, {\"name\": \"project_scene\", \"description\": \"项目场景\", \"line_no\": 74}, {\"name\": \"planned_start_date\", \"description\": \"计划开始日期\", \"line_no\": 75}], \"status_values\": [], \"rules\": [], \"notes\": [], \"suggested_violation_types\": [], \"source_lines\": {\"start\": 64, \"end\": 76}, \"display_group\": \"项目与目标层\", \"key_property_lines\": [\"project_id：项目id\", \"project_name：项目名称\", \"project_status：项目状态\", \"product_type：产品形态\", \"cooling_mode：冷却方式\", \"project_scene：项目场景\", \"planned_start_date：计划开始日期\"], \"status_value_lines\": [], \"rule_lines\": [], \"note_lines\": []}"}, "position": {"x": 180.0, "y": 320.0}}, {"data": {"id": "object_type:RoomMilestone", "label": "RoomMilestone\n项目与目标层", "display_name": "RoomMilestone", "type": "ObjectType", "attributes": {"group": "4.1 项目与目标层", "chinese_description": "机房里程碑。表示机房级里程碑约束。", "semantic_definition": "", "key_properties": [{"name": "room_milestone_id", "description": "机房里程碑ID", "line_no": 85}, {"name": "project_id", "description": "所属项目ID", "line_no": 86}, {"name": "room_id", "description": "目标机房ID", "line_no": 87}, {"name": "proposed_by", "description": "提出方", "line_no": 88}, {"name": "target_pod_count", "description": "目标PoD数量", "line_no": 89}, {"name": "completion_event_code", "description": "完成事件编码", "line_no": 90}, {"name": "completion_event_name", "description": "完成事件名称", "line_no": 91}, {"name": "due_time", "description": "截止时间", "line_no": 92}, {"name": "priority", "description": "优先级", "line_no": 93}, {"name": "status", "description": "状态", "line_no": 94}], "status_values": [], "rules": [], "notes": ["`completion_event_name` 第一版固定为 `移交`"], "suggested_violation_types": [], "source_lines": {"start": 77, "end": 98}, "display_group": "项目与目标层", "key_property_lines": ["room_milestone_id：机房里程碑ID", "project_id：所属项目ID", "room_id：目标机房ID", "proposed_by：提出方", "target_pod_count：目标PoD数量", "completion_event_code：完成事件编码", "completion_event_name：完成事件名称", "due_time：截止时间", "priority：优先级", "status：状态"], "status_value_lines": [], "rule_lines": [], "note_lines": ["`completion_event_name` 第一版固定为 `移交`"]}, "color": "#f59e0b", "search_text": "roommilestone 项目与目标层 4.1 项目与目标层 {\"group\": \"4.1 项目与目标层\", \"chinese_description\": \"机房里程碑。表示机房级里程碑约束。\", \"semantic_definition\": \"\", \"key_properties\": [{\"name\": \"room_milestone_id\", \"description\": \"机房里程碑id\", \"line_no\": 85}, {\"name\": \"project_id\", \"description\": \"所属项目id\", \"line_no\": 86}, {\"name\": \"room_id\", \"description\": \"目标机房id\", \"line_no\": 87}, {\"name\": \"proposed_by\", \"description\": \"提出方\", \"line_no\": 88}, {\"name\": \"target_pod_count\", \"description\": \"目标pod数量\", \"line_no\": 89}, {\"name\": \"completion_event_code\", \"description\": \"完成事件编码\", \"line_no\": 90}, {\"name\": \"completion_event_name\", \"description\": \"完成事件名称\", \"line_no\": 91}, {\"name\": \"due_time\", \"description\": \"截止时间\", \"line_no\": 92}, {\"name\": \"priority\", \"description\": \"优先级\", \"line_no\": 93}, {\"name\": \"status\", \"description\": \"状态\", \"line_no\": 94}], \"status_values\": [], \"rules\": [], \"notes\": [\"`completion_event_name` 第一版固定为 `移交`\"], \"suggested_violation_types\": [], \"source_lines\": {\"start\": 77, \"end\": 98}, \"display_group\": \"项目与目标层\", \"key_property_lines\": [\"room_milestone_id：机房里程碑id\", \"project_id：所属项目id\", \"room_id：目标机房id\", \"proposed_by：提出方\", \"target_pod_count：目标pod数量\", \"completion_event_code：完成事件编码\", \"completion_event_name：完成事件名称\", \"due_time：截止时间\", \"priority：优先级\", \"status：状态\"], \"status_value_lines\": [], \"rule_lines\": [], \"note_lines\": [\"`completion_event_name` 第一版固定为 `移交`\"]}"}, "position": {"x": 180.0, "y": 170.0}}, {"data": {"id": "object_type:FloorMilestone", "label": "FloorMilestone\n项目与目标层", "display_name": "FloorMilestone", "type": "ObjectType", "attributes": {"group": "4.1 项目与目标层", "chinese_description": "楼层里程碑。表示楼层级里程碑约束。", "semantic_definition": "", "key_properties": [{"name": "floor_milestone_id", "description": "楼层里程碑ID", "line_no": 107}, {"name": "project_id", "description": "所属项目ID", "line_no": 108}, {"name": "floor_id", "description": "目标楼层ID", "line_no": 109}, {"name": "proposed_by", "description": "提出方", "line_no": 110}, {"name": "due_time", "description": "截止时间", "line_no": 111}, {"name": "required_room_count", "description": "要求完成的机房数量", "line_no": 112}, {"name": "completed_room_count", "description": "已完成的机房数量", "line_no": 113}, {"name": "status", "description": "状态", "line_no": 114}], "status_values": [], "rules": [], "notes": [], "suggested_violation_types": [], "source_lines": {"start": 99, "end": 115}, "display_group": "项目与目标层", "key_property_lines": ["floor_milestone_id：楼层里程碑ID", "project_id：所属项目ID", "floor_id：目标楼层ID", "proposed_by：提出方", "due_time：截止时间", "required_room_count：要求完成的机房数量", "completed_room_count：已完成的机房数量", "status：状态"], "status_value_lines": [], "rule_lines": [], "note_lines": []}, "color": "#f59e0b", "search_text": "floormilestone 项目与目标层 4.1 项目与目标层 {\"group\": \"4.1 项目与目标层\", \"chinese_description\": \"楼层里程碑。表示楼层级里程碑约束。\", \"semantic_definition\": \"\", \"key_properties\": [{\"name\": \"floor_milestone_id\", \"description\": \"楼层里程碑id\", \"line_no\": 107}, {\"name\": \"project_id\", \"description\": \"所属项目id\", \"line_no\": 108}, {\"name\": \"floor_id\", \"description\": \"目标楼层id\", \"line_no\": 109}, {\"name\": \"proposed_by\", \"description\": \"提出方\", \"line_no\": 110}, {\"name\": \"due_time\", \"description\": \"截止时间\", \"line_no\": 111}, {\"name\": \"required_room_count\", \"description\": \"要求完成的机房数量\", \"line_no\": 112}, {\"name\": \"completed_room_count\", \"description\": \"已完成的机房数量\", \"line_no\": 113}, {\"name\": \"status\", \"description\": \"状态\", \"line_no\": 114}], \"status_values\": [], \"rules\": [], \"notes\": [], \"suggested_violation_types\": [], \"source_lines\": {\"start\": 99, \"end\": 115}, \"display_group\": \"项目与目标层\", \"key_property_lines\": [\"floor_milestone_id：楼层里程碑id\", \"project_id：所属项目id\", \"floor_id：目标楼层id\", \"proposed_by：提出方\", \"due_time：截止时间\", \"required_room_count：要求完成的机房数量\", \"completed_room_count：已完成的机房数量\", \"status：状态\"], \"status_value_lines\": [], \"rule_lines\": [], \"note_lines\": []}"}, "position": {"x": 180.0, "y": 470.0}}, {"data": {"id": "object_type:Building", "label": "Building\n空间层", "display_name": "Building", "type": "ObjectType", "attributes": {"group": "4.2 空间层", "chinese_description": "大楼。", "semantic_definition": null, "key_properties": [{"name": "building_id", "description": "大楼ID", "line_no": 123}, {"name": "project_id", "description": "所属项目ID", "line_no": 124}, {"name": "building_name", "description": "大楼名称", "line_no": 125}], "status_values": [], "rules": [], "notes": [], "suggested_violation_types": [], "source_lines": {"start": 118, "end": 126}, "display_group": "空间层", "key_property_lines": ["building_id：大楼ID", "project_id：所属项目ID", "building_name：大楼名称"], "status_value_lines": [], "rule_lines": [], "note_lines": []}, "color": "#0ea5e9", "search_text": "building 空间层 4.2 空间层 {\"group\": \"4.2 空间层\", \"chinese_description\": \"大楼。\", \"semantic_definition\": null, \"key_properties\": [{\"name\": \"building_id\", \"description\": \"大楼id\", \"line_no\": 123}, {\"name\": \"project_id\", \"description\": \"所属项目id\", \"line_no\": 124}, {\"name\": \"building_name\", \"description\": \"大楼名称\", \"line_no\": 125}], \"status_values\": [], \"rules\": [], \"notes\": [], \"suggested_violation_types\": [], \"source_lines\": {\"start\": 118, \"end\": 126}, \"display_group\": \"空间层\", \"key_property_lines\": [\"building_id：大楼id\", \"project_id：所属项目id\", \"building_name：大楼名称\"], \"status_value_lines\": [], \"rule_lines\": [], \"note_lines\": []}"}, "position": {"x": 510.0, "y": 320.0}}, {"data": {"id": "object_type:Floor", "label": "Floor\n空间层", "display_name": "Floor", "type": "ObjectType", "attributes": {"group": "4.2 空间层", "chinese_description": "楼层。", "semantic_definition": null, "key_properties": [{"name": "floor_id", "description": "楼层ID", "line_no": 132}, {"name": "building_id", "description": "所属大楼ID", "line_no": 133}, {"name": "floor_no", "description": "楼层编号", "line_no": 134}, {"name": "install_sequence", "description": "安装顺序", "line_no": 135}], "status_values": [], "rules": [], "notes": [], "suggested_violation_types": [], "source_lines": {"start": 127, "end": 136}, "display_group": "空间层", "key_property_lines": ["floor_id：楼层ID", "building_id：所属大楼ID", "floor_no：楼层编号", "install_sequence：安装顺序"], "status_value_lines": [], "rule_lines": [], "note_lines": []}, "color": "#0ea5e9", "search_text": "floor 空间层 4.2 空间层 {\"group\": \"4.2 空间层\", \"chinese_description\": \"楼层。\", \"semantic_definition\": null, \"key_properties\": [{\"name\": \"floor_id\", \"description\": \"楼层id\", \"line_no\": 132}, {\"name\": \"building_id\", \"description\": \"所属大楼id\", \"line_no\": 133}, {\"name\": \"floor_no\", \"description\": \"楼层编号\", \"line_no\": 134}, {\"name\": \"install_sequence\", \"description\": \"安装顺序\", \"line_no\": 135}], \"status_values\": [], \"rules\": [], \"notes\": [], \"suggested_violation_types\": [], \"source_lines\": {\"start\": 127, \"end\": 136}, \"display_group\": \"空间层\", \"key_property_lines\": [\"floor_id：楼层id\", \"building_id：所属大楼id\", \"floor_no：楼层编号\", \"install_sequence：安装顺序\"], \"status_value_lines\": [], \"rule_lines\": [], \"note_lines\": []}"}, "position": {"x": 510.0, "y": 170.0}}, {"data": {"id": "object_type:Room", "label": "Room\n空间层", "display_name": "Room", "type": "ObjectType", "attributes": {"group": "4.2 空间层", "chinese_description": "机房。", "semantic_definition": null, "key_properties": [{"name": "room_id", "description": "机房ID", "line_no": 142}, {"name": "floor_id", "description": "所属楼层ID", "line_no": 143}, {"name": "room_type", "description": "机房类型", "line_no": 144}, {"name": "max_pod_capacity", "description": "最大PoD容量", "line_no": 145}, {"name": "required_handover_pod_count", "description": "要求移交的PoD数量", "line_no": 146}, {"name": "room_status", "description": "机房状态", "line_no": 147}], "status_values": [], "rules": [], "notes": [], "suggested_violation_types": [], "source_lines": {"start": 137, "end": 148}, "display_group": "空间层", "key_property_lines": ["room_id：机房ID", "floor_id：所属楼层ID", "room_type：机房类型", "max_pod_capacity：最大PoD容量", "required_handover_pod_count：要求移交的PoD数量", "room_status：机房状态"], "status_value_lines": [], "rule_lines": [], "note_lines": []}, "color": "#0ea5e9", "search_text": "room 空间层 4.2 空间层 {\"group\": \"4.2 空间层\", \"chinese_description\": \"机房。\", \"semantic_definition\": null, \"key_properties\": [{\"name\": \"room_id\", \"description\": \"机房id\", \"line_no\": 142}, {\"name\": \"floor_id\", \"description\": \"所属楼层id\", \"line_no\": 143}, {\"name\": \"room_type\", \"description\": \"机房类型\", \"line_no\": 144}, {\"name\": \"max_pod_capacity\", \"description\": \"最大pod容量\", \"line_no\": 145}, {\"name\": \"required_handover_pod_count\", \"description\": \"要求移交的pod数量\", \"line_no\": 146}, {\"name\": \"room_status\", \"description\": \"机房状态\", \"line_no\": 147}], \"status_values\": [], \"rules\": [], \"notes\": [], \"suggested_violation_types\": [], \"source_lines\": {\"start\": 137, \"end\": 148}, \"display_group\": \"空间层\", \"key_property_lines\": [\"room_id：机房id\", \"floor_id：所属楼层id\", \"room_type：机房类型\", \"max_pod_capacity：最大pod容量\", \"required_handover_pod_count：要求移交的pod数量\", \"room_status：机房状态\"], \"status_value_lines\": [], \"rule_lines\": [], \"note_lines\": []}"}, "position": {"x": 510.0, "y": 470.0}}, {"data": {"id": "object_type:PoDPosition", "label": "PoDPosition\n空间层", "display_name": "PoDPosition", "type": "ObjectType", "attributes": {"group": "4.2 空间层", "chinese_description": "PoD落位。表示机房内的 PoD 安装落位。", "semantic_definition": null, "key_properties": [{"name": "position_id", "description": "落位ID", "line_no": 154}, {"name": "room_id", "description": "所属机房ID", "line_no": 155}, {"name": "position_code", "description": "落位编码", "line_no": 156}, {"name": "position_status", "description": "落位状态", "line_no": 157}, {"name": "sequence_no", "description": "落位顺序号", "line_no": 158}], "status_values": [], "rules": [], "notes": ["`A机房-01位`", "`A机房-02位`"], "suggested_violation_types": [], "source_lines": {"start": 149, "end": 163}, "display_group": "空间层", "key_property_lines": ["position_id：落位ID", "room_id：所属机房ID", "position_code：落位编码", "position_status：落位状态", "sequence_no：落位顺序号"], "status_value_lines": [], "rule_lines": [], "note_lines": ["`A机房-01位`", "`A机房-02位`"]}, "color": "#0ea5e9", "search_text": "podposition 空间层 4.2 空间层 {\"group\": \"4.2 空间层\", \"chinese_description\": \"pod落位。表示机房内的 pod 安装落位。\", \"semantic_definition\": null, \"key_properties\": [{\"name\": \"position_id\", \"description\": \"落位id\", \"line_no\": 154}, {\"name\": \"room_id\", \"description\": \"所属机房id\", \"line_no\": 155}, {\"name\": \"position_code\", \"description\": \"落位编码\", \"line_no\": 156}, {\"name\": \"position_status\", \"description\": \"落位状态\", \"line_no\": 157}, {\"name\": \"sequence_no\", \"description\": \"落位顺序号\", \"line_no\": 158}], \"status_values\": [], \"rules\": [], \"notes\": [\"`a机房-01位`\", \"`a机房-02位`\"], \"suggested_violation_types\": [], \"source_lines\": {\"start\": 149, \"end\": 163}, \"display_group\": \"空间层\", \"key_property_lines\": [\"position_id：落位id\", \"room_id：所属机房id\", \"position_code：落位编码\", \"position_status：落位状态\", \"sequence_no：落位顺序号\"], \"status_value_lines\": [], \"rule_lines\": [], \"note_lines\": [\"`a机房-01位`\", \"`a机房-02位`\"]}"}, "position": {"x": 510.0, "y": 20.0}}, {"data": {"id": "object_type:PoD", "label": "PoD\n设备与物流层", "display_name": "PoD", "type": "ObjectType", "attributes": {"group": "4.3 设备与物流层", "chinese_description": "PoD交付单元。表示交付、到货、安装、移交的核心业务对象。", "semantic_definition": null, "key_properties": [{"name": "pod_id", "description": "PoD ID", "line_no": 171}, {"name": "project_id", "description": "所属项目ID", "line_no": 172}, {"name": "pod_code", "description": "PoD编码", "line_no": 173}, {"name": "pod_type", "description": "PoD类型", "line_no": 174}, {"name": "pod_status", "description": "PoD状态", "line_no": 175}, {"name": "building_id", "description": "所在大楼ID", "line_no": 176}, {"name": "floor_id", "description": "所在楼层ID", "line_no": 177}, {"name": "room_id", "description": "所在机房ID", "line_no": 178}, {"name": "position_id", "description": "所在落位ID", "line_no": 179}, {"name": "planned_arrival_time", "description": "计划到货时间", "line_no": 180}, {"name": "actual_arrival_time", "description": "实际到货时间", "line_no": 181}, {"name": "planned_install_start_time", "description": "计划安装开始时间", "line_no": 182}, {"name": "actual_install_start_time", "description": "实际安装开始时间", "line_no": 183}, {"name": "planned_handover_time", "description": "计划移交时间", "line_no": 184}, {"name": "actual_handover_time", "description": "实际移交时间", "line_no": 185}], "status_values": [{"name": "InTransit", "description": "在途", "line_no": 188}, {"name": "ArrivedWaitingInstall", "description": "已到货待安装", "line_no": 189}, {"name": "Installing", "description": "安装中", "line_no": 190}, {"name": "Installed", "description": "已安装", "line_no": 191}, {"name": "HandedOver", "description": "已移交", "line_no": 192}], "rules": [], "notes": [], "suggested_violation_types": [], "source_lines": {"start": 166, "end": 193}, "display_group": "设备与物流层", "key_property_lines": ["pod_id：PoD ID", "project_id：所属项目ID", "pod_code：PoD编码", "pod_type：PoD类型", "pod_status：PoD状态", "building_id：所在大楼ID", "floor_id：所在楼层ID", "room_id：所在机房ID", "position_id：所在落位ID", "planned_arrival_time：计划到货时间", "actual_arrival_time：实际到货时间", "planned_install_start_time：计划安装开始时间", "actual_install_start_time：实际安装开始时间", "planned_handover_time：计划移交时间", "actual_handover_time：实际移交时间"], "status_value_lines": ["InTransit：在途", "ArrivedWaitingInstall：已到货待安装", "Installing：安装中", "Installed：已安装", "HandedOver：已移交"], "rule_lines": [], "note_lines": []}, "color": "#14b8a6", "search_text": "pod 设备与物流层 4.3 设备与物流层 {\"group\": \"4.3 设备与物流层\", \"chinese_description\": \"pod交付单元。表示交付、到货、安装、移交的核心业务对象。\", \"semantic_definition\": null, \"key_properties\": [{\"name\": \"pod_id\", \"description\": \"pod id\", \"line_no\": 171}, {\"name\": \"project_id\", \"description\": \"所属项目id\", \"line_no\": 172}, {\"name\": \"pod_code\", \"description\": \"pod编码\", \"line_no\": 173}, {\"name\": \"pod_type\", \"description\": \"pod类型\", \"line_no\": 174}, {\"name\": \"pod_status\", \"description\": \"pod状态\", \"line_no\": 175}, {\"name\": \"building_id\", \"description\": \"所在大楼id\", \"line_no\": 176}, {\"name\": \"floor_id\", \"description\": \"所在楼层id\", \"line_no\": 177}, {\"name\": \"room_id\", \"description\": \"所在机房id\", \"line_no\": 178}, {\"name\": \"position_id\", \"description\": \"所在落位id\", \"line_no\": 179}, {\"name\": \"planned_arrival_time\", \"description\": \"计划到货时间\", \"line_no\": 180}, {\"name\": \"actual_arrival_time\", \"description\": \"实际到货时间\", \"line_no\": 181}, {\"name\": \"planned_install_start_time\", \"description\": \"计划安装开始时间\", \"line_no\": 182}, {\"name\": \"actual_install_start_time\", \"description\": \"实际安装开始时间\", \"line_no\": 183}, {\"name\": \"planned_handover_time\", \"description\": \"计划移交时间\", \"line_no\": 184}, {\"name\": \"actual_handover_time\", \"description\": \"实际移交时间\", \"line_no\": 185}], \"status_values\": [{\"name\": \"intransit\", \"description\": \"在途\", \"line_no\": 188}, {\"name\": \"arrivedwaitinginstall\", \"description\": \"已到货待安装\", \"line_no\": 189}, {\"name\": \"installing\", \"description\": \"安装中\", \"line_no\": 190}, {\"name\": \"installed\", \"description\": \"已安装\", \"line_no\": 191}, {\"name\": \"handedover\", \"description\": \"已移交\", \"line_no\": 192}], \"rules\": [], \"notes\": [], \"suggested_violation_types\": [], \"source_lines\": {\"start\": 166, \"end\": 193}, \"display_group\": \"设备与物流层\", \"key_property_lines\": [\"pod_id：pod id\", \"project_id：所属项目id\", \"pod_code：pod编码\", \"pod_type：pod类型\", \"pod_status：pod状态\", \"building_id：所在大楼id\", \"floor_id：所在楼层id\", \"room_id：所在机房id\", \"position_id：所在落位id\", \"planned_arrival_time：计划到货时间\", \"actual_arrival_time：实际到货时间\", \"planned_install_start_time：计划安装开始时间\", \"actual_install_start_time：实际安装开始时间\", \"planned_handover_time：计划移交时间\", \"actual_handover_time：实际移交时间\"], \"status_value_lines\": [\"intransit：在途\", \"arrivedwaitinginstall：已到货待安装\", \"installing：安装中\", \"installed：已安装\", \"handedover：已移交\"], \"rule_lines\": [], \"note_lines\": []}"}, "position": {"x": 840.0, "y": 320.0}}, {"data": {"id": "object_type:Shipment", "label": "Shipment\n设备与物流层", "display_name": "Shipment", "type": "ObjectType", "attributes": {"group": "4.3 设备与物流层", "chinese_description": "发货单。表示一次 PoD 发货安排。", "semantic_definition": null, "key_properties": [{"name": "shipment_id", "description": "发货ID", "line_no": 199}, {"name": "project_id", "description": "所属项目ID", "line_no": 200}, {"name": "shipment_no", "description": "发货单号", "line_no": 201}, {"name": "pod_id", "description": "对应PoD ID", "line_no": 202}, {"name": "planned_ship_time", "description": "计划发货时间", "line_no": 203}, {"name": "planned_arrival_time", "description": "计划到货时间", "line_no": 204}, {"name": "actual_arrival_time", "description": "实际到货时间", "line_no": 205}, {"name": "shipment_status", "description": "发货状态", "line_no": 206}], "status_values": [], "rules": [], "notes": [], "suggested_violation_types": [], "source_lines": {"start": 194, "end": 207}, "display_group": "设备与物流层", "key_property_lines": ["shipment_id：发货ID", "project_id：所属项目ID", "shipment_no：发货单号", "pod_id：对应PoD ID", "planned_ship_time：计划发货时间", "planned_arrival_time：计划到货时间", "actual_arrival_time：实际到货时间", "shipment_status：发货状态"], "status_value_lines": [], "rule_lines": [], "note_lines": []}, "color": "#14b8a6", "search_text": "shipment 设备与物流层 4.3 设备与物流层 {\"group\": \"4.3 设备与物流层\", \"chinese_description\": \"发货单。表示一次 pod 发货安排。\", \"semantic_definition\": null, \"key_properties\": [{\"name\": \"shipment_id\", \"description\": \"发货id\", \"line_no\": 199}, {\"name\": \"project_id\", \"description\": \"所属项目id\", \"line_no\": 200}, {\"name\": \"shipment_no\", \"description\": \"发货单号\", \"line_no\": 201}, {\"name\": \"pod_id\", \"description\": \"对应pod id\", \"line_no\": 202}, {\"name\": \"planned_ship_time\", \"description\": \"计划发货时间\", \"line_no\": 203}, {\"name\": \"planned_arrival_time\", \"description\": \"计划到货时间\", \"line_no\": 204}, {\"name\": \"actual_arrival_time\", \"description\": \"实际到货时间\", \"line_no\": 205}, {\"name\": \"shipment_status\", \"description\": \"发货状态\", \"line_no\": 206}], \"status_values\": [], \"rules\": [], \"notes\": [], \"suggested_violation_types\": [], \"source_lines\": {\"start\": 194, \"end\": 207}, \"display_group\": \"设备与物流层\", \"key_property_lines\": [\"shipment_id：发货id\", \"project_id：所属项目id\", \"shipment_no：发货单号\", \"pod_id：对应pod id\", \"planned_ship_time：计划发货时间\", \"planned_arrival_time：计划到货时间\", \"actual_arrival_time：实际到货时间\", \"shipment_status：发货状态\"], \"status_value_lines\": [], \"rule_lines\": [], \"note_lines\": []}"}, "position": {"x": 840.0, "y": 20.0}}, {"data": {"id": "object_type:ArrivalEvent", "label": "ArrivalEvent\n设备与物流层", "display_name": "ArrivalEvent", "type": "ObjectType", "attributes": {"group": "4.3 设备与物流层", "chinese_description": "到货事件。表示一次 PoD 到货事实。", "semantic_definition": null, "key_properties": [{"name": "arrival_event_id", "description": "到货事件ID", "line_no": 213}, {"name": "pod_id", "description": "对应PoD ID", "line_no": 214}, {"name": "arrival_time", "description": "到货时间", "line_no": 215}, {"name": "arrival_status", "description": "到货状态", "line_no": 216}, {"name": "receiving_location", "description": "收货地点", "line_no": 217}, {"name": "confirmed_by", "description": "确认人", "line_no": 218}], "status_values": [], "rules": [], "notes": [], "suggested_violation_types": [], "source_lines": {"start": 208, "end": 219}, "display_group": "设备与物流层", "key_property_lines": ["arrival_event_id：到货事件ID", "pod_id：对应PoD ID", "arrival_time：到货时间", "arrival_status：到货状态", "receiving_location：收货地点", "confirmed_by：确认人"], "status_value_lines": [], "rule_lines": [], "note_lines": []}, "color": "#14b8a6", "search_text": "arrivalevent 设备与物流层 4.3 设备与物流层 {\"group\": \"4.3 设备与物流层\", \"chinese_description\": \"到货事件。表示一次 pod 到货事实。\", \"semantic_definition\": null, \"key_properties\": [{\"name\": \"arrival_event_id\", \"description\": \"到货事件id\", \"line_no\": 213}, {\"name\": \"pod_id\", \"description\": \"对应pod id\", \"line_no\": 214}, {\"name\": \"arrival_time\", \"description\": \"到货时间\", \"line_no\": 215}, {\"name\": \"arrival_status\", \"description\": \"到货状态\", \"line_no\": 216}, {\"name\": \"receiving_location\", \"description\": \"收货地点\", \"line_no\": 217}, {\"name\": \"confirmed_by\", \"description\": \"确认人\", \"line_no\": 218}], \"status_values\": [], \"rules\": [], \"notes\": [], \"suggested_violation_types\": [], \"source_lines\": {\"start\": 208, \"end\": 219}, \"display_group\": \"设备与物流层\", \"key_property_lines\": [\"arrival_event_id：到货事件id\", \"pod_id：对应pod id\", \"arrival_time：到货时间\", \"arrival_status：到货状态\", \"receiving_location：收货地点\", \"confirmed_by：确认人\"], \"status_value_lines\": [], \"rule_lines\": [], \"note_lines\": []}"}, "position": {"x": 840.0, "y": 470.0}}, {"data": {"id": "object_type:ArrivalPlan", "label": "ArrivalPlan\n设备与物流层", "display_name": "ArrivalPlan", "type": "ObjectType", "attributes": {"group": "4.3 设备与物流层", "chinese_description": "到货建议方案。表示系统对到货时间的建议方案。", "semantic_definition": null, "key_properties": [{"name": "arrival_plan_id", "description": "到货方案ID", "line_no": 225}, {"name": "project_id", "description": "所属项目ID", "line_no": 226}, {"name": "pod_id", "description": "对应PoD ID", "line_no": 227}, {"name": "recommended_arrival_time", "description": "建议到货时间", "line_no": 228}, {"name": "latest_safe_arrival_time", "description": "最晚安全到货时间", "line_no": 229}, {"name": "earliest_useful_arrival_time", "description": "最早有意义到货时间", "line_no": 230}, {"name": "backlog_risk_level", "description": "积压风险等级", "line_no": 231}, {"name": "plan_status", "description": "方案状态", "line_no": 232}], "status_values": [], "rules": [], "notes": [], "suggested_violation_types": [], "source_lines": {"start": 220, "end": 233}, "display_group": "设备与物流层", "key_property_lines": ["arrival_plan_id：到货方案ID", "project_id：所属项目ID", "pod_id：对应PoD ID", "recommended_arrival_time：建议到货时间", "latest_safe_arrival_time：最晚安全到货时间", "earliest_useful_arrival_time：最早有意义到货时间", "backlog_risk_level：积压风险等级", "plan_status：方案状态"], "status_value_lines": [], "rule_lines": [], "note_lines": []}, "color": "#14b8a6", "search_text": "arrivalplan 设备与物流层 4.3 设备与物流层 {\"group\": \"4.3 设备与物流层\", \"chinese_description\": \"到货建议方案。表示系统对到货时间的建议方案。\", \"semantic_definition\": null, \"key_properties\": [{\"name\": \"arrival_plan_id\", \"description\": \"到货方案id\", \"line_no\": 225}, {\"name\": \"project_id\", \"description\": \"所属项目id\", \"line_no\": 226}, {\"name\": \"pod_id\", \"description\": \"对应pod id\", \"line_no\": 227}, {\"name\": \"recommended_arrival_time\", \"description\": \"建议到货时间\", \"line_no\": 228}, {\"name\": \"latest_safe_arrival_time\", \"description\": \"最晚安全到货时间\", \"line_no\": 229}, {\"name\": \"earliest_useful_arrival_time\", \"description\": \"最早有意义到货时间\", \"line_no\": 230}, {\"name\": \"backlog_risk_level\", \"description\": \"积压风险等级\", \"line_no\": 231}, {\"name\": \"plan_status\", \"description\": \"方案状态\", \"line_no\": 232}], \"status_values\": [], \"rules\": [], \"notes\": [], \"suggested_violation_types\": [], \"source_lines\": {\"start\": 220, \"end\": 233}, \"display_group\": \"设备与物流层\", \"key_property_lines\": [\"arrival_plan_id：到货方案id\", \"project_id：所属项目id\", \"pod_id：对应pod id\", \"recommended_arrival_time：建议到货时间\", \"latest_safe_arrival_time：最晚安全到货时间\", \"earliest_useful_arrival_time：最早有意义到货时间\", \"backlog_risk_level：积压风险等级\", \"plan_status：方案状态\"], \"status_value_lines\": [], \"rule_lines\": [], \"note_lines\": []}"}, "position": {"x": 840.0, "y": 170.0}}, {"data": {"id": "object_type:ActivityTemplate", "label": "ActivityTemplate\n活动与排期层", "display_name": "ActivityTemplate", "type": "ObjectType", "attributes": {"group": "4.4 活动与排期层", "chinese_description": "活动模板。表示标准二级活动模板。", "semantic_definition": null, "key_properties": [{"name": "template_id", "description": "活动模板ID", "line_no": 241}, {"name": "l1_code", "description": "一级活动编码", "line_no": 242}, {"name": "l1_name", "description": "一级活动名称", "line_no": 243}, {"name": "l2_code", "description": "二级活动编码", "line_no": 244}, {"name": "l2_name", "description": "二级活动名称", "line_no": 245}, {"name": "activity_category", "description": "活动分类", "line_no": 246}, {"name": "completion_flag", "description": "是否为完成节点标记", "line_no": 247}, {"name": "applies_to_product_type", "description": "适用产品形态", "line_no": 248}, {"name": "applies_to_cooling_mode", "description": "适用冷却方式", "line_no": 249}, {"name": "applies_to_project_scene", "description": "适用项目场景", "line_no": 250}], "status_values": [], "rules": [], "notes": ["一级活动只作为分类字段保留", "真正进行实例化的是二级活动", "`12.4 移交` 在模板中应标记为关键完成节点"], "suggested_violation_types": [], "source_lines": {"start": 236, "end": 256}, "display_group": "活动与排期层", "key_property_lines": ["template_id：活动模板ID", "l1_code：一级活动编码", "l1_name：一级活动名称", "l2_code：二级活动编码", "l2_name：二级活动名称", "activity_category：活动分类", "completion_flag：是否为完成节点标记", "applies_to_product_type：适用产品形态", "applies_to_cooling_mode：适用冷却方式", "applies_to_project_scene：适用项目场景"], "status_value_lines": [], "rule_lines": [], "note_lines": ["一级活动只作为分类字段保留", "真正进行实例化的是二级活动", "`12.4 移交` 在模板中应标记为关键完成节点"]}, "color": "#6366f1", "search_text": "activitytemplate 活动与排期层 4.4 活动与排期层 {\"group\": \"4.4 活动与排期层\", \"chinese_description\": \"活动模板。表示标准二级活动模板。\", \"semantic_definition\": null, \"key_properties\": [{\"name\": \"template_id\", \"description\": \"活动模板id\", \"line_no\": 241}, {\"name\": \"l1_code\", \"description\": \"一级活动编码\", \"line_no\": 242}, {\"name\": \"l1_name\", \"description\": \"一级活动名称\", \"line_no\": 243}, {\"name\": \"l2_code\", \"description\": \"二级活动编码\", \"line_no\": 244}, {\"name\": \"l2_name\", \"description\": \"二级活动名称\", \"line_no\": 245}, {\"name\": \"activity_category\", \"description\": \"活动分类\", \"line_no\": 246}, {\"name\": \"completion_flag\", \"description\": \"是否为完成节点标记\", \"line_no\": 247}, {\"name\": \"applies_to_product_type\", \"description\": \"适用产品形态\", \"line_no\": 248}, {\"name\": \"applies_to_cooling_mode\", \"description\": \"适用冷却方式\", \"line_no\": 249}, {\"name\": \"applies_to_project_scene\", \"description\": \"适用项目场景\", \"line_no\": 250}], \"status_values\": [], \"rules\": [], \"notes\": [\"一级活动只作为分类字段保留\", \"真正进行实例化的是二级活动\", \"`12.4 移交` 在模板中应标记为关键完成节点\"], \"suggested_violation_types\": [], \"source_lines\": {\"start\": 236, \"end\": 256}, \"display_group\": \"活动与排期层\", \"key_property_lines\": [\"template_id：活动模板id\", \"l1_code：一级活动编码\", \"l1_name：一级活动名称\", \"l2_code：二级活动编码\", \"l2_name：二级活动名称\", \"activity_category：活动分类\", \"completion_flag：是否为完成节点标记\", \"applies_to_product_type：适用产品形态\", \"applies_to_cooling_mode：适用冷却方式\", \"applies_to_project_scene：适用项目场景\"], \"status_value_lines\": [], \"rule_lines\": [], \"note_lines\": [\"一级活动只作为分类字段保留\", \"真正进行实例化的是二级活动\", \"`12.4 移交` 在模板中应标记为关键完成节点\"]}"}, "position": {"x": 1170.0, "y": 470.0}}, {"data": {"id": "object_type:ActivityDependencyTemplate", "label": "ActivityDependencyTemplate\n活动与排期层", "display_name": "ActivityDependencyTemplate", "type": "ObjectType", "attributes": {"group": "4.4 活动与排期层", "chinese_description": "活动依赖模板。表示标准活动依赖模板。", "semantic_definition": null, "key_properties": [{"name": "dependency_template_id", "description": "依赖模板ID", "line_no": 262}, {"name": "predecessor_template_id", "description": "前置活动模板ID", "line_no": 263}, {"name": "successor_template_id", "description": "后继活动模板ID", "line_no": 264}, {"name": "dependency_type", "description": "依赖类型", "line_no": 265}], "status_values": [], "rules": [], "notes": [], "suggested_violation_types": [], "source_lines": {"start": 257, "end": 266}, "display_group": "活动与排期层", "key_property_lines": ["dependency_template_id：依赖模板ID", "predecessor_template_id：前置活动模板ID", "successor_template_id：后继活动模板ID", "dependency_type：依赖类型"], "status_value_lines": [], "rule_lines": [], "note_lines": []}, "color": "#6366f1", "search_text": "activitydependencytemplate 活动与排期层 4.4 活动与排期层 {\"group\": \"4.4 活动与排期层\", \"chinese_description\": \"活动依赖模板。表示标准活动依赖模板。\", \"semantic_definition\": null, \"key_properties\": [{\"name\": \"dependency_template_id\", \"description\": \"依赖模板id\", \"line_no\": 262}, {\"name\": \"predecessor_template_id\", \"description\": \"前置活动模板id\", \"line_no\": 263}, {\"name\": \"successor_template_id\", \"description\": \"后继活动模板id\", \"line_no\": 264}, {\"name\": \"dependency_type\", \"description\": \"依赖类型\", \"line_no\": 265}], \"status_values\": [], \"rules\": [], \"notes\": [], \"suggested_violation_types\": [], \"source_lines\": {\"start\": 257, \"end\": 266}, \"display_group\": \"活动与排期层\", \"key_property_lines\": [\"dependency_template_id：依赖模板id\", \"predecessor_template_id：前置活动模板id\", \"successor_template_id：后继活动模板id\", \"dependency_type：依赖类型\"], \"status_value_lines\": [], \"rule_lines\": [], \"note_lines\": []}"}, "position": {"x": 1170.0, "y": 170.0}}, {"data": {"id": "object_type:SLAStandard", "label": "SLAStandard\n活动与排期层", "display_name": "SLAStandard", "type": "ObjectType", "attributes": {"group": "4.4 活动与排期层", "chinese_description": "标准SLA。表示标准活动工期。", "semantic_definition": null, "key_properties": [{"name": "sla_id", "description": "SLA ID", "line_no": 272}, {"name": "template_id", "description": "活动模板ID", "line_no": 273}, {"name": "standard_duration", "description": "标准时长", "line_no": 274}, {"name": "duration_unit", "description": "时长单位", "line_no": 275}, {"name": "crew_capacity_assumption", "description": "施工队能力假设", "line_no": 276}, {"name": "scenario_tag", "description": "场景标签", "line_no": 277}], "status_values": [], "rules": [], "notes": [], "suggested_violation_types": [], "source_lines": {"start": 267, "end": 278}, "display_group": "活动与排期层", "key_property_lines": ["sla_id：SLA ID", "template_id：活动模板ID", "standard_duration：标准时长", "duration_unit：时长单位", "crew_capacity_assumption：施工队能力假设", "scenario_tag：场景标签"], "status_value_lines": [], "rule_lines": [], "note_lines": []}, "color": "#6366f1", "search_text": "slastandard 活动与排期层 4.4 活动与排期层 {\"group\": \"4.4 活动与排期层\", \"chinese_description\": \"标准sla。表示标准活动工期。\", \"semantic_definition\": null, \"key_properties\": [{\"name\": \"sla_id\", \"description\": \"sla id\", \"line_no\": 272}, {\"name\": \"template_id\", \"description\": \"活动模板id\", \"line_no\": 273}, {\"name\": \"standard_duration\", \"description\": \"标准时长\", \"line_no\": 274}, {\"name\": \"duration_unit\", \"description\": \"时长单位\", \"line_no\": 275}, {\"name\": \"crew_capacity_assumption\", \"description\": \"施工队能力假设\", \"line_no\": 276}, {\"name\": \"scenario_tag\", \"description\": \"场景标签\", \"line_no\": 277}], \"status_values\": [], \"rules\": [], \"notes\": [], \"suggested_violation_types\": [], \"source_lines\": {\"start\": 267, \"end\": 278}, \"display_group\": \"活动与排期层\", \"key_property_lines\": [\"sla_id：sla id\", \"template_id：活动模板id\", \"standard_duration：标准时长\", \"duration_unit：时长单位\", \"crew_capacity_assumption：施工队能力假设\", \"scenario_tag：场景标签\"], \"status_value_lines\": [], \"rule_lines\": [], \"note_lines\": []}"}, "position": {"x": 1170.0, "y": 620.0}}, {"data": {"id": "object_type:ActivityInstance", "label": "ActivityInstance\n活动与排期层", "display_name": "ActivityInstance", "type": "ObjectType", "attributes": {"group": "4.4 活动与排期层", "chinese_description": "活动实例。表示某个 PoD 在项目中的实际二级活动实例。", "semantic_definition": null, "key_properties": [{"name": "activity_id", "description": "活动实例ID", "line_no": 284}, {"name": "project_id", "description": "所属项目ID", "line_no": 285}, {"name": "pod_id", "description": "所属PoD ID", "line_no": 286}, {"name": "template_id", "description": "活动模板ID", "line_no": 287}, {"name": "l1_name", "description": "一级活动名称", "line_no": 288}, {"name": "l2_name", "description": "二级活动名称", "line_no": 289}, {"name": "activity_status", "description": "活动状态", "line_no": 290}, {"name": "planned_start_time", "description": "计划开始时间", "line_no": 291}, {"name": "planned_finish_time", "description": "计划结束时间", "line_no": 292}, {"name": "latest_start_time", "description": "最晚开始时间", "line_no": 293}, {"name": "latest_finish_time", "description": "最晚结束时间", "line_no": 294}, {"name": "actual_start_time", "description": "实际开始时间", "line_no": 295}, {"name": "actual_finish_time", "description": "实际结束时间", "line_no": 296}, {"name": "is_milestone_anchor", "description": "是否为里程碑锚点", "line_no": 297}], "status_values": [], "rules": [], "notes": [], "suggested_violation_types": [], "source_lines": {"start": 279, "end": 298}, "display_group": "活动与排期层", "key_property_lines": ["activity_id：活动实例ID", "project_id：所属项目ID", "pod_id：所属PoD ID", "template_id：活动模板ID", "l1_name：一级活动名称", "l2_name：二级活动名称", "activity_status：活动状态", "planned_start_time：计划开始时间", "planned_finish_time：计划结束时间", "latest_start_time：最晚开始时间", "latest_finish_time：最晚结束时间", "actual_start_time：实际开始时间", "actual_finish_time：实际结束时间", "is_milestone_anchor：是否为里程碑锚点"], "status_value_lines": [], "rule_lines": [], "note_lines": []}, "color": "#6366f1", "search_text": "activityinstance 活动与排期层 4.4 活动与排期层 {\"group\": \"4.4 活动与排期层\", \"chinese_description\": \"活动实例。表示某个 pod 在项目中的实际二级活动实例。\", \"semantic_definition\": null, \"key_properties\": [{\"name\": \"activity_id\", \"description\": \"活动实例id\", \"line_no\": 284}, {\"name\": \"project_id\", \"description\": \"所属项目id\", \"line_no\": 285}, {\"name\": \"pod_id\", \"description\": \"所属pod id\", \"line_no\": 286}, {\"name\": \"template_id\", \"description\": \"活动模板id\", \"line_no\": 287}, {\"name\": \"l1_name\", \"description\": \"一级活动名称\", \"line_no\": 288}, {\"name\": \"l2_name\", \"description\": \"二级活动名称\", \"line_no\": 289}, {\"name\": \"activity_status\", \"description\": \"活动状态\", \"line_no\": 290}, {\"name\": \"planned_start_time\", \"description\": \"计划开始时间\", \"line_no\": 291}, {\"name\": \"planned_finish_time\", \"description\": \"计划结束时间\", \"line_no\": 292}, {\"name\": \"latest_start_time\", \"description\": \"最晚开始时间\", \"line_no\": 293}, {\"name\": \"latest_finish_time\", \"description\": \"最晚结束时间\", \"line_no\": 294}, {\"name\": \"actual_start_time\", \"description\": \"实际开始时间\", \"line_no\": 295}, {\"name\": \"actual_finish_time\", \"description\": \"实际结束时间\", \"line_no\": 296}, {\"name\": \"is_milestone_anchor\", \"description\": \"是否为里程碑锚点\", \"line_no\": 297}], \"status_values\": [], \"rules\": [], \"notes\": [], \"suggested_violation_types\": [], \"source_lines\": {\"start\": 279, \"end\": 298}, \"display_group\": \"活动与排期层\", \"key_property_lines\": [\"activity_id：活动实例id\", \"project_id：所属项目id\", \"pod_id：所属pod id\", \"template_id：活动模板id\", \"l1_name：一级活动名称\", \"l2_name：二级活动名称\", \"activity_status：活动状态\", \"planned_start_time：计划开始时间\", \"planned_finish_time：计划结束时间\", \"latest_start_time：最晚开始时间\", \"latest_finish_time：最晚结束时间\", \"actual_start_time：实际开始时间\", \"actual_finish_time：实际结束时间\", \"is_milestone_anchor：是否为里程碑锚点\"], \"status_value_lines\": [], \"rule_lines\": [], \"note_lines\": []}"}, "position": {"x": 1170.0, "y": 320.0}}, {"data": {"id": "object_type:PoDSchedule", "label": "PoDSchedule\n活动与排期层", "display_name": "PoDSchedule", "type": "ObjectType", "attributes": {"group": "4.4 活动与排期层", "chinese_description": "PoD排期。表示某个 PoD 的活动排期结果。", "semantic_definition": null, "key_properties": [{"name": "pod_schedule_id", "description": "PoD排期ID", "line_no": 304}, {"name": "project_id", "description": "所属项目ID", "line_no": 305}, {"name": "pod_id", "description": "对应PoD ID", "line_no": 306}, {"name": "anchor_activity_id", "description": "锚点活动ID", "line_no": 307}, {"name": "schedule_type", "description": "排期类型", "line_no": 308}, {"name": "generated_at", "description": "生成时间", "line_no": 309}, {"name": "is_feasible", "description": "是否可执行", "line_no": 310}], "status_values": [], "rules": [], "notes": [], "suggested_violation_types": [], "source_lines": {"start": 299, "end": 311}, "display_group": "活动与排期层", "key_property_lines": ["pod_schedule_id：PoD排期ID", "project_id：所属项目ID", "pod_id：对应PoD ID", "anchor_activity_id：锚点活动ID", "schedule_type：排期类型", "generated_at：生成时间", "is_feasible：是否可执行"], "status_value_lines": [], "rule_lines": [], "note_lines": []}, "color": "#6366f1", "search_text": "podschedule 活动与排期层 4.4 活动与排期层 {\"group\": \"4.4 活动与排期层\", \"chinese_description\": \"pod排期。表示某个 pod 的活动排期结果。\", \"semantic_definition\": null, \"key_properties\": [{\"name\": \"pod_schedule_id\", \"description\": \"pod排期id\", \"line_no\": 304}, {\"name\": \"project_id\", \"description\": \"所属项目id\", \"line_no\": 305}, {\"name\": \"pod_id\", \"description\": \"对应pod id\", \"line_no\": 306}, {\"name\": \"anchor_activity_id\", \"description\": \"锚点活动id\", \"line_no\": 307}, {\"name\": \"schedule_type\", \"description\": \"排期类型\", \"line_no\": 308}, {\"name\": \"generated_at\", \"description\": \"生成时间\", \"line_no\": 309}, {\"name\": \"is_feasible\", \"description\": \"是否可执行\", \"line_no\": 310}], \"status_values\": [], \"rules\": [], \"notes\": [], \"suggested_violation_types\": [], \"source_lines\": {\"start\": 299, \"end\": 311}, \"display_group\": \"活动与排期层\", \"key_property_lines\": [\"pod_schedule_id：pod排期id\", \"project_id：所属项目id\", \"pod_id：对应pod id\", \"anchor_activity_id：锚点活动id\", \"schedule_type：排期类型\", \"generated_at：生成时间\", \"is_feasible：是否可执行\"], \"status_value_lines\": [], \"rule_lines\": [], \"note_lines\": []}"}, "position": {"x": 1170.0, "y": 20.0}}, {"data": {"id": "object_type:Crew", "label": "Crew\n施工执行层", "display_name": "Crew", "type": "ObjectType", "attributes": {"group": "4.5 施工执行层", "chinese_description": "施工队。", "semantic_definition": null, "key_properties": [{"name": "crew_id", "description": "施工队ID", "line_no": 319}, {"name": "project_id", "description": "所属项目ID", "line_no": 320}, {"name": "crew_status", "description": "施工队状态", "line_no": 321}, {"name": "daily_pod_capacity", "description": "每日PoD安装能力", "line_no": 322}, {"name": "parallel_limit", "description": "并行上限", "line_no": 323}], "status_values": [], "rules": ["每个施工队同一时间只能安装一个 PoD", "每个施工队每天可安装的 PoD 数量采用固定规则"], "notes": [], "suggested_violation_types": [], "source_lines": {"start": 314, "end": 328}, "display_group": "施工执行层", "key_property_lines": ["crew_id：施工队ID", "project_id：所属项目ID", "crew_status：施工队状态", "daily_pod_capacity：每日PoD安装能力", "parallel_limit：并行上限"], "status_value_lines": [], "rule_lines": ["每个施工队同一时间只能安装一个 PoD", "每个施工队每天可安装的 PoD 数量采用固定规则"], "note_lines": []}, "color": "#10b981", "search_text": "crew 施工执行层 4.5 施工执行层 {\"group\": \"4.5 施工执行层\", \"chinese_description\": \"施工队。\", \"semantic_definition\": null, \"key_properties\": [{\"name\": \"crew_id\", \"description\": \"施工队id\", \"line_no\": 319}, {\"name\": \"project_id\", \"description\": \"所属项目id\", \"line_no\": 320}, {\"name\": \"crew_status\", \"description\": \"施工队状态\", \"line_no\": 321}, {\"name\": \"daily_pod_capacity\", \"description\": \"每日pod安装能力\", \"line_no\": 322}, {\"name\": \"parallel_limit\", \"description\": \"并行上限\", \"line_no\": 323}], \"status_values\": [], \"rules\": [\"每个施工队同一时间只能安装一个 pod\", \"每个施工队每天可安装的 pod 数量采用固定规则\"], \"notes\": [], \"suggested_violation_types\": [], \"source_lines\": {\"start\": 314, \"end\": 328}, \"display_group\": \"施工执行层\", \"key_property_lines\": [\"crew_id：施工队id\", \"project_id：所属项目id\", \"crew_status：施工队状态\", \"daily_pod_capacity：每日pod安装能力\", \"parallel_limit：并行上限\"], \"status_value_lines\": [], \"rule_lines\": [\"每个施工队同一时间只能安装一个 pod\", \"每个施工队每天可安装的 pod 数量采用固定规则\"], \"note_lines\": []}"}, "position": {"x": 1500.0, "y": 170.0}}, {"data": {"id": "object_type:WorkAssignment", "label": "WorkAssignment\n施工执行层", "display_name": "WorkAssignment", "type": "ObjectType", "attributes": {"group": "4.5 施工执行层", "chinese_description": "施工分配。表示某个施工队在某个时间窗内被分配到哪个机房、安装哪个 PoD。", "semantic_definition": null, "key_properties": [{"name": "assignment_id", "description": "分配ID", "line_no": 334}, {"name": "project_id", "description": "所属项目ID", "line_no": 335}, {"name": "crew_id", "description": "施工队ID", "line_no": 336}, {"name": "pod_id", "description": "PoD ID", "line_no": 337}, {"name": "room_id", "description": "机房ID", "line_no": 338}, {"name": "position_id", "description": "落位ID", "line_no": 339}, {"name": "assignment_date", "description": "分配日期", "line_no": 340}, {"name": "start_time", "description": "开始时间", "line_no": 341}, {"name": "finish_time", "description": "结束时间", "line_no": 342}, {"name": "assignment_status", "description": "分配状态", "line_no": 343}], "status_values": [], "rules": [], "notes": [], "suggested_violation_types": [], "source_lines": {"start": 329, "end": 344}, "display_group": "施工执行层", "key_property_lines": ["assignment_id：分配ID", "project_id：所属项目ID", "crew_id：施工队ID", "pod_id：PoD ID", "room_id：机房ID", "position_id：落位ID", "assignment_date：分配日期", "start_time：开始时间", "finish_time：结束时间", "assignment_status：分配状态"], "status_value_lines": [], "rule_lines": [], "note_lines": []}, "color": "#10b981", "search_text": "workassignment 施工执行层 4.5 施工执行层 {\"group\": \"4.5 施工执行层\", \"chinese_description\": \"施工分配。表示某个施工队在某个时间窗内被分配到哪个机房、安装哪个 pod。\", \"semantic_definition\": null, \"key_properties\": [{\"name\": \"assignment_id\", \"description\": \"分配id\", \"line_no\": 334}, {\"name\": \"project_id\", \"description\": \"所属项目id\", \"line_no\": 335}, {\"name\": \"crew_id\", \"description\": \"施工队id\", \"line_no\": 336}, {\"name\": \"pod_id\", \"description\": \"pod id\", \"line_no\": 337}, {\"name\": \"room_id\", \"description\": \"机房id\", \"line_no\": 338}, {\"name\": \"position_id\", \"description\": \"落位id\", \"line_no\": 339}, {\"name\": \"assignment_date\", \"description\": \"分配日期\", \"line_no\": 340}, {\"name\": \"start_time\", \"description\": \"开始时间\", \"line_no\": 341}, {\"name\": \"finish_time\", \"description\": \"结束时间\", \"line_no\": 342}, {\"name\": \"assignment_status\", \"description\": \"分配状态\", \"line_no\": 343}], \"status_values\": [], \"rules\": [], \"notes\": [], \"suggested_violation_types\": [], \"source_lines\": {\"start\": 329, \"end\": 344}, \"display_group\": \"施工执行层\", \"key_property_lines\": [\"assignment_id：分配id\", \"project_id：所属项目id\", \"crew_id：施工队id\", \"pod_id：pod id\", \"room_id：机房id\", \"position_id：落位id\", \"assignment_date：分配日期\", \"start_time：开始时间\", \"finish_time：结束时间\", \"assignment_status：分配状态\"], \"status_value_lines\": [], \"rule_lines\": [], \"note_lines\": []}"}, "position": {"x": 1500.0, "y": 320.0}}, {"data": {"id": "object_type:PlacementPlan", "label": "PlacementPlan\n决策与解释层", "display_name": "PlacementPlan", "type": "ObjectType", "attributes": {"group": "4.6 决策与解释层", "chinese_description": "落位建议方案。表示 PoD 落位建议。", "semantic_definition": null, "key_properties": [{"name": "placement_plan_id", "description": "落位方案ID", "line_no": 352}, {"name": "project_id", "description": "所属项目ID", "line_no": 353}, {"name": "pod_id", "description": "对应PoD ID", "line_no": 354}, {"name": "building_id", "description": "建议大楼ID", "line_no": 355}, {"name": "floor_id", "description": "建议楼层ID", "line_no": 356}, {"name": "room_id", "description": "建议机房ID", "line_no": 357}, {"name": "position_id", "description": "建议落位ID", "line_no": 358}, {"name": "placement_score", "description": "落位评分", "line_no": 359}, {"name": "plan_status", "description": "方案状态", "line_no": 360}], "status_values": [], "rules": [], "notes": [], "suggested_violation_types": [], "source_lines": {"start": 347, "end": 361}, "display_group": "决策与解释层", "key_property_lines": ["placement_plan_id：落位方案ID", "project_id：所属项目ID", "pod_id：对应PoD ID", "building_id：建议大楼ID", "floor_id：建议楼层ID", "room_id：建议机房ID", "position_id：建议落位ID", "placement_score：落位评分", "plan_status：方案状态"], "status_value_lines": [], "rule_lines": [], "note_lines": []}, "color": "#ef4444", "search_text": "placementplan 决策与解释层 4.6 决策与解释层 {\"group\": \"4.6 决策与解释层\", \"chinese_description\": \"落位建议方案。表示 pod 落位建议。\", \"semantic_definition\": null, \"key_properties\": [{\"name\": \"placement_plan_id\", \"description\": \"落位方案id\", \"line_no\": 352}, {\"name\": \"project_id\", \"description\": \"所属项目id\", \"line_no\": 353}, {\"name\": \"pod_id\", \"description\": \"对应pod id\", \"line_no\": 354}, {\"name\": \"building_id\", \"description\": \"建议大楼id\", \"line_no\": 355}, {\"name\": \"floor_id\", \"description\": \"建议楼层id\", \"line_no\": 356}, {\"name\": \"room_id\", \"description\": \"建议机房id\", \"line_no\": 357}, {\"name\": \"position_id\", \"description\": \"建议落位id\", \"line_no\": 358}, {\"name\": \"placement_score\", \"description\": \"落位评分\", \"line_no\": 359}, {\"name\": \"plan_status\", \"description\": \"方案状态\", \"line_no\": 360}], \"status_values\": [], \"rules\": [], \"notes\": [], \"suggested_violation_types\": [], \"source_lines\": {\"start\": 347, \"end\": 361}, \"display_group\": \"决策与解释层\", \"key_property_lines\": [\"placement_plan_id：落位方案id\", \"project_id：所属项目id\", \"pod_id：对应pod id\", \"building_id：建议大楼id\", \"floor_id：建议楼层id\", \"room_id：建议机房id\", \"position_id：建议落位id\", \"placement_score：落位评分\", \"plan_status：方案状态\"], \"status_value_lines\": [], \"rule_lines\": [], \"note_lines\": []}"}, "position": {"x": 1830.0, "y": 320.0}}, {"data": {"id": "object_type:ConstraintViolation", "label": "ConstraintViolation\n决策与解释层", "display_name": "ConstraintViolation", "type": "ObjectType", "attributes": {"group": "4.6 决策与解释层", "chinese_description": "约束冲突。表示当前方案不满足约束的原因。", "semantic_definition": null, "key_properties": [{"name": "violation_id", "description": "冲突ID", "line_no": 367}, {"name": "project_id", "description": "所属项目ID", "line_no": 368}, {"name": "object_type", "description": "冲突对象类型", "line_no": 369}, {"name": "object_id", "description": "冲突对象ID", "line_no": 370}, {"name": "violation_type", "description": "冲突类型", "line_no": 371}, {"name": "severity", "description": "严重程度", "line_no": 372}, {"name": "message", "description": "说明信息", "line_no": 373}, {"name": "related_milestone_id", "description": "关联里程碑ID", "line_no": 374}], "status_values": [], "rules": [], "notes": [], "suggested_violation_types": [{"name": "MilestoneMissRisk", "description": "里程碑失约风险", "line_no": 377}, {"name": "ArrivalTooLate", "description": "到货过晚", "line_no": 378}, {"name": "ArrivalTooEarlyBacklog", "description": "到货过早导致积压", "line_no": 379}, {"name": "CrewCapacityExceeded", "description": "施工队能力超限", "line_no": 380}, {"name": "PositionUnavailable", "description": "落位不可用", "line_no": 381}, {"name": "DependencyUnsatisfied", "description": "依赖未满足", "line_no": 382}], "source_lines": {"start": 362, "end": 383}, "display_group": "决策与解释层", "key_property_lines": ["violation_id：冲突ID", "project_id：所属项目ID", "object_type：冲突对象类型", "object_id：冲突对象ID", "violation_type：冲突类型", "severity：严重程度", "message：说明信息", "related_milestone_id：关联里程碑ID"], "status_value_lines": [], "rule_lines": [], "note_lines": []}, "color": "#ef4444", "search_text": "constraintviolation 决策与解释层 4.6 决策与解释层 {\"group\": \"4.6 决策与解释层\", \"chinese_description\": \"约束冲突。表示当前方案不满足约束的原因。\", \"semantic_definition\": null, \"key_properties\": [{\"name\": \"violation_id\", \"description\": \"冲突id\", \"line_no\": 367}, {\"name\": \"project_id\", \"description\": \"所属项目id\", \"line_no\": 368}, {\"name\": \"object_type\", \"description\": \"冲突对象类型\", \"line_no\": 369}, {\"name\": \"object_id\", \"description\": \"冲突对象id\", \"line_no\": 370}, {\"name\": \"violation_type\", \"description\": \"冲突类型\", \"line_no\": 371}, {\"name\": \"severity\", \"description\": \"严重程度\", \"line_no\": 372}, {\"name\": \"message\", \"description\": \"说明信息\", \"line_no\": 373}, {\"name\": \"related_milestone_id\", \"description\": \"关联里程碑id\", \"line_no\": 374}], \"status_values\": [], \"rules\": [], \"notes\": [], \"suggested_violation_types\": [{\"name\": \"milestonemissrisk\", \"description\": \"里程碑失约风险\", \"line_no\": 377}, {\"name\": \"arrivaltoolate\", \"description\": \"到货过晚\", \"line_no\": 378}, {\"name\": \"arrivaltooearlybacklog\", \"description\": \"到货过早导致积压\", \"line_no\": 379}, {\"name\": \"crewcapacityexceeded\", \"description\": \"施工队能力超限\", \"line_no\": 380}, {\"name\": \"positionunavailable\", \"description\": \"落位不可用\", \"line_no\": 381}, {\"name\": \"dependencyunsatisfied\", \"description\": \"依赖未满足\", \"line_no\": 382}], \"source_lines\": {\"start\": 362, \"end\": 383}, \"display_group\": \"决策与解释层\", \"key_property_lines\": [\"violation_id：冲突id\", \"project_id：所属项目id\", \"object_type：冲突对象类型\", \"object_id：冲突对象id\", \"violation_type：冲突类型\", \"severity：严重程度\", \"message：说明信息\", \"related_milestone_id：关联里程碑id\"], \"status_value_lines\": [], \"rule_lines\": [], \"note_lines\": []}"}, "position": {"x": 1830.0, "y": 170.0}}, {"data": {"id": "object_type:DecisionRecommendation", "label": "DecisionRecommendation\n决策与解释层", "display_name": "DecisionRecommendation", "type": "ObjectType", "attributes": {"group": "4.6 决策与解释层", "chinese_description": "决策建议。表示 agent 输出的建议结果。", "semantic_definition": null, "key_properties": [{"name": "recommendation_id", "description": "建议ID", "line_no": 389}, {"name": "project_id", "description": "所属项目ID", "line_no": 390}, {"name": "recommendation_type", "description": "建议类型", "line_no": 391}, {"name": "target_object_type", "description": "目标对象类型", "line_no": 392}, {"name": "target_object_id", "description": "目标对象ID", "line_no": 393}, {"name": "recommendation_text", "description": "建议内容", "line_no": 394}, {"name": "confidence", "description": "置信度", "line_no": 395}, {"name": "created_at", "description": "创建时间", "line_no": 396}], "status_values": [], "rules": [], "notes": [], "suggested_violation_types": [], "source_lines": {"start": 384, "end": 399}, "display_group": "决策与解释层", "key_property_lines": ["recommendation_id：建议ID", "project_id：所属项目ID", "recommendation_type：建议类型", "target_object_type：目标对象类型", "target_object_id：目标对象ID", "recommendation_text：建议内容", "confidence：置信度", "created_at：创建时间"], "status_value_lines": [], "rule_lines": [], "note_lines": []}, "color": "#ef4444", "search_text": "decisionrecommendation 决策与解释层 4.6 决策与解释层 {\"group\": \"4.6 决策与解释层\", \"chinese_description\": \"决策建议。表示 agent 输出的建议结果。\", \"semantic_definition\": null, \"key_properties\": [{\"name\": \"recommendation_id\", \"description\": \"建议id\", \"line_no\": 389}, {\"name\": \"project_id\", \"description\": \"所属项目id\", \"line_no\": 390}, {\"name\": \"recommendation_type\", \"description\": \"建议类型\", \"line_no\": 391}, {\"name\": \"target_object_type\", \"description\": \"目标对象类型\", \"line_no\": 392}, {\"name\": \"target_object_id\", \"description\": \"目标对象id\", \"line_no\": 393}, {\"name\": \"recommendation_text\", \"description\": \"建议内容\", \"line_no\": 394}, {\"name\": \"confidence\", \"description\": \"置信度\", \"line_no\": 395}, {\"name\": \"created_at\", \"description\": \"创建时间\", \"line_no\": 396}], \"status_values\": [], \"rules\": [], \"notes\": [], \"suggested_violation_types\": [], \"source_lines\": {\"start\": 384, \"end\": 399}, \"display_group\": \"决策与解释层\", \"key_property_lines\": [\"recommendation_id：建议id\", \"project_id：所属项目id\", \"recommendation_type：建议类型\", \"target_object_type：目标对象类型\", \"target_object_id：目标对象id\", \"recommendation_text：建议内容\", \"confidence：置信度\", \"created_at：创建时间\"], \"status_value_lines\": [], \"rule_lines\": [], \"note_lines\": []}"}, "position": {"x": 1830.0, "y": 470.0}}, {"data": {"id": "metric_group:关键派生指标", "label": "关键派生指标", "display_name": "关键派生指标", "type": "MetricGroup", "attributes": {"display_group": "关键派生指标", "description": "点击图中该节点可原地展开或收起详细指标。", "metric_names": ["waiting_install_duration", "latest_safe_arrival_time", "earliest_useful_arrival_time", "arrival_delay_duration", "arrival_backlog_risk_level", "room_handover_completed_pod_count", "room_handover_completion_rate", "room_milestone_gap_pod_count", "floor_handover_completed_room_count", "floor_milestone_completion_rate", "floor_milestone_gap_room_count", "crew_daily_load", "crew_capacity_utilization", "room_daily_install_count", "floor_daily_install_count", "schedule_feasibility_flag", "placement_feasibility_flag", "milestone_risk_level"]}, "color": "#6d28d9", "search_text": "关键派生指标 waiting_install_duration latest_safe_arrival_time earliest_useful_arrival_time arrival_delay_duration arrival_backlog_risk_level room_handover_completed_pod_count room_handover_completion_rate room_milestone_gap_pod_count floor_handover_completed_room_count floor_milestone_completion_rate floor_milestone_gap_room_count crew_daily_load crew_capacity_utilization room_daily_install_count floor_daily_install_count schedule_feasibility_flag placement_feasibility_flag milestone_risk_level"}, "position": {"x": 2160.0, "y": 320.0}}, {"data": {"id": "derived_metric:waiting_install_duration", "label": "waiting_install_duration", "display_name": "waiting_install_duration", "type": "DerivedMetric", "attributes": {"group": "6. 关键派生指标", "description": "待安装时长，等于实际安装开始时间减去实际到货时间", "source_lines": {"start": 487, "end": 487}, "display_group": "关键派生指标", "rule_lines": [], "note_lines": []}, "color": "#7c3aed", "search_text": "waiting_install_duration 关键派生指标 {\"group\": \"6. 关键派生指标\", \"description\": \"待安装时长，等于实际安装开始时间减去实际到货时间\", \"source_lines\": {\"start\": 487, \"end\": 487}, \"display_group\": \"关键派生指标\", \"rule_lines\": [], \"note_lines\": []}"}, "classes": "metric-hidden", "position": {"x": 2050.0, "y": 450.0}}, {"data": {"id": "metric_edge:1", "source": "metric_group:关键派生指标", "target": "derived_metric:waiting_install_duration", "label": "", "relation": "__METRIC__", "synthetic": true, "edgeColor": "#c4b5fd", "lineStyle": "dashed", "width": 2}, "classes": "metric-hidden"}, {"data": {"id": "derived_metric:latest_safe_arrival_time", "label": "latest_safe_arrival_time", "display_name": "latest_safe_arrival_time", "type": "DerivedMetric", "attributes": {"group": "6. 关键派生指标", "description": "最晚安全到货时间", "source_lines": {"start": 488, "end": 488}, "display_group": "关键派生指标", "rule_lines": [], "note_lines": []}, "color": "#7c3aed", "search_text": "latest_safe_arrival_time 关键派生指标 {\"group\": \"6. 关键派生指标\", \"description\": \"最晚安全到货时间\", \"source_lines\": {\"start\": 488, \"end\": 488}, \"display_group\": \"关键派生指标\", \"rule_lines\": [], \"note_lines\": []}"}, "classes": "metric-hidden", "position": {"x": 2270.0, "y": 450.0}}, {"data": {"id": "metric_edge:2", "source": "metric_group:关键派生指标", "target": "derived_metric:latest_safe_arrival_time", "label": "", "relation": "__METRIC__", "synthetic": true, "edgeColor": "#c4b5fd", "lineStyle": "dashed", "width": 2}, "classes": "metric-hidden"}, {"data": {"id": "derived_metric:earliest_useful_arrival_time", "label": "earliest_useful_arrival_time", "display_name": "earliest_useful_arrival_time", "type": "DerivedMetric", "attributes": {"group": "6. 关键派生指标", "description": "最早有意义到货时间", "source_lines": {"start": 489, "end": 489}, "display_group": "关键派生指标", "rule_lines": [], "note_lines": []}, "color": "#7c3aed", "search_text": "earliest_useful_arrival_time 关键派生指标 {\"group\": \"6. 关键派生指标\", \"description\": \"最早有意义到货时间\", \"source_lines\": {\"start\": 489, \"end\": 489}, \"display_group\": \"关键派生指标\", \"rule_lines\": [], \"note_lines\": []}"}, "classes": "metric-hidden", "position": {"x": 2050.0, "y": 560.0}}, {"data": {"id": "metric_edge:3", "source": "metric_group:关键派生指标", "target": "derived_metric:earliest_useful_arrival_time", "label": "", "relation": "__METRIC__", "synthetic": true, "edgeColor": "#c4b5fd", "lineStyle": "dashed", "width": 2}, "classes": "metric-hidden"}, {"data": {"id": "derived_metric:arrival_delay_duration", "label": "arrival_delay_duration", "display_name": "arrival_delay_duration", "type": "DerivedMetric", "attributes": {"group": "6. 关键派生指标", "description": "到货延迟时长", "source_lines": {"start": 490, "end": 490}, "display_group": "关键派生指标", "rule_lines": [], "note_lines": []}, "color": "#7c3aed", "search_text": "arrival_delay_duration 关键派生指标 {\"group\": \"6. 关键派生指标\", \"description\": \"到货延迟时长\", \"source_lines\": {\"start\": 490, \"end\": 490}, \"display_group\": \"关键派生指标\", \"rule_lines\": [], \"note_lines\": []}"}, "classes": "metric-hidden", "position": {"x": 2270.0, "y": 560.0}}, {"data": {"id": "metric_edge:4", "source": "metric_group:关键派生指标", "target": "derived_metric:arrival_delay_duration", "label": "", "relation": "__METRIC__", "synthetic": true, "edgeColor": "#c4b5fd", "lineStyle": "dashed", "width": 2}, "classes": "metric-hidden"}, {"data": {"id": "derived_metric:arrival_backlog_risk_level", "label": "arrival_backlog_risk_level", "display_name": "arrival_backlog_risk_level", "type": "DerivedMetric", "attributes": {"group": "6. 关键派生指标", "description": "到货积压风险等级", "source_lines": {"start": 491, "end": 491}, "display_group": "关键派生指标", "rule_lines": [], "note_lines": []}, "color": "#7c3aed", "search_text": "arrival_backlog_risk_level 关键派生指标 {\"group\": \"6. 关键派生指标\", \"description\": \"到货积压风险等级\", \"source_lines\": {\"start\": 491, \"end\": 491}, \"display_group\": \"关键派生指标\", \"rule_lines\": [], \"note_lines\": []}"}, "classes": "metric-hidden", "position": {"x": 2050.0, "y": 670.0}}, {"data": {"id": "metric_edge:5", "source": "metric_group:关键派生指标", "target": "derived_metric:arrival_backlog_risk_level", "label": "", "relation": "__METRIC__", "synthetic": true, "edgeColor": "#c4b5fd", "lineStyle": "dashed", "width": 2}, "classes": "metric-hidden"}, {"data": {"id": "derived_metric:room_handover_completed_pod_count", "label": "room_handover_completed_pod_count", "display_name": "room_handover_completed_pod_count", "type": "DerivedMetric", "attributes": {"group": "6. 关键派生指标", "description": "机房已完成移交的PoD数量", "source_lines": {"start": 492, "end": 492}, "display_group": "关键派生指标", "rule_lines": [], "note_lines": []}, "color": "#7c3aed", "search_text": "room_handover_completed_pod_count 关键派生指标 {\"group\": \"6. 关键派生指标\", \"description\": \"机房已完成移交的pod数量\", \"source_lines\": {\"start\": 492, \"end\": 492}, \"display_group\": \"关键派生指标\", \"rule_lines\": [], \"note_lines\": []}"}, "classes": "metric-hidden", "position": {"x": 2270.0, "y": 670.0}}, {"data": {"id": "metric_edge:6", "source": "metric_group:关键派生指标", "target": "derived_metric:room_handover_completed_pod_count", "label": "", "relation": "__METRIC__", "synthetic": true, "edgeColor": "#c4b5fd", "lineStyle": "dashed", "width": 2}, "classes": "metric-hidden"}, {"data": {"id": "derived_metric:room_handover_completion_rate", "label": "room_handover_completion_rate", "display_name": "room_handover_completion_rate", "type": "DerivedMetric", "attributes": {"group": "6. 关键派生指标", "description": "机房移交完成率", "source_lines": {"start": 493, "end": 493}, "display_group": "关键派生指标", "rule_lines": [], "note_lines": []}, "color": "#7c3aed", "search_text": "room_handover_completion_rate 关键派生指标 {\"group\": \"6. 关键派生指标\", \"description\": \"机房移交完成率\", \"source_lines\": {\"start\": 493, \"end\": 493}, \"display_group\": \"关键派生指标\", \"rule_lines\": [], \"note_lines\": []}"}, "classes": "metric-hidden", "position": {"x": 2050.0, "y": 780.0}}, {"data": {"id": "metric_edge:7", "source": "metric_group:关键派生指标", "target": "derived_metric:room_handover_completion_rate", "label": "", "relation": "__METRIC__", "synthetic": true, "edgeColor": "#c4b5fd", "lineStyle": "dashed", "width": 2}, "classes": "metric-hidden"}, {"data": {"id": "derived_metric:room_milestone_gap_pod_count", "label": "room_milestone_gap_pod_count", "display_name": "room_milestone_gap_pod_count", "type": "DerivedMetric", "attributes": {"group": "6. 关键派生指标", "description": "机房里程碑差额PoD数量", "source_lines": {"start": 494, "end": 494}, "display_group": "关键派生指标", "rule_lines": [], "note_lines": []}, "color": "#7c3aed", "search_text": "room_milestone_gap_pod_count 关键派生指标 {\"group\": \"6. 关键派生指标\", \"description\": \"机房里程碑差额pod数量\", \"source_lines\": {\"start\": 494, \"end\": 494}, \"display_group\": \"关键派生指标\", \"rule_lines\": [], \"note_lines\": []}"}, "classes": "metric-hidden", "position": {"x": 2270.0, "y": 780.0}}, {"data": {"id": "metric_edge:8", "source": "metric_group:关键派生指标", "target": "derived_metric:room_milestone_gap_pod_count", "label": "", "relation": "__METRIC__", "synthetic": true, "edgeColor": "#c4b5fd", "lineStyle": "dashed", "width": 2}, "classes": "metric-hidden"}, {"data": {"id": "derived_metric:floor_handover_completed_room_count", "label": "floor_handover_completed_room_count", "display_name": "floor_handover_completed_room_count", "type": "DerivedMetric", "attributes": {"group": "6. 关键派生指标", "description": "楼层已完成移交的机房数量", "source_lines": {"start": 495, "end": 495}, "display_group": "关键派生指标", "rule_lines": [], "note_lines": []}, "color": "#7c3aed", "search_text": "floor_handover_completed_room_count 关键派生指标 {\"group\": \"6. 关键派生指标\", \"description\": \"楼层已完成移交的机房数量\", \"source_lines\": {\"start\": 495, \"end\": 495}, \"display_group\": \"关键派生指标\", \"rule_lines\": [], \"note_lines\": []}"}, "classes": "metric-hidden", "position": {"x": 2050.0, "y": 890.0}}, {"data": {"id": "metric_edge:9", "source": "metric_group:关键派生指标", "target": "derived_metric:floor_handover_completed_room_count", "label": "", "relation": "__METRIC__", "synthetic": true, "edgeColor": "#c4b5fd", "lineStyle": "dashed", "width": 2}, "classes": "metric-hidden"}, {"data": {"id": "derived_metric:floor_milestone_completion_rate", "label": "floor_milestone_completion_rate", "display_name": "floor_milestone_completion_rate", "type": "DerivedMetric", "attributes": {"group": "6. 关键派生指标", "description": "楼层里程碑完成率", "source_lines": {"start": 496, "end": 496}, "display_group": "关键派生指标", "rule_lines": [], "note_lines": []}, "color": "#7c3aed", "search_text": "floor_milestone_completion_rate 关键派生指标 {\"group\": \"6. 关键派生指标\", \"description\": \"楼层里程碑完成率\", \"source_lines\": {\"start\": 496, \"end\": 496}, \"display_group\": \"关键派生指标\", \"rule_lines\": [], \"note_lines\": []}"}, "classes": "metric-hidden", "position": {"x": 2270.0, "y": 890.0}}, {"data": {"id": "metric_edge:10", "source": "metric_group:关键派生指标", "target": "derived_metric:floor_milestone_completion_rate", "label": "", "relation": "__METRIC__", "synthetic": true, "edgeColor": "#c4b5fd", "lineStyle": "dashed", "width": 2}, "classes": "metric-hidden"}, {"data": {"id": "derived_metric:floor_milestone_gap_room_count", "label": "floor_milestone_gap_room_count", "display_name": "floor_milestone_gap_room_count", "type": "DerivedMetric", "attributes": {"group": "6. 关键派生指标", "description": "楼层里程碑差额机房数量", "source_lines": {"start": 497, "end": 497}, "display_group": "关键派生指标", "rule_lines": [], "note_lines": []}, "color": "#7c3aed", "search_text": "floor_milestone_gap_room_count 关键派生指标 {\"group\": \"6. 关键派生指标\", \"description\": \"楼层里程碑差额机房数量\", \"source_lines\": {\"start\": 497, \"end\": 497}, \"display_group\": \"关键派生指标\", \"rule_lines\": [], \"note_lines\": []}"}, "classes": "metric-hidden", "position": {"x": 2050.0, "y": 1000.0}}, {"data": {"id": "metric_edge:11", "source": "metric_group:关键派生指标", "target": "derived_metric:floor_milestone_gap_room_count", "label": "", "relation": "__METRIC__", "synthetic": true, "edgeColor": "#c4b5fd", "lineStyle": "dashed", "width": 2}, "classes": "metric-hidden"}, {"data": {"id": "derived_metric:crew_daily_load", "label": "crew_daily_load", "display_name": "crew_daily_load", "type": "DerivedMetric", "attributes": {"group": "6. 关键派生指标", "description": "施工队日负载", "source_lines": {"start": 498, "end": 498}, "display_group": "关键派生指标", "rule_lines": [], "note_lines": []}, "color": "#7c3aed", "search_text": "crew_daily_load 关键派生指标 {\"group\": \"6. 关键派生指标\", \"description\": \"施工队日负载\", \"source_lines\": {\"start\": 498, \"end\": 498}, \"display_group\": \"关键派生指标\", \"rule_lines\": [], \"note_lines\": []}"}, "classes": "metric-hidden", "position": {"x": 2270.0, "y": 1000.0}}, {"data": {"id": "metric_edge:12", "source": "metric_group:关键派生指标", "target": "derived_metric:crew_daily_load", "label": "", "relation": "__METRIC__", "synthetic": true, "edgeColor": "#c4b5fd", "lineStyle": "dashed", "width": 2}, "classes": "metric-hidden"}, {"data": {"id": "derived_metric:crew_capacity_utilization", "label": "crew_capacity_utilization", "display_name": "crew_capacity_utilization", "type": "DerivedMetric", "attributes": {"group": "6. 关键派生指标", "description": "施工队能力利用率", "source_lines": {"start": 499, "end": 499}, "display_group": "关键派生指标", "rule_lines": [], "note_lines": []}, "color": "#7c3aed", "search_text": "crew_capacity_utilization 关键派生指标 {\"group\": \"6. 关键派生指标\", \"description\": \"施工队能力利用率\", \"source_lines\": {\"start\": 499, \"end\": 499}, \"display_group\": \"关键派生指标\", \"rule_lines\": [], \"note_lines\": []}"}, "classes": "metric-hidden", "position": {"x": 2050.0, "y": 1110.0}}, {"data": {"id": "metric_edge:13", "source": "metric_group:关键派生指标", "target": "derived_metric:crew_capacity_utilization", "label": "", "relation": "__METRIC__", "synthetic": true, "edgeColor": "#c4b5fd", "lineStyle": "dashed", "width": 2}, "classes": "metric-hidden"}, {"data": {"id": "derived_metric:room_daily_install_count", "label": "room_daily_install_count", "display_name": "room_daily_install_count", "type": "DerivedMetric", "attributes": {"group": "6. 关键派生指标", "description": "机房日安装PoD数量", "source_lines": {"start": 500, "end": 500}, "display_group": "关键派生指标", "rule_lines": [], "note_lines": []}, "color": "#7c3aed", "search_text": "room_daily_install_count 关键派生指标 {\"group\": \"6. 关键派生指标\", \"description\": \"机房日安装pod数量\", \"source_lines\": {\"start\": 500, \"end\": 500}, \"display_group\": \"关键派生指标\", \"rule_lines\": [], \"note_lines\": []}"}, "classes": "metric-hidden", "position": {"x": 2270.0, "y": 1110.0}}, {"data": {"id": "metric_edge:14", "source": "metric_group:关键派生指标", "target": "derived_metric:room_daily_install_count", "label": "", "relation": "__METRIC__", "synthetic": true, "edgeColor": "#c4b5fd", "lineStyle": "dashed", "width": 2}, "classes": "metric-hidden"}, {"data": {"id": "derived_metric:floor_daily_install_count", "label": "floor_daily_install_count", "display_name": "floor_daily_install_count", "type": "DerivedMetric", "attributes": {"group": "6. 关键派生指标", "description": "楼层日安装PoD数量", "source_lines": {"start": 501, "end": 501}, "display_group": "关键派生指标", "rule_lines": [], "note_lines": []}, "color": "#7c3aed", "search_text": "floor_daily_install_count 关键派生指标 {\"group\": \"6. 关键派生指标\", \"description\": \"楼层日安装pod数量\", \"source_lines\": {\"start\": 501, \"end\": 501}, \"display_group\": \"关键派生指标\", \"rule_lines\": [], \"note_lines\": []}"}, "classes": "metric-hidden", "position": {"x": 2050.0, "y": 1220.0}}, {"data": {"id": "metric_edge:15", "source": "metric_group:关键派生指标", "target": "derived_metric:floor_daily_install_count", "label": "", "relation": "__METRIC__", "synthetic": true, "edgeColor": "#c4b5fd", "lineStyle": "dashed", "width": 2}, "classes": "metric-hidden"}, {"data": {"id": "derived_metric:schedule_feasibility_flag", "label": "schedule_feasibility_flag", "display_name": "schedule_feasibility_flag", "type": "DerivedMetric", "attributes": {"group": "6. 关键派生指标", "description": "排期可执行标记", "source_lines": {"start": 502, "end": 502}, "display_group": "关键派生指标", "rule_lines": [], "note_lines": []}, "color": "#7c3aed", "search_text": "schedule_feasibility_flag 关键派生指标 {\"group\": \"6. 关键派生指标\", \"description\": \"排期可执行标记\", \"source_lines\": {\"start\": 502, \"end\": 502}, \"display_group\": \"关键派生指标\", \"rule_lines\": [], \"note_lines\": []}"}, "classes": "metric-hidden", "position": {"x": 2270.0, "y": 1220.0}}, {"data": {"id": "metric_edge:16", "source": "metric_group:关键派生指标", "target": "derived_metric:schedule_feasibility_flag", "label": "", "relation": "__METRIC__", "synthetic": true, "edgeColor": "#c4b5fd", "lineStyle": "dashed", "width": 2}, "classes": "metric-hidden"}, {"data": {"id": "derived_metric:placement_feasibility_flag", "label": "placement_feasibility_flag", "display_name": "placement_feasibility_flag", "type": "DerivedMetric", "attributes": {"group": "6. 关键派生指标", "description": "落位可执行标记", "source_lines": {"start": 503, "end": 503}, "display_group": "关键派生指标", "rule_lines": [], "note_lines": []}, "color": "#7c3aed", "search_text": "placement_feasibility_flag 关键派生指标 {\"group\": \"6. 关键派生指标\", \"description\": \"落位可执行标记\", \"source_lines\": {\"start\": 503, \"end\": 503}, \"display_group\": \"关键派生指标\", \"rule_lines\": [], \"note_lines\": []}"}, "classes": "metric-hidden", "position": {"x": 2050.0, "y": 1330.0}}, {"data": {"id": "metric_edge:17", "source": "metric_group:关键派生指标", "target": "derived_metric:placement_feasibility_flag", "label": "", "relation": "__METRIC__", "synthetic": true, "edgeColor": "#c4b5fd", "lineStyle": "dashed", "width": 2}, "classes": "metric-hidden"}, {"data": {"id": "derived_metric:milestone_risk_level", "label": "milestone_risk_level", "display_name": "milestone_risk_level", "type": "DerivedMetric", "attributes": {"group": "6. 关键派生指标", "description": "里程碑风险等级", "source_lines": {"start": 504, "end": 504}, "display_group": "关键派生指标", "rule_lines": [], "note_lines": []}, "color": "#7c3aed", "search_text": "milestone_risk_level 关键派生指标 {\"group\": \"6. 关键派生指标\", \"description\": \"里程碑风险等级\", \"source_lines\": {\"start\": 504, \"end\": 504}, \"display_group\": \"关键派生指标\", \"rule_lines\": [], \"note_lines\": []}"}, "classes": "metric-hidden", "position": {"x": 2270.0, "y": 1330.0}}, {"data": {"id": "metric_edge:18", "source": "metric_group:关键派生指标", "target": "derived_metric:milestone_risk_level", "label": "", "relation": "__METRIC__", "synthetic": true, "edgeColor": "#c4b5fd", "lineStyle": "dashed", "width": 2}, "classes": "metric-hidden"}, {"data": {"id": "e1", "source": "object_type:Project", "target": "object_type:Building", "label": "HAS", "relation": "HAS", "attributes": {"group": "5.1 项目与空间关系", "description": "项目包含大楼", "source_lines": {"start": 426, "end": 426}}, "synthetic": false, "edgeColor": "#94a3b8", "lineStyle": "solid", "width": 3}}, {"data": {"id": "e2", "source": "object_type:Building", "target": "object_type:Floor", "label": "HAS", "relation": "HAS", "attributes": {"group": "5.1 项目与空间关系", "description": "大楼包含楼层", "source_lines": {"start": 427, "end": 427}}, "synthetic": false, "edgeColor": "#94a3b8", "lineStyle": "solid", "width": 3}}, {"data": {"id": "e3", "source": "object_type:Floor", "target": "object_type:Room", "label": "HAS", "relation": "HAS", "attributes": {"group": "5.1 项目与空间关系", "description": "楼层包含机房", "source_lines": {"start": 428, "end": 428}}, "synthetic": false, "edgeColor": "#94a3b8", "lineStyle": "solid", "width": 3}}, {"data": {"id": "e4", "source": "object_type:Room", "target": "object_type:PoDPosition", "label": "HAS", "relation": "HAS", "attributes": {"group": "5.1 项目与空间关系", "description": "机房包含PoD落位", "source_lines": {"start": 429, "end": 429}}, "synthetic": false, "edgeColor": "#94a3b8", "lineStyle": "solid", "width": 3}}, {"data": {"id": "e5", "source": "object_type:Project", "target": "object_type:RoomMilestone", "label": "HAS", "relation": "HAS", "attributes": {"group": "5.2 项目与里程碑关系", "description": "项目包含机房里程碑", "source_lines": {"start": 433, "end": 433}}, "synthetic": false, "edgeColor": "#94a3b8", "lineStyle": "solid", "width": 3}}, {"data": {"id": "e6", "source": "object_type:Project", "target": "object_type:FloorMilestone", "label": "HAS", "relation": "HAS", "attributes": {"group": "5.2 项目与里程碑关系", "description": "项目包含楼层里程碑", "source_lines": {"start": 434, "end": 434}}, "synthetic": false, "edgeColor": "#94a3b8", "lineStyle": "solid", "width": 3}}, {"data": {"id": "e7", "source": "object_type:RoomMilestone", "target": "object_type:Room", "label": "CONSTRAINS", "relation": "CONSTRAINS", "attributes": {"group": "5.2 项目与里程碑关系", "description": "机房里程碑约束机房", "source_lines": {"start": 435, "end": 435}}, "synthetic": false, "edgeColor": "#94a3b8", "lineStyle": "solid", "width": 3}}, {"data": {"id": "e8", "source": "object_type:FloorMilestone", "target": "object_type:Floor", "label": "CONSTRAINS", "relation": "CONSTRAINS", "attributes": {"group": "5.2 项目与里程碑关系", "description": "楼层里程碑约束楼层", "source_lines": {"start": 436, "end": 436}}, "synthetic": false, "edgeColor": "#94a3b8", "lineStyle": "solid", "width": 3}}, {"data": {"id": "e9", "source": "object_type:FloorMilestone", "target": "object_type:RoomMilestone", "label": "AGGREGATES", "relation": "AGGREGATES", "attributes": {"group": "5.2 项目与里程碑关系", "description": "楼层里程碑聚合机房里程碑", "source_lines": {"start": 437, "end": 437}}, "synthetic": false, "edgeColor": "#94a3b8", "lineStyle": "solid", "width": 3}}, {"data": {"id": "e10", "source": "object_type:Project", "target": "object_type:PoD", "label": "DELIVERS", "relation": "DELIVERS", "attributes": {"group": "5.3 项目与 PoD 关系", "description": "项目交付PoD", "source_lines": {"start": 441, "end": 441}}, "synthetic": false, "edgeColor": "#94a3b8", "lineStyle": "solid", "width": 3}}, {"data": {"id": "e11", "source": "object_type:PoD", "target": "object_type:Building", "label": "ASSIGNED_TO", "relation": "ASSIGNED_TO", "attributes": {"group": "5.3 项目与 PoD 关系", "description": "PoD分配到大楼", "source_lines": {"start": 442, "end": 442}}, "synthetic": false, "edgeColor": "#94a3b8", "lineStyle": "solid", "width": 3}}, {"data": {"id": "e12", "source": "object_type:PoD", "target": "object_type:Floor", "label": "ASSIGNED_TO", "relation": "ASSIGNED_TO", "attributes": {"group": "5.3 项目与 PoD 关系", "description": "PoD分配到楼层", "source_lines": {"start": 443, "end": 443}}, "synthetic": false, "edgeColor": "#94a3b8", "lineStyle": "solid", "width": 3}}, {"data": {"id": "e13", "source": "object_type:PoD", "target": "object_type:Room", "label": "ASSIGNED_TO", "relation": "ASSIGNED_TO", "attributes": {"group": "5.3 项目与 PoD 关系", "description": "PoD分配到机房", "source_lines": {"start": 444, "end": 444}}, "synthetic": false, "edgeColor": "#94a3b8", "lineStyle": "solid", "width": 3}}, {"data": {"id": "e14", "source": "object_type:PoD", "target": "object_type:PoDPosition", "label": "ASSIGNED_TO", "relation": "ASSIGNED_TO", "attributes": {"group": "5.3 项目与 PoD 关系", "description": "PoD分配到落位", "source_lines": {"start": 445, "end": 445}}, "synthetic": false, "edgeColor": "#94a3b8", "lineStyle": "solid", "width": 3}}, {"data": {"id": "e15", "source": "object_type:Project", "target": "object_type:Shipment", "label": "HAS", "relation": "HAS", "attributes": {"group": "5.4 PoD 与物流关系", "description": "项目包含发货单", "source_lines": {"start": 449, "end": 449}}, "synthetic": false, "edgeColor": "#94a3b8", "lineStyle": "solid", "width": 3}}, {"data": {"id": "e16", "source": "object_type:Shipment", "target": "object_type:PoD", "label": "SHIPS", "relation": "SHIPS", "attributes": {"group": "5.4 PoD 与物流关系", "description": "发货单运输PoD", "source_lines": {"start": 450, "end": 450}}, "synthetic": false, "edgeColor": "#94a3b8", "lineStyle": "solid", "width": 3}}, {"data": {"id": "e17", "source": "object_type:PoD", "target": "object_type:ArrivalEvent", "label": "HAS", "relation": "HAS", "attributes": {"group": "5.4 PoD 与物流关系", "description": "PoD具有到货事件", "source_lines": {"start": 451, "end": 451}}, "synthetic": false, "edgeColor": "#94a3b8", "lineStyle": "solid", "width": 3}}, {"data": {"id": "e18", "source": "object_type:ArrivalPlan", "target": "object_type:PoD", "label": "APPLIES_TO", "relation": "APPLIES_TO", "attributes": {"group": "5.4 PoD 与物流关系", "description": "到货方案作用于PoD", "source_lines": {"start": 452, "end": 452}}, "synthetic": false, "edgeColor": "#94a3b8", "lineStyle": "solid", "width": 3}}, {"data": {"id": "e19", "source": "object_type:PoD", "target": "object_type:ActivityInstance", "label": "HAS", "relation": "HAS", "attributes": {"group": "5.5 PoD 与活动关系", "description": "PoD具有活动实例", "source_lines": {"start": 456, "end": 456}}, "synthetic": false, "edgeColor": "#94a3b8", "lineStyle": "solid", "width": 3}}, {"data": {"id": "e20", "source": "object_type:ActivityTemplate", "target": "object_type:ActivityInstance", "label": "GENERATES", "relation": "GENERATES", "attributes": {"group": "5.5 PoD 与活动关系", "description": "活动模板生成活动实例", "source_lines": {"start": 457, "end": 457}}, "synthetic": false, "edgeColor": "#94a3b8", "lineStyle": "solid", "width": 3}}, {"data": {"id": "e21", "source": "object_type:ActivityInstance", "target": "object_type:SLAStandard", "label": "USES", "relation": "USES", "attributes": {"group": "5.5 PoD 与活动关系", "description": "活动实例使用标准SLA", "source_lines": {"start": 458, "end": 458}}, "synthetic": false, "edgeColor": "#94a3b8", "lineStyle": "solid", "width": 3}}, {"data": {"id": "e22", "source": "object_type:ActivityInstance", "target": "object_type:ActivityInstance", "label": "DEPENDS_ON", "relation": "DEPENDS_ON", "attributes": {"group": "5.5 PoD 与活动关系", "description": "活动实例依赖活动实例", "source_lines": {"start": 459, "end": 459}}, "synthetic": false, "edgeColor": "#94a3b8", "lineStyle": "solid", "width": 3}}, {"data": {"id": "e23", "source": "object_type:ActivityDependencyTemplate", "target": "object_type:ActivityInstance", "label": "DEFINES", "relation": "DEFINES", "attributes": {"group": "5.5 PoD 与活动关系", "description": "活动依赖模板定义活动实例关系", "source_lines": {"start": 460, "end": 460}}, "synthetic": false, "edgeColor": "#94a3b8", "lineStyle": "solid", "width": 3}}, {"data": {"id": "e24", "source": "object_type:PoDSchedule", "target": "object_type:ActivityInstance", "label": "CONTAINS", "relation": "CONTAINS", "attributes": {"group": "5.5 PoD 与活动关系", "description": "PoD排期包含活动实例", "source_lines": {"start": 461, "end": 461}}, "synthetic": false, "edgeColor": "#94a3b8", "lineStyle": "solid", "width": 3}}, {"data": {"id": "e25", "source": "object_type:PoDSchedule", "target": "object_type:PoD", "label": "APPLIES_TO", "relation": "APPLIES_TO", "attributes": {"group": "5.5 PoD 与活动关系", "description": "PoD排期作用于PoD", "source_lines": {"start": 462, "end": 462}}, "synthetic": false, "edgeColor": "#94a3b8", "lineStyle": "solid", "width": 3}}, {"data": {"id": "e26", "source": "object_type:Project", "target": "object_type:Crew", "label": "HAS", "relation": "HAS", "attributes": {"group": "5.6 施工执行关系", "description": "项目包含施工队", "source_lines": {"start": 466, "end": 466}}, "synthetic": false, "edgeColor": "#94a3b8", "lineStyle": "solid", "width": 3}}, {"data": {"id": "e27", "source": "object_type:Crew", "target": "object_type:WorkAssignment", "label": "EXECUTES", "relation": "EXECUTES", "attributes": {"group": "5.6 施工执行关系", "description": "施工队执行施工分配", "source_lines": {"start": 467, "end": 467}}, "synthetic": false, "edgeColor": "#94a3b8", "lineStyle": "solid", "width": 3}}, {"data": {"id": "e28", "source": "object_type:WorkAssignment", "target": "object_type:PoD", "label": "ASSIGNS", "relation": "ASSIGNS", "attributes": {"group": "5.6 施工执行关系", "description": "施工分配指向PoD", "source_lines": {"start": 468, "end": 468}}, "synthetic": false, "edgeColor": "#94a3b8", "lineStyle": "solid", "width": 3}}, {"data": {"id": "e29", "source": "object_type:WorkAssignment", "target": "object_type:Room", "label": "OCCURS_IN", "relation": "OCCURS_IN", "attributes": {"group": "5.6 施工执行关系", "description": "施工分配发生在机房", "source_lines": {"start": 469, "end": 469}}, "synthetic": false, "edgeColor": "#94a3b8", "lineStyle": "solid", "width": 3}}, {"data": {"id": "e30", "source": "object_type:WorkAssignment", "target": "object_type:PoDPosition", "label": "OCCURS_AT", "relation": "OCCURS_AT", "attributes": {"group": "5.6 施工执行关系", "description": "施工分配发生在落位", "source_lines": {"start": 470, "end": 470}}, "synthetic": false, "edgeColor": "#94a3b8", "lineStyle": "solid", "width": 3}}, {"data": {"id": "e31", "source": "object_type:PlacementPlan", "target": "object_type:PoD", "label": "APPLIES_TO", "relation": "APPLIES_TO", "attributes": {"group": "5.7 决策与解释关系", "description": "落位方案作用于PoD", "source_lines": {"start": 474, "end": 474}}, "synthetic": false, "edgeColor": "#94a3b8", "lineStyle": "solid", "width": 3}}, {"data": {"id": "e32", "source": "object_type:PlacementPlan", "target": "object_type:PoDPosition", "label": "REFERENCES", "relation": "REFERENCES", "attributes": {"group": "5.7 决策与解释关系", "description": "落位方案引用落位", "source_lines": {"start": 475, "end": 475}}, "synthetic": false, "edgeColor": "#94a3b8", "lineStyle": "solid", "width": 3}}, {"data": {"id": "e33", "source": "object_type:ConstraintViolation", "target": "object_type:PoD", "label": "REFERENCES", "relation": "REFERENCES", "attributes": {"group": "5.7 决策与解释关系", "description": "约束冲突关联PoD", "source_lines": {"start": 476, "end": 476}}, "synthetic": false, "edgeColor": "#94a3b8", "lineStyle": "solid", "width": 3}}, {"data": {"id": "e34", "source": "object_type:ConstraintViolation", "target": "object_type:RoomMilestone", "label": "REFERENCES", "relation": "REFERENCES", "attributes": {"group": "5.7 决策与解释关系", "description": "约束冲突关联机房里程碑", "source_lines": {"start": 477, "end": 477}}, "synthetic": false, "edgeColor": "#94a3b8", "lineStyle": "solid", "width": 3}}, {"data": {"id": "e35", "source": "object_type:ConstraintViolation", "target": "object_type:FloorMilestone", "label": "REFERENCES", "relation": "REFERENCES", "attributes": {"group": "5.7 决策与解释关系", "description": "约束冲突关联楼层里程碑", "source_lines": {"start": 478, "end": 478}}, "synthetic": false, "edgeColor": "#94a3b8", "lineStyle": "solid", "width": 3}}, {"data": {"id": "e36", "source": "object_type:DecisionRecommendation", "target": "object_type:ArrivalPlan", "label": "REFERENCES", "relation": "REFERENCES", "attributes": {"group": "5.7 决策与解释关系", "description": "决策建议引用到货方案", "source_lines": {"start": 479, "end": 479}}, "synthetic": false, "edgeColor": "#94a3b8", "lineStyle": "solid", "width": 3}}, {"data": {"id": "e37", "source": "object_type:DecisionRecommendation", "target": "object_type:PlacementPlan", "label": "REFERENCES", "relation": "REFERENCES", "attributes": {"group": "5.7 决策与解释关系", "description": "决策建议引用落位方案", "source_lines": {"start": 480, "end": 480}}, "synthetic": false, "edgeColor": "#94a3b8", "lineStyle": "solid", "width": 3}}, {"data": {"id": "e38", "source": "object_type:DecisionRecommendation", "target": "object_type:ConstraintViolation", "label": "REFERENCES", "relation": "REFERENCES", "attributes": {"group": "5.7 决策与解释关系", "description": "决策建议引用约束冲突", "source_lines": {"start": 481, "end": 481}}, "synthetic": false, "edgeColor": "#94a3b8", "lineStyle": "solid", "width": 3}}], "relationTypes": ["HAS", "CONSTRAINS", "AGGREGATES", "DELIVERS", "ASSIGNED_TO", "SHIPS", "APPLIES_TO", "GENERATES", "USES", "DEPENDS_ON", "DEFINES", "CONTAINS", "EXECUTES", "ASSIGNS", "OCCURS_IN", "OCCURS_AT", "REFERENCES"], "relationLegend": [{"relation": "HAS", "translation": "包含"}, {"relation": "CONSTRAINS", "translation": "约束"}, {"relation": "AGGREGATES", "translation": "聚合"}, {"relation": "DELIVERS", "translation": "交付"}, {"relation": "ASSIGNED_TO", "translation": "分配到"}, {"relation": "SHIPS", "translation": "运输"}, {"relation": "APPLIES_TO", "translation": "作用于"}, {"relation": "GENERATES", "translation": "生成"}, {"relation": "USES", "translation": "使用"}, {"relation": "DEPENDS_ON", "translation": "依赖"}, {"relation": "DEFINES", "translation": "定义"}, {"relation": "CONTAINS", "translation": "包含"}, {"relation": "EXECUTES", "translation": "执行"}, {"relation": "ASSIGNS", "translation": "指派给"}, {"relation": "OCCURS_IN", "translation": "发生于机房"}, {"relation": "OCCURS_AT", "translation": "发生于落位"}, {"relation": "REFERENCES", "translation": "引用"}], "metricGroupId": "metric_group:关键派生指标", "metricNodeIds": ["derived_metric:waiting_install_duration", "derived_metric:latest_safe_arrival_time", "derived_metric:earliest_useful_arrival_time", "derived_metric:arrival_delay_duration", "derived_metric:arrival_backlog_risk_level", "derived_metric:room_handover_completed_pod_count", "derived_metric:room_handover_completion_rate", "derived_metric:room_milestone_gap_pod_count", "derived_metric:floor_handover_completed_room_count", "derived_metric:floor_milestone_completion_rate", "derived_metric:floor_milestone_gap_room_count", "derived_metric:crew_daily_load", "derived_metric:crew_capacity_utilization", "derived_metric:room_daily_install_count", "derived_metric:floor_daily_install_count", "derived_metric:schedule_feasibility_flag", "derived_metric:placement_feasibility_flag", "derived_metric:milestone_risk_level"], "metricEdgeIds": ["metric_edge:1", "metric_edge:2", "metric_edge:3", "metric_edge:4", "metric_edge:5", "metric_edge:6", "metric_edge:7", "metric_edge:8", "metric_edge:9", "metric_edge:10", "metric_edge:11", "metric_edge:12", "metric_edge:13", "metric_edge:14", "metric_edge:15", "metric_edge:16", "metric_edge:17", "metric_edge:18"]};
    const relationFilter = document.getElementById('relation-filter');
    const floatingDetailCard = document.getElementById('floating-detail-card');
    const searchInput = document.getElementById('node-search');
    const searchButton = document.getElementById('search-button');
    const resetButton = document.getElementById('reset-view');
    const toggleMetricsButton = document.getElementById('toggle-metrics');
    const qaAssistantToggle = document.getElementById('qa-assistant-toggle');
    const qaAnswerPanel = document.getElementById('qa-answer-panel');
    const qaQuestionInput = document.getElementById('qa-question');
    const qaSubmitButton = document.getElementById('qa-submit');
    const qaStatusCard = document.getElementById('qa-status');
    const qaAnswerCard = document.getElementById('qa-answer');
    const qaEvidenceTimelineCard = document.getElementById('evidence-timeline');
    const qaStatusBody = qaStatusCard.querySelector('div:last-child');
    const qaAnswerBody = qaAnswerCard.querySelector('div:last-child');
    const qaEvidenceTimelineBody = qaEvidenceTimelineCard.querySelector('div:last-child');
    const defaultPanelHtml = "<div class=\"hero-card\"><div class=\"hero-title\">节点详情</div><div class=\"hero-subtitle\">点击左侧节点查看定义、属性和关系摘要。</div></div><div class=\"detail-card\"><div class=\"section-title\">关系摘要</div><p class=\"muted\">默认折叠，点击节点后可展开查看入边和出边详情。</p></div>";
    let qaEventSource = null;
    let persistedEvidenceChain = [];
    let persistedEvidenceMap = new Map();
    let evidenceSnapshots = new Map();
    let playbackController = null;

    relationFilter.innerHTML = ['<option value="all">全部关系</option>']
      .concat(graphPayload.relationTypes.map(item => `<option value="${item}">${item}</option>`))
      .join('');

    const cy = cytoscape({
      container: document.getElementById('cy'),
      elements: graphPayload.elements,
      layout: {
        name: 'cose',
        animate: false,
        randomize: false,
        fit: false,
        idealEdgeLength: 180,
        nodeRepulsion: 420000,
        edgeElasticity: 120,
        gravity: 0.25,
        nestingFactor: 1.1,
        numIter: 1600,
        initialTemp: 180,
        coolingFactor: 0.95
      },
      autoungrabify: true,
      boxSelectionEnabled: false,
      wheelSensitivity: 0.18,
      minZoom: 0.35,
      maxZoom: 2.2,
      style: [
        {
          selector: 'node',
          style: {
            'shape': 'round-rectangle',
            'background-color': 'data(color)',
            'label': 'data(label)',
            'text-wrap': 'wrap',
            'text-max-width': 150,
            'text-valign': 'center',
            'text-halign': 'center',
            'font-size': 11,
            'font-weight': 600,
            'color': '#0f172a',
            'padding': '12px',
            'width': 'label',
            'height': 'label',
            'border-width': 2,
            'border-color': '#1e293b',
            'shadow-blur': 18,
            'shadow-color': 'rgba(15, 23, 42, 0.15)',
            'shadow-opacity': 1,
            'shadow-offset-x': 0,
            'shadow-offset-y': 8
          }
        },
        {
          selector: 'edge',
          style: {
            'curve-style': 'bezier',
            'target-arrow-shape': 'triangle',
            'line-color': 'data(edgeColor)',
            'target-arrow-color': 'data(edgeColor)',
            'line-style': 'data(lineStyle)',
            'label': 'data(label)',
            'font-size': 10,
            'font-weight': 700,
            'text-rotation': 'autorotate',
            'text-background-color': '#ffffff',
            'text-background-opacity': 0.96,
            'text-background-padding': 3,
            'color': '#0f172a',
            'width': 'data(width)'
          }
        },
        { selector: '.metric-hidden', style: { display: 'none' } },
        { selector: '.filtered-hidden', style: { display: 'none' } },
        { selector: '.dimmed', style: { opacity: 0.12 } },
        { selector: '.trace-dimmed', style: { opacity: 0.12 } },
        { selector: '.highlighted', style: { opacity: 1, 'border-color': '#2563eb', 'border-width': 4 } },
        { selector: 'edge.highlighted', style: { 'line-color': '#2563eb', 'target-arrow-color': '#2563eb', 'width': 4 } },
        { selector: 'node.trace-path', style: { 'border-color': '#f97316', 'border-width': 4, 'shadow-color': 'rgba(249,115,22,0.35)', 'shadow-blur': 24, 'shadow-opacity': 1 } },
        { selector: 'edge.trace-path', style: { 'line-color': '#f97316', 'target-arrow-color': '#f97316', 'width': 5 } },
        { selector: 'node.searching-node', style: { 'border-color': '#38bdf8', 'border-width': 5, 'overlay-color': '#60a5fa', 'overlay-opacity': 0.18, 'overlay-padding': 12 } }
      ]
    });

    let metricsExpanded = false;

    function formatPropertyLines(values) {
      if (!Array.isArray(values) || values.length === 0) return '';
      return `<ul class="list">${values.map(item => {
        const value = String(item || '').trim();
        if (!value) return '';
        const separatorIndex = value.indexOf('：');
        if (separatorIndex === -1) {
          return `<li><strong>${value}</strong></li>`;
        }
        const key = value.slice(0, separatorIndex);
        const description = value.slice(separatorIndex + 1);
        return `<li><strong>${key}</strong>：${description}</li>`;
      }).join('')}</ul>`;
    }

    function formatStringList(values) {
      if (!Array.isArray(values) || values.length === 0) return '';
      return `<ul class="list">${values.map(item => {
        const value = String(item || '').trim();
        return value ? `<li>${value}</li>` : '';
      }).join('')}</ul>`;
    }

    function renderSection(title, bodyHtml, hasContent) {
      if (!hasContent) return ''; // if (!hasContent) return
      return `<div class="detail-card"><div class="section-title">${title}</div>${bodyHtml}</div>`;
    }

    function hasNamedList(values) {
      return Array.isArray(values) && values.length > 0;
    }

    function hasStringList(values) {
      return Array.isArray(values) && values.length > 0;
    }

    function renderRelations(title, relations) {
      if (!relations.length) return '';
      return `<div class="detail-card"><div class="section-title">${title}</div><ul class="list">${relations.map(item => `<li>${item}</li>`).join('')}</ul></div>`;
    }

    function showInlineDetailCard(node, htmlContent) {
      floatingDetailCard.innerHTML = htmlContent;
      floatingDetailCard.classList.remove('hidden');
      floatingDetailCard.style.visibility = 'hidden';
      const graphStage = document.querySelector('.graph-stage');
      const stageRect = graphStage.getBoundingClientRect();
      const cardRect = floatingDetailCard.getBoundingClientRect();
      const nodePos = node.renderedPosition();
      let left = nodePos.x + 28;
      let top = nodePos.y - cardRect.height / 2;
      if (left + cardRect.width > stageRect.width - 12) {
        left = nodePos.x - cardRect.width - 28;
      }
      if (left < 12) left = 12;
      if (top < 12) top = 12;
      if (top + cardRect.height > stageRect.height - 12) {
        top = stageRect.height - cardRect.height - 12;
      }
      floatingDetailCard.style.left = `${left}px`;
      floatingDetailCard.style.top = `${top}px`;
      floatingDetailCard.style.visibility = 'visible';
    }

    function hideInlineDetailCard() {
      floatingDetailCard.classList.add('hidden');
      floatingDetailCard.innerHTML = defaultPanelHtml;
    }

    function escapeHtml(value) {
      return String(value || '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
    }

    function setQaStatus(message) {
      qaStatusCard.classList.remove('hidden');
      qaStatusBody.textContent = message || '\u7b49\u5f85\u63d0\u95ee';
    }

    function setQaAnswer(message) {
      qaAnswerCard.classList.remove('hidden');
      qaAnswerBody.innerHTML = escapeHtml(message || '');
    }

    function clearTraceClasses() {
      cy.elements().removeClass('trace-path');
      cy.elements().removeClass('trace-dimmed');
      cy.elements().removeClass('searching-node');
      cy.elements().removeClass('highlighted');
      cy.elements().removeClass('dimmed');
    }

    function clearPlaybackTimers(controller) {
      if (!controller || !Array.isArray(controller.timers)) return;
      controller.timers.forEach(timer => window.clearTimeout(timer));
      controller.timers = [];
    }

    function clearQaPresentation() {
      setQaStatus('\u7b49\u5f85\u63d0\u95ee');
      qaAnswerCard.classList.add('hidden');
      qaAnswerBody.textContent = '\u7b49\u5f85\u56de\u7b54';
      qaEvidenceTimelineCard.classList.add('hidden');
      qaEvidenceTimelineBody.innerHTML = '\u7b49\u5f85\u68c0\u7d22';
      persistedEvidenceChain = [];
      persistedEvidenceMap = new Map();
      evidenceSnapshots = new Map();
      clearTraceClasses();
      clearPlaybackTimers(playbackController);
      if (playbackController) {
        playbackController.queue = [];
        playbackController.running = false;
        playbackController.traceProtocolSeen = false;
      }
    }

    function buildFocusCollection(nodeIds, edgeIds) {
      let collection = cy.collection();
      (nodeIds || []).forEach(id => {
        const node = cy.getElementById(id);
        if (node && node.length) collection = collection.union(node);
      });
      (edgeIds || []).forEach(id => {
        const edge = cy.getElementById(id);
        if (edge && edge.length) collection = collection.union(edge);
      });
      return collection;
    }

    function normalizeSnapshot(snapshot) {
      const nodeIds = Array.isArray(snapshot && snapshot.node_ids) ? snapshot.node_ids.filter(Boolean) : [];
      const edgeIds = Array.isArray(snapshot && snapshot.edge_ids) ? snapshot.edge_ids.filter(Boolean) : [];
      return { node_ids: [...new Set(nodeIds)], edge_ids: [...new Set(edgeIds)] };
    }

    function replayFromSnapshot(snapshot, options = {}) {
      const normalized = normalizeSnapshot(snapshot || {});
      clearTraceClasses();
      const collection = buildFocusCollection(normalized.node_ids, normalized.edge_ids);
      if (!collection.length) {
        cy.elements(':visible').removeClass('trace-dimmed');
        return normalized;
      }
      cy.elements(':visible').addClass('trace-dimmed');
      collection.removeClass('trace-dimmed');
      collection.addClass('trace-path');
      collection.nodes().addClass('searching-node');
      collection.addClass('highlighted');
      if (options.fit !== false) {
        cy.animate({
          fit: { eles: collection, padding: 90 },
          duration: typeof options.duration === 'number' ? options.duration : 320,
        });
      }
      window.setTimeout(() => {
        collection.removeClass('highlighted');
      }, typeof options.pulseDuration === 'number' ? options.pulseDuration : 360);
      return normalized;
    }

    function focusEvidence(nodeIds, edgeIds) {
      replayFromSnapshot({ node_ids: nodeIds || [], edge_ids: edgeIds || [] });
    }

    function buildEvidenceSnapshots(chain, searchTrace) {
      const snapshots = new Map();
      const seedNodeIds = Array.isArray(searchTrace && searchTrace.seed_node_ids) ? searchTrace.seed_node_ids : [];
      const expansionSteps = Array.isArray(searchTrace && searchTrace.expansion_steps) ? searchTrace.expansion_steps : [];
      const seedSnapshot = normalizeSnapshot({ node_ids: seedNodeIds, edge_ids: [] });
      let relationIndex = 0;
      let latestSnapshot = seedSnapshot;
      (chain || []).forEach(item => {
        let snapshot = latestSnapshot;
        if (item.kind === 'seed') {
          snapshot = seedSnapshot.node_ids.length ? seedSnapshot : normalizeSnapshot({ node_ids: item.node_ids || [], edge_ids: item.edge_ids || [] });
        } else if (item.kind === 'relation' && expansionSteps[relationIndex]) {
          const traceStep = expansionSteps[relationIndex];
          relationIndex += 1;
          snapshot = normalizeSnapshot({
            node_ids: traceStep.snapshot_node_ids || item.node_ids || [],
            edge_ids: traceStep.snapshot_edge_ids || item.edge_ids || [],
          });
        } else if (item && item.evidence_id) {
          snapshot = normalizeSnapshot({ node_ids: item.node_ids || [], edge_ids: item.edge_ids || [] });
        }
        latestSnapshot = snapshot;
        if (item && item.evidence_id) {
          snapshots.set(item.evidence_id, snapshot);
        }
      });
      return snapshots;
    }

    function renderEvidenceTimeline(chain) {
      qaEvidenceTimelineCard.classList.remove('hidden');
      if (!Array.isArray(chain) || chain.length === 0) {
        qaEvidenceTimelineBody.innerHTML = '<div class="muted">暂无证据</div>';
        return;
      }
      qaEvidenceTimelineBody.innerHTML = chain.map(item => {
        const reasons = Array.isArray(item.why_matched) && item.why_matched.length
          ? `<div style="margin-top:6px;color:#93c5fd;font-size:12px;">${item.why_matched.map(reason => escapeHtml(reason)).join('<br />')}</div>`
          : '';
        return `
          <button type="button" data-evidence-id="${escapeHtml(item.evidence_id)}" style="display:block;width:100%;text-align:left;background:rgba(30,41,59,0.9);border:1px solid rgba(148,163,184,0.28);border-radius:12px;color:#e2e8f0;padding:10px 12px;margin:0 0 10px 0;cursor:pointer;">
            <div style="font-weight:700;color:#bfdbfe;">[${escapeHtml(item.evidence_id)}] ${escapeHtml(item.label || item.kind || '\u8bc1\u636e')}</div>
            <div style="margin-top:4px;line-height:1.5;">${escapeHtml(item.message || '')}</div>
            ${reasons}
          </button>
        `;
      }).join('');
      qaEvidenceTimelineBody.querySelectorAll('[data-evidence-id]').forEach(button => {
        button.addEventListener('click', () => {
          const snapshot = evidenceSnapshots.get(button.dataset.evidenceId) || { node_ids: [], edge_ids: [] };
          replayFromSnapshot(snapshot, { fit: true, duration: 280, pulseDuration: 420 });
          setQaStatus(`\u56de\u653e\u8bc1\u636e ${button.dataset.evidenceId}`);
        });
      });
    }

    function appendEvidenceIncrementally(evidence) {
      if (!evidence || !evidence.evidence_id) return;
      persistedEvidenceMap.set(evidence.evidence_id, evidence);
      persistedEvidenceChain = Array.from(persistedEvidenceMap.values());
      renderEvidenceTimeline(persistedEvidenceChain);
    }

    function persistFinalEvidence(result) {
      persistedEvidenceChain = Array.isArray(result.evidence_chain) ? result.evidence_chain : [];
      persistedEvidenceMap = new Map(persistedEvidenceChain.map(item => [item.evidence_id, item]));
      evidenceSnapshots = buildEvidenceSnapshots(persistedEvidenceChain, result.search_trace || {});
      renderEvidenceTimeline(persistedEvidenceChain);
    }

    function playRetrievalEvent(eventType, payload) {
      const nodeIds = Array.isArray(payload.node_ids) ? payload.node_ids : [];
      const edgeIds = Array.isArray(payload.edge_ids) ? payload.edge_ids : [];
      if (payload.message) {
        setQaStatus(payload.message);
      }
      if (['anchor_node', 'expand_neighbors', 'filter_nodes', 'focus_subgraph'].includes(eventType)) {
        focusEvidence(nodeIds, edgeIds);
        return;
      }
      if (eventType === 'evidence' && payload.evidence) {
        appendEvidenceIncrementally(payload.evidence);
        focusEvidence(nodeIds, edgeIds);
      }
    }

    class PlaybackController {
      constructor(cyInstance) {
        this.cy = cyInstance;
        this.queue = [];
        this.running = false;
        this.timers = [];
        this.traceProtocolSeen = false;
      }

      enqueue(eventType, payload) {
        if (['trace_anchor', 'trace_expand', 'evidence_final'].includes(eventType)) {
          this.traceProtocolSeen = true;
        }
        this.queue.push({ eventType, payload });
        if (!this.running) {
          this.drain();
        }
      }

      drain() {
        if (!this.queue.length) {
          this.running = false;
          return;
        }
        this.running = true;
        const item = this.queue.shift();
        this.play(item.eventType, item.payload);
        const delay = ['trace_anchor', 'trace_expand'].includes(item.eventType)
          ? Math.max(Number(item.payload && item.payload.delay_ms) || 0, 0)
          : 0;
        const timer = window.setTimeout(() => this.drain(), delay);
        this.timers.push(timer);
      }

      play(eventType, payload) {
        if (payload && payload.message) {
          setQaStatus(payload.message);
        }
        if (eventType === 'trace_anchor') {
          replayFromSnapshot({ node_ids: payload.node_ids || [], edge_ids: payload.edge_ids || [] }, { fit: true, duration: 340 });
          return;
        }
        if (eventType === 'trace_expand') {
          replayFromSnapshot({
            node_ids: payload.snapshot_node_ids || payload.node_ids || [],
            edge_ids: payload.snapshot_edge_ids || payload.edge_ids || [],
          }, { fit: true, duration: 340, pulseDuration: 420 });
          return;
        }
        if (eventType === 'evidence_final') {
          persistFinalEvidence(payload || {});
          return;
        }
        if (eventType === 'answer_done') {
          if (!this.traceProtocolSeen) {
            persistFinalEvidence(payload || {});
          }
          setQaAnswer(payload.answer || '');
        }
      }
    }

    function startQaStream(question) {
      const trimmedQuestion = String(question || '').trim();
      if (!trimmedQuestion) return;
      qaAnswerPanel.classList.remove('hidden');
      if (qaEventSource) {
        qaEventSource.close();
        qaEventSource = null;
      }
      if (!playbackController) {
        playbackController = new PlaybackController(cy);
      }
      clearQaPresentation();
      setQaStatus('\u6b63\u5728\u68c0\u7d22\u672c\u4f53\u8bc1\u636e...');
      const eventSource = new EventSource(`/api/qa/stream?q=${encodeURIComponent(trimmedQuestion)}`);
      qaEventSource = eventSource;
      ['trace_anchor', 'trace_expand', 'evidence_final', 'answer_done'].forEach(eventType => {
        eventSource.addEventListener(eventType, event => {
          const payload = JSON.parse(event.data);
          playbackController.enqueue(eventType, payload);
          if (eventType === 'answer_done') {
            eventSource.close();
            if (qaEventSource === eventSource) {
              qaEventSource = null;
            }
          }
        });
      });
      ['anchor_node', 'expand_neighbors', 'filter_nodes', 'focus_subgraph', 'evidence'].forEach(eventType => {
        eventSource.addEventListener(eventType, event => {
          const payload = JSON.parse(event.data);
          if (playbackController && playbackController.traceProtocolSeen) {
            return;
          }
          playRetrievalEvent(eventType, payload);
        });
      });
      eventSource.addEventListener('error', () => {
        setQaStatus('\u95ee\u7b54\u6d41\u5df2\u4e2d\u65ad');
        eventSource.close();
        if (qaEventSource === eventSource) {
          qaEventSource = null;
        }
      });
    }

    function visibleBusinessEdgesFor(nodeId, direction) {
      return cy.edges().filter(edge => {
        if (edge.data('synthetic')) return false;
        if (edge.style('display') === 'none') return false;
        return direction === 'in' ? edge.target().id() === nodeId : edge.source().id() === nodeId;
      });
    }

    function relationLinesFor(nodeId, direction) {
      return visibleBusinessEdgesFor(nodeId, direction).map(edge => {
        const src = edge.source().data('display_name');
        const dst = edge.target().data('display_name');
        return `${src} ${edge.data('relation')} ${dst}`;
      });
    }

    function renderNodeDetails(node) {
      const data = node.data();
      const attrs = data.attributes || {};
      const inRelations = relationLinesFor(node.id(), 'in');
      const outRelations = relationLinesFor(node.id(), 'out');
      const relationTypes = [...new Set(
        cy.edges().filter(edge => !edge.data('synthetic') && (edge.source().id() === node.id() || edge.target().id() === node.id()))
          .map(edge => edge.data('relation'))
      )].sort();
      const hasRelationSummary = relationTypes.length > 0 || inRelations.length > 0 || outRelations.length > 0;
      const relationSummaryHtml = hasRelationSummary
        ? `<div class="detail-card"><div class="section-title">关系摘要</div><div class="summary-box"><strong>入边：</strong>${inRelations.length} &nbsp; <strong>出边：</strong>${outRelations.length}</div><div style="height:8px"></div><div class="pill-row">${relationTypes.length ? relationTypes.map(item => `<span class="pill">${item}</span>`).join('') : '<span class="muted">无</span>'}</div><div class="actions"><button id="toggle-relations">展开关系明细</button></div></div><div id="relation-details" class="hidden">${renderRelations('入边明细', inRelations)}${renderRelations('出边明细', outRelations)}</div>`
        : '';
      const htmlContent = `
        <div class="hero-card">
          <div class="hero-title">${data.display_name}</div>
          <div class="hero-subtitle">
            <span class="type-chip">${data.type}</span>
            <span class="group-chip">${attrs.display_group || '未分组'}</span>
          </div>
        </div>
        ${renderSection('中文释义', `<p class="detail-text">${attrs.chinese_description || attrs.description}</p>`, Boolean(attrs.chinese_description || attrs.description))}
        ${renderSection('语义定义', `<p class="detail-text">${attrs.semantic_definition}</p>`, Boolean(attrs.semantic_definition))}
        ${renderSection('关键属性', formatPropertyLines(attrs.key_property_lines || []), hasStringList(attrs.key_property_lines))}
        ${renderSection('状态建议', formatPropertyLines(attrs.status_value_lines || []), hasStringList(attrs.status_value_lines))}
        ${renderSection('规则约束', formatStringList(attrs.rule_lines || attrs.rules || []), hasStringList(attrs.rule_lines || attrs.rules))}
        ${renderSection('说明', formatStringList(attrs.note_lines || attrs.notes || []), hasStringList(attrs.note_lines || attrs.notes))}
        ${relationSummaryHtml}
      `;
      showInlineDetailCard(node, htmlContent);
      const button = document.getElementById('toggle-relations');
      if (button) {
        button.addEventListener('click', () => {
          const details = document.getElementById('relation-details');
          details.classList.toggle('hidden');
          button.textContent = details.classList.contains('hidden') ? '展开关系明细' : '收起关系明细';
        });
      }
    }

    function renderMetricGroupDetails(node) {
      const attrs = node.data('attributes') || {};
      const htmlContent = `
        <div class="hero-card">
          <div class="hero-title">关键派生指标</div>
          <div class="hero-subtitle">点击图中该节点可原地展开/收起详细指标。</div>
        </div>
        ${renderSection('说明', `<p class="detail-text">${attrs.description}</p>`, Boolean(attrs.description))}
        ${renderSection('指标列表', formatStringList(attrs.metric_names || []), hasStringList(attrs.metric_names))}
      `;
      showInlineDetailCard(node, htmlContent);
    }

    function toggleMetricNodes(forceState) {
      metricsExpanded = typeof forceState === 'boolean' ? forceState : !metricsExpanded;
      graphPayload.metricNodeIds.forEach(id => {
        const node = cy.getElementById(id);
        if (node) node.style('display', metricsExpanded ? 'element' : 'none');
      });
      graphPayload.metricEdgeIds.forEach(id => {
        const edge = cy.getElementById(id);
        if (edge) edge.style('display', metricsExpanded ? 'element' : 'none');
      });
    }

    function applyRelationFilter() {
      const relation = relationFilter.value;
      cy.edges().forEach(edge => {
        if (edge.data('synthetic')) {
          edge.style('display', metricsExpanded ? 'element' : 'none');
          return;
        }
        const visible = relation === 'all' || edge.data('relation') === relation;
        edge.style('display', visible ? 'element' : 'none');
      });

      cy.nodes().forEach(node => {
        if (node.id() === graphPayload.metricGroupId) {
          node.style('display', 'element');
          return;
        }
        if (graphPayload.metricNodeIds.includes(node.id())) {
          node.style('display', metricsExpanded ? 'element' : 'none');
          return;
        }
        const connectedVisible = node.connectedEdges().some(edge => !edge.data('synthetic') && edge.style('display') !== 'none');
        node.style('display', relation === 'all' || connectedVisible ? 'element' : 'none');
      });
    }

    function highlightNode(node) {
      cy.elements().removeClass('highlighted');
      cy.elements().removeClass('dimmed');
      const neighborhood = node.closedNeighborhood();
      cy.elements(':visible').addClass('dimmed');
      neighborhood.removeClass('dimmed');
      neighborhood.addClass('highlighted');
      cy.fit(neighborhood, 90);
    }

    cy.on('tap', 'node', event => {
      const node = event.target;
      if (node.id() === graphPayload.metricGroupId) {
        toggleMetricNodes();
        applyRelationFilter();
        highlightNode(node);
        renderMetricGroupDetails(node);
        return;
      }
      highlightNode(node);
      renderNodeDetails(node);
    });

    cy.on('tap', event => {
      if (event.target === cy) {
        cy.elements().removeClass('highlighted');
        cy.elements().removeClass('dimmed');
        hideInlineDetailCard();
      }
    });

    relationFilter.addEventListener('change', () => {
      applyRelationFilter();
      cy.fit(cy.elements(':visible'), 70);
    });

    searchButton.addEventListener('click', () => {
      const query = searchInput.value.trim().toLowerCase();
      if (!query) return;
      const match = cy.nodes().find(node => (node.data('search_text') || '').includes(query));
      if (match) {
        if (graphPayload.metricNodeIds.includes(match.id())) {
          toggleMetricNodes(true);
          applyRelationFilter();
        }
        highlightNode(match);
        if (match.id() === graphPayload.metricGroupId) {
          renderMetricGroupDetails(match);
        } else {
          renderNodeDetails(match);
        }
      }
    });

    toggleMetricsButton.addEventListener('click', () => {
      toggleMetricNodes();
      applyRelationFilter();
      cy.fit(cy.elements(':visible'), 70);
    });

    resetButton.addEventListener('click', () => {
      relationFilter.value = 'all';
      searchInput.value = '';
      cy.elements().removeClass('highlighted');
      cy.elements().removeClass('dimmed');
      if (qaEventSource) {
        qaEventSource.close();
        qaEventSource = null;
      }
      toggleMetricNodes(false);
      applyRelationFilter();
      hideInlineDetailCard();
      cy.fit(cy.elements(':visible'), 70);
    });

    qaAssistantToggle.addEventListener('click', () => {
      qaAnswerPanel.classList.toggle('hidden');
    });

    qaSubmitButton.addEventListener('click', () => {
      startQaStream(qaQuestionInput.value);
    });

    qaQuestionInput.addEventListener('keydown', event => {
      if ((event.ctrlKey || event.metaKey) && event.key === 'Enter') {
        startQaStream(qaQuestionInput.value);
      }
    });

    cy.ready(() => {
      toggleMetricNodes(false);
      applyRelationFilter();
      clearQaPresentation();
      cy.fit(cy.elements(':visible'), 70);
    });
  