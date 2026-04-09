# QA Panel Tabs and Clean Trace Design

**Date:** 2026-04-08

## Goal
围绕当前实例问答页面，只落地两件事：
1. 将右侧 QA 面板改为 `答案摘要 / 关键证据 / 图谱定位` 三个 tab。
2. 继续收紧用户态展示，避免重新回到调试台风格。

## Decision
采用单面板三 tab 方案，不新增弹层，不拆新页面，不改后端主链路。

默认行为：
- 用户发起问答后默认停留在 `答案摘要`
- `关键证据` 以实例卡片方式展示命中的关键对象
- `图谱定位` 提供可点击证据对象/路径，点击后联动高亮图谱

## Scope
本次只处理前端展示层与最小必要的数据映射：
- 复用现有 `/api/qa/stream`
- 复用现有 `trace_summary`
- 复用现有 evidence timeline / graph focus 能力
- 不新增 TypeDB 查询类型
- 不改最终问答链路协议的主结构

## UX Structure
### Tab 1: 答案摘要
展示：
- 最终回答文本
- 回答状态（AI总结 / 基础回答）

约束：
- 不显示 TypeQL
- 不显示 query plan
- 不显示错误堆栈

### Tab 2: 关键证据
展示：
- 关键实例卡片
- 每张卡片只展示：实体、实例ID、少量关键属性、证据标签
- 支持显示 `其余 N 条已折叠`

数据来源优先级：
1. `trace_summary.compact.key_evidence`
2. `trace_summary.expanded.detailed_evidence`
3. 必要时辅以 `fact_pack` 做实例字段补足

### Tab 3: 图谱定位
展示：
- 可点击证据对象列表
- 可点击关键路径列表

交互：
- 点击对象或路径后，调用现有图谱聚焦/高亮逻辑
- 同步状态栏，提示当前定位对象
- 不额外展示底层调试信息

## Clean Trace Constraint
用户态只允许出现：
- 问题理解
- 关键证据
- 数据缺口
- 结论依据
- 详细证据对象
- 关键路径

用户态禁止出现：
- TypeQL
- row_count
- query plan
- typedb_query 原文
- stack trace
- rows=0 日志

## Frontend Data Mapping
### 答案摘要 tab
- 来自 `answer_done.answer_text` / `answer_done.answer`
- 若 `used_fallback=true`，展示 `基础回答`
- 否则展示 `AI总结`

### 关键证据 tab
- 从 `trace_summary.compact.key_evidence.direct_hits` 生成摘要卡片
- 从 `trace_summary.expanded.detailed_evidence` 生成详情卡片
- 统一字段映射为：
  - `entity`
  - `label`
  - `instance_id`
  - `attrs[]`
  - `impact_tag`

### 图谱定位 tab
- 使用 `trace_summary.expanded.key_paths`
- 使用现有 `findNodeIdsForEntityNames(...)` / `findEdgeIdsForRelationTriples(...)` / `replayFromSnapshot(...)`
- 若路径无法精确映射边，至少回退到节点级定位

## Testing Strategy
1. HTML shell 层测试
- tab 按钮存在
- tab 容器存在
- 默认 tab 为 `答案摘要`

2. 前端脚本测试
- 存在 tab 切换函数
- 存在 evidence card 渲染函数
- 存在 graph focus 入口
- 不再依赖旧的整块 trace 文本渲染作为主展示

3. 回归测试
- 页面 JS 仍可通过 `node --check`
- 现有 trace summary SSE 流程不回退
- 图谱高亮相关函数仍可复用

## Acceptance Criteria
- QA 面板出现三个 tab：`答案摘要 / 关键证据 / 图谱定位`
- 默认打开 `答案摘要`
- `关键证据` 以卡片而非大段文本展示
- `图谱定位` 点击后可触发图谱聚焦
- 用户态不出现 TypeQL / query log / stack trace
- 现有 SSE 流程和测试保持通过
