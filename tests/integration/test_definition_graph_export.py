from pathlib import Path

from cloud_delivery_ontology_palantir.export.graph_export import export_interactive_graph_html
from cloud_delivery_ontology_palantir.models.ontology import OntologyGraph, OntologyObject, OntologyRelation



def test_exported_html_uses_edge_friendly_non_lane_layout(tmp_path: Path):
    graph = OntologyGraph(metadata={'title': '本体建模 v2', 'mainline': ['Project', 'Building', 'PoD']})
    graph.add_object(
        OntologyObject(
            id='object_type:Project',
            type='ObjectType',
            name='Project',
            attributes={
                'group': '4.1 项目与目标层',
                'semantic_definition': '',
                'key_properties': [{'name': 'project_id', 'description': '项目ID'}],
            },
        )
    )
    graph.add_object(
        OntologyObject(
            id='object_type:Building',
            type='ObjectType',
            name='Building',
            attributes={
                'group': '4.2 空间层',
                'semantic_definition': '',
                'key_properties': [{'name': 'building_id', 'description': '大楼ID'}],
            },
        )
    )
    graph.add_object(
        OntologyObject(
            id='object_type:PoD',
            type='ObjectType',
            name='PoD',
            attributes={
                'group': '4.3 设备与物流层',
                'semantic_definition': '',
                'key_properties': [{'name': 'pod_id', 'description': 'PoD ID'}],
            },
        )
    )
    graph.add_object(
        OntologyObject(
            id='derived_metric:latest_safe_arrival_time',
            type='DerivedMetric',
            name='latest_safe_arrival_time',
            attributes={
                'group': '6. 关键派生指标',
                'description': '最晚安全到货时间',
            },
        )
    )
    graph.add_relation(
        OntologyRelation(
            source_id='object_type:Project',
            target_id='object_type:Building',
            relation='HAS',
            attributes={'description': '项目包含大楼'},
        )
    )
    graph.add_relation(
        OntologyRelation(
            source_id='object_type:Building',
            target_id='object_type:PoD',
            relation='HAS',
            attributes={'description': '大楼关联PoD'},
        )
    )

    output = export_interactive_graph_html(graph, tmp_path / 'ontology.html', title='Ontology Graph')
    text = output.read_text(encoding='utf-8')

    assert 'project_id' in text
    assert '关系摘要' in text
    assert 'HAS：包含' in text
    assert '关键派生指标' in text
    assert 'autoungrabify: true' in text
    assert "name: 'cose'" in text
    assert 'cdn.jsdelivr.net/npm/cytoscape' not in text
    assert 'window.cytoscape = window.cytoscape || cytoscape' in text
    assert 'lane-guide' not in text
    assert 'renderSection' in text
    assert '"label": "Project\\n' in text
    assert '"label": "Project\\n4.1 ' not in text


def test_exported_html_uses_inline_floating_detail_card_and_hides_empty_sections(tmp_path: Path):
    graph = OntologyGraph(metadata={'title': '本体建模 v2'})
    graph.add_object(
        OntologyObject(
            id='object_type:Project',
            type='ObjectType',
            name='Project',
            attributes={
                'group': '4.1 项目与目标层',
                'semantic_definition': '',
                'key_properties': [{'name': 'project_id', 'description': '项目ID'}],
                'notes': [],
                'rules': [],
                'status_values': [],
            },
        )
    )
    output = export_interactive_graph_html(graph, tmp_path / 'ontology.html', title='Ontology Graph')
    text = output.read_text(encoding='utf-8')

    assert 'floating-detail-card' in text
    assert 'showInlineDetailCard' in text
    assert 'if (!hasContent) return' in text
    assert 'hideInlineDetailCard' in text



def test_exported_html_contains_qa_assistant_shell(tmp_path: Path):
    graph = OntologyGraph(metadata={'title': '本体建模 v2'})
    output = export_interactive_graph_html(graph, tmp_path / 'ontology.html', title='Ontology Graph')
    text = output.read_text(encoding='utf-8')
    assert '智能问答助手' in text
    assert '仅基于当前本体系统回答' in text
    assert 'qa-assistant-toggle' in text
    assert 'qa-answer-panel' in text



def test_exported_html_uses_clean_chinese_labels_in_detail_templates(tmp_path: Path):
    graph = OntologyGraph(metadata={'title': '本体建模 v2'})
    graph.add_object(
        OntologyObject(
            id='object_type:Project',
            type='ObjectType',
            name='Project',
            attributes={
                'group': '4.1 项目与目标层',
                'chinese_description': '项目。',
                'semantic_definition': '定义文本',
                'key_properties': [{'name': 'project_id', 'description': '项目ID'}],
            },
        )
    )
    output = export_interactive_graph_html(graph, tmp_path / 'ontology.html', title='Ontology Graph')
    text = output.read_text(encoding='utf-8')
    assert '中文释义' in text
    assert '语义定义' in text
    assert '说明' in text
    assert 'project_id：项目ID' in text
    assert '????' not in text
    assert '>?</p>' not in text



def test_exported_html_contains_sse_qa_hooks_and_evidence_clickback(tmp_path: Path):
    graph = OntologyGraph(metadata={'title': '本体建模 v2'})
    output = export_interactive_graph_html(graph, tmp_path / 'ontology.html', title='Ontology Graph')
    text = output.read_text(encoding='utf-8')

    assert 'EventSource' in text
    assert 'playRetrievalEvent' in text
    assert 'startQaStream' in text
    assert 'renderEvidenceTimeline' in text
    assert 'replayFromSnapshot' in text
    assert 'PlaybackController' in text
    assert 'evidence-timeline' in text
    assert 'trace_anchor' in text
    assert 'trace_expand' in text


def test_exported_html_renders_evidence_timeline_markup_not_legacy_chain_id(tmp_path: Path):
    graph = OntologyGraph(metadata={'title': '???? v2'})
    output = export_interactive_graph_html(graph, tmp_path / 'ontology.html', title='Ontology Graph')
    text = output.read_text(encoding='utf-8')

    assert 'id="qa-focus-playback"' in text
    assert 'id="qa-evidence-chain"' not in text


def test_exported_html_contains_trace_playback_controller_and_timeline(tmp_path: Path):
    graph = OntologyGraph(metadata={'title': '本体建模 v2'})
    output = export_interactive_graph_html(graph, tmp_path / 'ontology.html', title='Ontology Graph')
    text = output.read_text(encoding='utf-8')

    assert 'EventSource' in text
    assert 'PlaybackController' in text
    assert 'startQaStream' in text
    assert 'replayFromSnapshot' in text
    assert 'evidence-timeline' in text
    assert 'searching-node' in text
    assert 'trace-path' in text
    assert 'trace-dimmed' in text
    assert 'trace_anchor' in text
    assert 'trace_expand' in text
    assert 'evidence_final' in text


def test_exported_html_contains_trace_reset_mode_controls(tmp_path: Path):
    graph = OntologyGraph(metadata={'title': 'Ontology v2'})
    output = export_interactive_graph_html(graph, tmp_path / 'ontology.html', title='Ontology Graph')
    text = output.read_text(encoding='utf-8')

    assert 'filtering-active' in text
    assert 'resetToExplorationMode' in text
    assert 'trace-reset-button' in text
    assert 'currentSnapshot' in text
    assert 'event.target === cy' in text
    assert 'max-width: 280px' in text
    assert 'font-size: 12px' in text


def test_exported_html_contains_node_relative_detail_card_positioning(tmp_path: Path):
    graph = OntologyGraph(metadata={'title': 'Ontology v2'})
    output = export_interactive_graph_html(graph, tmp_path / 'ontology.html', title='Ontology Graph')
    text = output.read_text(encoding='utf-8')

    assert 'max-width: 280px' in text
    assert 'font-size: 12px' in text
    assert 'activeDetailNode.renderedPosition()' in text
    assert 'let left = pos.x + 20' in text
    assert 'let top = pos.y - 20' in text
    assert 'left = Math.max(12, Math.min(left, maxLeft));' in text
    assert 'top = Math.max(12, Math.min(top, maxTop));' in text



def test_exported_html_repositions_detail_card_on_viewport_changes(tmp_path: Path):
    graph = OntologyGraph(metadata={'title': 'Ontology v2'})
    output = export_interactive_graph_html(graph, tmp_path / 'ontology.html', title='Ontology Graph')
    text = output.read_text(encoding='utf-8')

    assert 'let activeDetailNode = null' in text
    assert 'function repositionDetailCard()' in text
    assert "requestAnimationFrame(() => {" in text
    assert "cy.on('pan zoom resize', repositionDetailCard);" in text
    assert 'activeDetailNode = node;' in text
    assert 'activeDetailNode = null;' in text
    assert 'repositionDetailCard();' in text
    assert 'cy.fit(neighborhood, 90);' not in text





def test_exported_html_contains_qa_tabs_and_defaults_to_answer_summary(tmp_path: Path):
    graph = OntologyGraph(metadata={'title': 'Ontology'})
    output = export_interactive_graph_html(graph, tmp_path / 'ontology.html', title='Ontology Graph')
    text = output.read_text(encoding='utf-8')

    assert 'qa-tab-answer' in text
    assert 'qa-tab-evidence' in text
    assert 'qa-tab-focus' in text
    assert 'qa-panel-answer' in text
    assert 'qa-panel-evidence' in text
    assert 'qa-panel-focus' in text
    assert 'setQaActiveTab' in text


def test_exported_html_routes_answer_text_to_answer_tab_only(tmp_path: Path):
    graph = OntologyGraph(metadata={'title': 'Ontology'})
    output = export_interactive_graph_html(graph, tmp_path / 'ontology.html', title='Ontology Graph')
    text = output.read_text(encoding='utf-8')

    assert 'qa-answer-mode' in text
    assert 'qa-answer-insights' in text
    assert 'renderAnswerInsights' in text
    assert 'setQaAnswerTabState' in text
    assert 'used_fallback' in text
    assert 'qa-trace-report' not in text


def test_exported_html_renders_instance_evidence_cards_from_trace_summary(tmp_path: Path):
    graph = OntologyGraph(metadata={'title': 'Ontology'})
    output = export_interactive_graph_html(graph, tmp_path / 'ontology.html', title='Ontology Graph')
    text = output.read_text(encoding='utf-8')

    assert 'renderEvidenceCards' in text
    assert 'qa-evidence-cards' in text
    assert 'evidence-card' in text
    assert 'evidence-card-attrs' in text
    assert 'evidence-card-tag' in text


def test_exported_html_contains_focus_tab_and_retrieval_playback(tmp_path: Path):
    graph = OntologyGraph(metadata={'title': 'Ontology'})
    output = export_interactive_graph_html(graph, tmp_path / 'ontology.html', title='Ontology Graph')
    text = output.read_text(encoding='utf-8')

    assert 'qa-focus-list' in text
    assert 'renderFocusTargets' in text
    assert 'focusTraceTarget' in text
    assert 'qa-focus-playback' in text


def test_exported_html_contains_focus_playback_controls(tmp_path: Path):
    graph = OntologyGraph(metadata={'title': 'Ontology'})
    output = export_interactive_graph_html(graph, tmp_path / 'ontology.html', title='Ontology Graph')
    text = output.read_text(encoding='utf-8')

    assert 'qa-playback-prev' in text
    assert 'qa-playback-next' in text
    assert 'qa-playback-replay' in text
    assert 'qa-playback-current' in text


def test_exported_html_focus_playback_uses_schema_retrieval_only(tmp_path: Path):
    graph = OntologyGraph(metadata={'title': 'Ontology'})
    output = export_interactive_graph_html(graph, tmp_path / 'ontology.html', title='Ontology Graph')
    text = output.read_text(encoding='utf-8')

    assert 'buildSchemaRetrievalPlaybackSteps' in text
    assert 'evidence_bundle_ready' in text
    assert 'typedb_result' not in text.split('function buildSchemaRetrievalPlaybackSteps', 1)[1][:1800]


def test_exported_html_instance_qa_stage_events_do_not_auto_play_graph_focus(tmp_path: Path):
    graph = OntologyGraph(metadata={'title': 'Ontology'})
    output = export_interactive_graph_html(graph, tmp_path / 'ontology.html', title='Ontology Graph')
    text = output.read_text(encoding='utf-8')

    assert 'function handleInstanceQaStageEvent' in text
    assert 'setFocusPlaybackIndex(playbackIndex' not in text.split('function handleInstanceQaStageEvent', 1)[1][:3200]


def test_exported_html_prefers_live_trace_stream_over_synthetic_schema_playback(tmp_path: Path):
    graph = OntologyGraph(metadata={'title': 'Ontology'})
    output = export_interactive_graph_html(graph, tmp_path / 'ontology.html', title='Ontology Graph')
    text = output.read_text(encoding='utf-8')

    assert 'traceProtocolSeen' in text
    assert '!playbackController || !playbackController.traceProtocolSeen' in text


def test_exported_html_focus_playback_keeps_entity_retrieval_wording(tmp_path: Path):
    graph = OntologyGraph(metadata={'title': 'Ontology'})
    output = export_interactive_graph_html(graph, tmp_path / 'ontology.html', title='Ontology Graph')
    text = output.read_text(encoding='utf-8').lower()

    assert 'qa-focus-playback' in text
    assert 'trace_anchor' in text
    assert 'trace_expand' in text
    assert 'query plan' not in text
    assert 'stack trace' not in text


def test_exported_html_keeps_user_trace_clean_without_debug_payload_sections(tmp_path: Path):
    graph = OntologyGraph(metadata={'title': 'Ontology'})
    output = export_interactive_graph_html(graph, tmp_path / 'ontology.html', title='Ontology Graph')
    text = output.read_text(encoding='utf-8').lower()

    assert 'typeql:' not in text
    assert 'row_count' not in text
    assert 'query plan' not in text
    assert 'stack trace' not in text

def test_exported_html_contains_streaming_answer_and_trace_sections(tmp_path: Path):
    graph = OntologyGraph(metadata={'title': 'ontology'})
    output = export_interactive_graph_html(graph, tmp_path / 'ontology.html', title='Ontology Graph')
    text = output.read_text(encoding='utf-8')

    assert 'answer_delta' in text
    assert 'trace_summary_ready' in text
    assert 'answer_text_so_far' in text
    assert 'qa-answer-text' in text
    assert 'qa-answer-insights' in text
    assert 'qa-focus-playback' in text


def test_exported_html_uses_generating_then_generated_answer_status_copy(tmp_path: Path):
    graph = OntologyGraph(metadata={'title': 'Ontology'})
    output = export_interactive_graph_html(graph, tmp_path / 'ontology.html', title='Ontology Graph')
    text = output.read_text(encoding='utf-8')

    assert "setQaStatus('\u6b63\u5728\u751f\u6210\u56de\u7b54\u6458\u8981')" in text
    assert "setQaStatus('\u5df2\u751f\u6210\u56de\u7b54\u6458\u8981')" in text





def test_exported_html_prefers_structured_summary_sections_over_debug_log_text(tmp_path: Path):
    graph = OntologyGraph(metadata={'title': 'Ontology'})
    output = export_interactive_graph_html(graph, tmp_path / 'ontology.html', title='Ontology Graph')
    text = output.read_text(encoding='utf-8')

    assert 'renderAnswerInsights' in text
    assert 'renderEvidenceCards' in text
    assert 'renderFocusTargets' in text
    assert 'typeql:' not in text


def test_build_graph_payload_does_not_append_group_text_for_ungrouped_object_type():
    from cloud_delivery_ontology_palantir.export.graph_export import build_graph_payload

    graph = OntologyGraph(metadata={'title': 'Ontology'})
    graph.add_object(
        OntologyObject(
            id='object_type:Project',
            type='ObjectType',
            name='Project',
            attributes={
                'group': '',
                'semantic_definition': '',
                'key_properties': [{'name': 'project_id', 'description': 'Project ID'}],
            },
        )
    )

    payload = build_graph_payload(graph)
    project = next(item for item in payload['elements'] if item['data']['id'] == 'object_type:Project')

    assert project['data']['label'] == 'Project'
    assert project['data']['attributes']['display_group'] == ''



def test_exported_html_hides_group_chip_for_ungrouped_object_type(tmp_path: Path):
    graph = OntologyGraph(metadata={'title': 'Ontology'})
    graph.add_object(
        OntologyObject(
            id='object_type:Project',
            type='ObjectType',
            name='Project',
            attributes={
                'group': '',
                'chinese_description': '??',
                'semantic_definition': '',
                'key_properties': [{'name': 'project_id', 'description': '??ID'}],
            },
        )
    )

    output = export_interactive_graph_html(graph, tmp_path / 'ontology.html', title='Ontology Graph')
    text = output.read_text(encoding='utf-8')

    assert 'const groupChipHtml = attrs.display_group ?' in text
    assert "<span class=\"group-chip\">${attrs.display_group}</span>" in text
    assert 'attrs.display_group ||' not in text
    assert '"label": "Project"' in text
    assert '"label": "Project\\n' not in text



def test_exported_html_contains_instance_qa_stage_handlers(tmp_path: Path):
    graph = OntologyGraph(metadata={'title': 'Ontology'})
    output = export_interactive_graph_html(graph, tmp_path / 'ontology.html', title='Ontology Graph')
    text = output.read_text(encoding='utf-8')

    assert 'question_parsed' in text
    assert 'question_dsl' in text
    assert 'fact_query_planned' in text
    assert 'typedb_query' in text
    assert 'typedb_result' in text
    assert 'reasoning_done' in text
    assert 'trace_summary_ready' in text
    assert 'handleInstanceQaStageEvent' in text
    assert 'renderAnswerInsights' in text
    assert 'renderInstanceQaTraceReport' not in text



def test_exported_html_embeds_javascript_without_syntax_error(tmp_path: Path):
    import re
    import subprocess
    import sys

    graph = OntologyGraph(metadata={'title': 'Ontology'})
    output = export_interactive_graph_html(graph, tmp_path / 'ontology.html', title='Ontology Graph')
    html = output.read_text(encoding='utf-8')
    scripts = re.findall(r'<script>(.*?)</script>', html, flags=re.S)
    script = scripts[-1]
    script_path = tmp_path / 'page-script.js'
    script_path.write_text(script, encoding='utf-8')

    result = subprocess.run(
        ['node', '--check', str(script_path)],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr


def test_exported_html_uses_clean_qa_copy_and_formats_answer_text(tmp_path: Path):
    graph = OntologyGraph(metadata={'title': 'Ontology'})
    output = export_interactive_graph_html(graph, tmp_path / 'ontology.html', title='Ontology Graph')
    text = output.read_text(encoding='utf-8')

    assert '\u667a\u80fd\u95ee\u7b54\u52a9\u624b' in text
    assert '\u7b54\u6848\u6458\u8981' in text
    assert '\u5173\u952e\u8bc1\u636e' in text
    assert '\u56fe\u8c31\u5b9a\u4f4d' in text
    assert '\u68c0\u7d22\u56de\u653e' in text
    assert '\u72b6\u6001' in text
    assert '\u5173\u7cfb\u56fe\u4f8b' in text
    assert '\u8282\u70b9\u8be6\u60c5' in text
    assert 'formatQaAnswer' in text
    assert 'qa-answer-inline-entity' in text
    assert '\*\*([^*]+)\*\*' in text
    for bad in ['????', '????', '???', '???', '????', '??']:
        assert bad not in text


def test_exported_html_skips_backlog_playback_after_visibility_restore(tmp_path: Path):
    graph = OntologyGraph(metadata={'title': 'Ontology'})
    output = export_interactive_graph_html(graph, tmp_path / 'ontology.html', title='Ontology Graph')
    text = output.read_text(encoding='utf-8')

    assert "document.addEventListener('visibilitychange'" in text
    assert 'pausePlaybackForHiddenDocument' in text
    assert 'resumePlaybackAfterVisibilityRestore' in text
    assert 'playbackController.queue = []' in text
    assert 'replayFromSnapshot(finalSnapshot, { fit: true, duration: 0, pulseDuration: 0 })' in text


def test_exported_html_derives_snapshot_edges_from_highlighted_nodes(tmp_path: Path):
    graph = OntologyGraph(metadata={'title': 'Ontology'})
    output = export_interactive_graph_html(graph, tmp_path / 'ontology.html', title='Ontology Graph')
    text = output.read_text(encoding='utf-8')

    assert 'function deriveIncrementalEdgeIds' in text
    assert 'duration: 420' in text
    assert 'pulseDuration: 580' in text
    assert 'deriveIncrementalEdgeIds(seedNodeIds, seedNodeIds)' in text
    assert 'deriveIncrementalEdgeIds(stepNodeIds, snapshotNodeIds, previousSnapshot.edge_ids || [])' in text


def test_exported_html_contains_router_failure_status_handling(tmp_path: Path):
    graph = OntologyGraph(metadata={'title': 'Ontology'})
    output = export_interactive_graph_html(graph, tmp_path / 'ontology.html', title='Ontology Graph')
    text = output.read_text(encoding='utf-8')

    assert 'currentRouterDiagnostics' in text
    assert 'handleRouterFailureDiagnostics' in text
    assert '路由识别失败' in text
    assert '因路由失败，未生成实例查询计划' in text
