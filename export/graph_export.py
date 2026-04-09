from __future__ import annotations

import html
import json
import math
import re
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

from ..schema import OntologyGraph


BROWSER_CANDIDATES = [
    Path(r'C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe'),
    Path(r'C:\Program Files\Microsoft\Edge\Application\msedge.exe'),
    Path(r'C:\Program Files\Google\Chrome\Application\chrome.exe'),
    Path(r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe'),
]

RELATION_TRANSLATIONS = {
    'HAS': '包含',
    'AGGREGATES': '聚合',
    'APPLIES_TO': '作用于',
    'ASSIGNED_TO': '分配到',
    'ASSIGNS': '指派给',
    'CONSTRAINS': '约束',
    'CONTAINS': '包含',
    'DEFINES': '定义',
    'DELIVERS': '交付',
    'DEPENDS_ON': '依赖',
    'EXECUTES': '执行',
    'GENERATES': '生成',
    'OCCURS_AT': '发生于落位',
    'OCCURS_IN': '发生于机房',
    'REFERENCES': '引用',
    'SHIPS': '运输',
    'USES': '使用',
}

GROUP_ORDER = [
    '项目与目标层',
    '空间层',
    '设备与物流层',
    '活动与排期层',
    '施工执行层',
    '决策与解释层',
]

DEFAULT_TYPE_COLORS = {
    'ObjectType': '#2563eb',
    'DerivedMetric': '#7c3aed',
    'MetricGroup': '#6d28d9',
}

METRIC_GROUP_ID = 'metric_group:关键派生指标'



def _load_cytoscape_bundle() -> str:
    asset_path = Path(__file__).resolve().parent / 'assets' / 'cytoscape.min.js'
    return asset_path.read_text(encoding='utf-8')


def build_interactive_graph_html(graph: OntologyGraph, title: str = 'Interactive Ontology Graph') -> str:
    payload = build_graph_payload(graph)
    payload_json = json.dumps(payload, ensure_ascii=False)
    cytoscape_bundle = _load_cytoscape_bundle()
    relation_legend_html = ''.join(
        f'<div class="legend-row"><span class="legend-en">{html.escape(item["relation"])}：{html.escape(item["translation"])}</span></div>'
        for item in payload['relationLegend']
    )
    default_panel_html = (
        '<div class="hero-card">'
        '<div class="hero-title">节点详情</div>'
        '<div class="hero-subtitle">点击左侧节点查看定义、属性和关系摘要。</div>'
        '</div>'
        '<div class="detail-card">'
        '<div class="section-title">关系摘要</div>'
        '<p class="muted">默认折叠，点击节点后可展开查看入边和出边详情。</p>'
        '</div>'
    )
    template = """<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>__TITLE__</title>
  <style>
    body { margin: 0; font-family: "Segoe UI", Arial, sans-serif; background: linear-gradient(180deg, #f8fafc 0%, #eef4ff 100%); color: #0f172a; }
    .toolbar { display: flex; gap: 10px; align-items: center; padding: 14px 18px; background: rgba(15, 23, 42, 0.96); color: white; position: sticky; top: 0; z-index: 20; backdrop-filter: blur(10px); box-shadow: 0 8px 20px rgba(15, 23, 42, 0.22); }
    .toolbar input, .toolbar select, .toolbar button { border-radius: 10px; border: none; padding: 9px 12px; font-size: 14px; }
    .toolbar input, .toolbar select { background: white; color: #0f172a; min-width: 180px; }
    .toolbar button { background: #2563eb; color: white; cursor: pointer; box-shadow: 0 6px 14px rgba(37, 99, 235, 0.25); }
    .toolbar button:hover { background: #1d4ed8; }
    .layout { height: calc(100vh - 66px); }
    .graph-stage { position: relative; height: 100%; overflow: hidden; background:
      radial-gradient(circle at top left, rgba(59,130,246,0.12), transparent 32%),
      linear-gradient(180deg, rgba(255,255,255,0.9), rgba(239,246,255,0.95)); }
    #cy { width: 100%; height: 100%; }
    .legend-card { position: absolute; left: 18px; bottom: 18px; width: 220px; background: rgba(255,255,255,0.95); border: 1px solid #dbe3f0; border-radius: 16px; padding: 14px; box-shadow: 0 14px 30px rgba(15,23,42,0.12); z-index: 10; }
    .legend-title { font-size: 14px; font-weight: 700; margin-bottom: 8px; color: #0f172a; }
    .legend-row { display: flex; justify-content: space-between; gap: 10px; padding: 5px 0; font-size: 12px; border-bottom: 1px dashed #e2e8f0; }
    .legend-row:last-child { border-bottom: none; }
    .legend-en { font-weight: 700; color: #1d4ed8; }
    .legend-zh { color: #475569; text-align: right; }
    .floating-detail-card { position: absolute; min-width: 220px; max-width: 280px; max-height: calc(100% - 48px); overflow: auto; right: auto; top: auto; z-index: 12; background: rgba(255,255,255,0.97); border: 1px solid #dbe3f0; border-radius: 18px; box-shadow: 0 20px 44px rgba(15,23,42,0.18); padding: 12px; backdrop-filter: blur(10px); font-size: 12px; }
    .graph-stage.filtering-active .legend-card { opacity: 0.72; }
    .trace-reset-button { position: absolute; top: 18px; right: 18px; z-index: 13; border: none; border-radius: 999px; padding: 8px 12px; font-size: 12px; font-weight: 700; background: rgba(15,23,42,0.88); color: white; cursor: pointer; box-shadow: 0 12px 28px rgba(15,23,42,0.22); }
    .floating-empty { color: #64748b; line-height: 1.5; }
    .hero-card { border-radius: 18px; padding: 18px; background: linear-gradient(135deg, #1d4ed8, #7c3aed); color: white; box-shadow: 0 18px 34px rgba(37,99,235,0.24); margin-bottom: 14px; }
    .hero-title { font-size: 22px; font-weight: 700; margin-bottom: 6px; }
    .hero-subtitle { opacity: 0.92; line-height: 1.5; }
    .detail-card { border-radius: 16px; background: white; border: 1px solid #e2e8f0; box-shadow: 0 10px 24px rgba(15,23,42,0.06); padding: 14px 16px; margin-bottom: 12px; }
    .section-title { margin: 0 0 10px 0; font-size: 14px; color: #334155; font-weight: 700; }
    .type-chip { display: inline-block; padding: 4px 10px; border-radius: 999px; background: #eff6ff; color: #1d4ed8; font-size: 12px; font-weight: 700; margin-right: 8px; }
    .group-chip { display: inline-block; padding: 4px 10px; border-radius: 999px; background: #f5f3ff; color: #6d28d9; font-size: 12px; font-weight: 600; }
    .muted { color: #64748b; }
    .detail-text { margin: 0; line-height: 1.65; }
    .pill-row { display: flex; gap: 6px; flex-wrap: wrap; }
    .pill { display: inline-block; padding: 4px 10px; border-radius: 999px; background: #e0e7ff; color: #3730a3; font-size: 12px; font-weight: 600; }
    .list { margin: 0; padding-left: 18px; }
    .list li { margin: 6px 0; line-height: 1.45; }
    .kv-grid { display: grid; grid-template-columns: 1fr; gap: 8px; }
    .summary-box { border-radius: 12px; background: #f8fafc; border: 1px solid #e2e8f0; padding: 10px 12px; }
    .summary-box strong { color: #0f172a; }
    .actions { margin-top: 12px; }
    .actions button { background: #e2e8f0; color: #0f172a; border: none; border-radius: 10px; padding: 7px 12px; cursor: pointer; }
    .hidden { display: none; }
    .qa-assistant-toggle { position: absolute; right: 20px; bottom: 20px; z-index: 14; border: none; border-radius: 999px; padding: 12px 18px; background: linear-gradient(135deg, #0ea5e9, #7c3aed); color: white; font-weight: 700; cursor: pointer; box-shadow: 0 12px 26px rgba(59,130,246,0.28); }
    .qa-answer-panel { position: absolute; right: 20px; bottom: 76px; z-index: 14; width: 360px; max-height: calc(100% - 120px); overflow: auto; border-radius: 18px; border: 1px solid rgba(59,130,246,0.24); background: linear-gradient(180deg, rgba(15,23,42,0.94), rgba(30,41,59,0.92)); color: #e2e8f0; box-shadow: 0 20px 48px rgba(15,23,42,0.34); padding: 16px; backdrop-filter: blur(14px); }
    .qa-title { font-size: 18px; font-weight: 700; margin-bottom: 4px; color: #f8fafc; }
    .qa-subtitle { font-size: 12px; color: #93c5fd; line-height: 1.5; margin-bottom: 14px; }
    .qa-input { width: 100%; min-height: 96px; resize: vertical; border-radius: 12px; border: 1px solid rgba(148,163,184,0.35); background: rgba(15,23,42,0.72); color: #e2e8f0; padding: 12px; box-sizing: border-box; }
    .qa-actions { display: flex; justify-content: flex-end; margin-top: 10px; }
    .qa-submit { border: none; border-radius: 10px; padding: 8px 14px; background: linear-gradient(135deg, #2563eb, #7c3aed); color: white; font-weight: 700; cursor: pointer; }
    .qa-card { margin-top: 14px; border-radius: 14px; background: rgba(15,23,42,0.48); border: 1px solid rgba(148,163,184,0.24); padding: 12px; }
    .qa-card-title { font-size: 13px; font-weight: 700; color: #bfdbfe; margin-bottom: 8px; }
    @keyframes tracePulse { 0% { transform: scale(1); box-shadow: 0 0 0 rgba(96,165,250,0.0); } 50% { transform: scale(1.01); box-shadow: 0 0 18px rgba(96,165,250,0.35); } 100% { transform: scale(1); box-shadow: 0 0 0 rgba(96,165,250,0.0); } }
    .searching-node { animation: tracePulse 1.2s ease-in-out infinite; }
    .trace-path { box-shadow: 0 0 0 1px rgba(249,115,22,0.35); }
    .trace-dimmed { opacity: 0.38; }
    .evidence-timeline button { width: 100%; text-align: left; }
    .qa-answer-text { min-height: 72px; line-height: 1.7; font-size: 15px; color: #f8fafc; white-space: pre-wrap; }
    .qa-tabs { display: flex; gap: 8px; margin-top: 12px; }
    .qa-tab { border: 1px solid rgba(148,163,184,0.35); background: rgba(15,23,42,0.65); color: #cbd5e1; border-radius: 10px; padding: 6px 10px; font-size: 12px; cursor: pointer; }
    .qa-tab.active { background: linear-gradient(135deg, #2563eb, #7c3aed); color: #fff; border-color: transparent; }
    .qa-tab-panel { margin-top: 10px; }
    .qa-tab-panel.hidden { display: none; }
    .qa-answer-mode { margin-top: 8px; font-size: 12px; color: #93c5fd; }
    .qa-answer-insights { display: grid; gap: 10px; margin-top: 10px; }
    .qa-answer-insight-body { font-size: 12px; color: #cbd5e1; line-height: 1.7; }
    .qa-answer-insight-list { margin: 0; padding-left: 18px; }
    .qa-answer-insight-list li { margin: 6px 0; }
    .qa-answer-insight-empty { color: #94a3b8; }
    .qa-evidence-cards { display: grid; gap: 10px; }
    .evidence-card { border: 1px solid rgba(148,163,184,0.26); background: rgba(30,41,59,0.72); border-radius: 12px; padding: 10px; }
    .evidence-card-tag { display: inline-flex; align-items: center; margin-bottom: 8px; padding: 2px 8px; border-radius: 999px; background: rgba(59,130,246,0.16); color: #93c5fd; font-size: 11px; font-weight: 700; }
    .evidence-card-title { font-size: 12px; font-weight: 700; color: #e2e8f0; margin-bottom: 4px; }
    .evidence-card-entity { font-size: 11px; color: #94a3b8; margin-bottom: 8px; }
    .evidence-card-attrs { display: grid; gap: 6px; font-size: 12px; color: #cbd5e1; line-height: 1.5; }
    .evidence-card-overflow { border-style: dashed; }
    .qa-focus-list { display: grid; gap: 8px; }
    .qa-focus-target { text-align: left; border: 1px solid rgba(148,163,184,0.32); background: rgba(30,41,59,0.82); color: #e2e8f0; border-radius: 10px; padding: 8px 10px; cursor: pointer; }
    .qa-focus-playback { margin-top: 10px; }
    .qa-playback-controls { display: flex; gap: 8px; margin-bottom: 10px; }
    .qa-playback-button { flex: 1; border: 1px solid rgba(148,163,184,0.3); background: rgba(15,23,42,0.68); color: #e2e8f0; border-radius: 10px; padding: 6px 10px; font-size: 12px; cursor: pointer; }
    .qa-playback-button[disabled] { opacity: 0.45; cursor: not-allowed; }
    .qa-playback-current { margin-bottom: 10px; font-size: 12px; color: #cbd5e1; line-height: 1.6; }
    .qa-playback-step.active { border-color: rgba(96,165,250,0.9) !important; box-shadow: 0 0 0 1px rgba(96,165,250,0.25); }
  </style>
</head>
<body>
  <div class="toolbar">
    <input id="node-search" type="search" placeholder="搜索实体或指标" />
    <button id="search-button">定位</button>
    <select id="relation-filter"></select>
    <button id="toggle-metrics">展开/收起指标</button>
    <button id="reset-view">重置视图</button>
  </div>
  <div class="layout">
    <div class="graph-stage">
      <div id="cy"></div>
      <div class="legend-card">
        <div class="legend-title">关系图例</div>
        __RELATION_LEGEND__
      </div>
      <div id="floating-detail-card" class="floating-detail-card hidden">__DEFAULT_PANEL__</div>
      <button id="trace-reset-button" class="trace-reset-button hidden">Reset focus</button>
      <button id="qa-assistant-toggle" class="qa-assistant-toggle">智能问答助手</button>
      <section id="qa-answer-panel" class="qa-answer-panel hidden">
        <div class="qa-title">智能问答助手</div>
        <div class="qa-subtitle">仅基于当前本体系统回答</div>
        <textarea id="qa-question" class="qa-input" placeholder="请输入你想询问的本体问题"></textarea>
        <div class="qa-actions"><button id="qa-submit" class="qa-submit">提问</button></div>
        <div id="qa-status" class="qa-card hidden"><div class="qa-card-title">状态</div><div>等待提问</div></div>

        <div class="qa-tabs" id="qa-tabs">
          <button id="qa-tab-answer" class="qa-tab active" type="button">答案摘要</button>
          <button id="qa-tab-evidence" class="qa-tab" type="button">关键证据</button>
          <button id="qa-tab-focus" class="qa-tab" type="button">图谱定位</button>
        </div>

        <div id="qa-panel-answer" class="qa-tab-panel">
          <div id="qa-answer" class="qa-card hidden"><div class="qa-card-title">答案摘要</div><div id="qa-answer-text" class="qa-answer-text">等待回答</div><div id="qa-answer-mode" class="qa-answer-mode hidden"></div></div>
          <div id="qa-answer-insights" class="qa-answer-insights">
            <div class="qa-card">
              <div class="qa-card-title">结论依据</div>
              <div id="qa-answer-basis" class="qa-answer-insight-body"><div class="muted">等待回答</div></div>
            </div>
            <div class="qa-card">
              <div class="qa-card-title">数据缺口</div>
              <div id="qa-answer-gaps" class="qa-answer-insight-body"><div class="muted">等待检索</div></div>
            </div>
          </div>
        </div>

        <div id="qa-panel-evidence" class="qa-tab-panel hidden">
          <div class="qa-card">
            <div class="qa-card-title">关键证据</div>
            <div id="qa-evidence-cards" class="qa-evidence-cards"><div class="muted">等待证据</div></div>
          </div>
        </div>

        <div id="qa-panel-focus" class="qa-tab-panel hidden">
          <div class="qa-card">
            <div class="qa-card-title">图谱定位</div>
            <div id="qa-focus-list" class="qa-focus-list"><div class="muted">等待可定位对象</div></div>
          </div>
          <div id="qa-focus-playback" class="qa-card hidden evidence-timeline qa-focus-playback"><div class="qa-card-title">检索回放</div><div class="qa-playback-controls"><button id="qa-playback-prev" class="qa-playback-button" type="button">上一步</button><button id="qa-playback-replay" class="qa-playback-button" type="button">重播</button><button id="qa-playback-next" class="qa-playback-button" type="button">下一步</button></div><div id="qa-playback-current" class="qa-playback-current">等待检索</div><div id="qa-focus-playback-body"><div class="muted">等待检索</div></div></div>
        </div>
      </section>
  </div>
  <script>__CYTOSCAPE_BUNDLE__
window.cytoscape = window.cytoscape || cytoscape;
</script>
  <script>
    const graphPayload = __PAYLOAD__;
    const relationFilter = document.getElementById('relation-filter');
    const graphStage = document.querySelector('.graph-stage');
    const floatingDetailCard = document.getElementById('floating-detail-card');
    const traceResetButton = document.getElementById('trace-reset-button');
    const searchInput = document.getElementById('node-search');
    const searchButton = document.getElementById('search-button');
    const resetButton = document.getElementById('reset-view');
    const toggleMetricsButton = document.getElementById('toggle-metrics');
    const qaAssistantToggle = document.getElementById('qa-assistant-toggle');
    const qaAnswerPanel = document.getElementById('qa-answer-panel');
    const qaQuestionInput = document.getElementById('qa-question');
    const qaSubmitButton = document.getElementById('qa-submit');
    const qaStatusCard = document.getElementById('qa-status');
    const qaTabAnswer = document.getElementById('qa-tab-answer');
    const qaTabEvidence = document.getElementById('qa-tab-evidence');
    const qaTabFocus = document.getElementById('qa-tab-focus');
    const qaPanelAnswer = document.getElementById('qa-panel-answer');
    const qaPanelEvidence = document.getElementById('qa-panel-evidence');
    const qaPanelFocus = document.getElementById('qa-panel-focus');
    const qaAnswerCard = document.getElementById('qa-answer');
    const qaAnswerText = document.getElementById('qa-answer-text');
    const qaAnswerMode = document.getElementById('qa-answer-mode');
    const qaAnswerInsights = document.getElementById('qa-answer-insights');
    const qaAnswerBasis = document.getElementById('qa-answer-basis');
    const qaAnswerGaps = document.getElementById('qa-answer-gaps');
    const qaEvidenceCards = document.getElementById('qa-evidence-cards');
    const qaFocusList = document.getElementById('qa-focus-list');
    const qaFocusPlaybackCard = document.getElementById('qa-focus-playback');
    const qaPlaybackPrev = document.getElementById('qa-playback-prev');
    const qaPlaybackReplay = document.getElementById('qa-playback-replay');
    const qaPlaybackNext = document.getElementById('qa-playback-next');
    const qaPlaybackCurrent = document.getElementById('qa-playback-current');
    const qaStatusBody = qaStatusCard.querySelector('div:last-child');
    const qaFocusPlaybackBody = document.getElementById('qa-focus-playback-body');
    const defaultPanelHtml = __DEFAULT_PANEL_JSON__;
    let qaEventSource = null;
    let persistedEvidenceChain = [];
    let persistedEvidenceMap = new Map();
    let evidenceSnapshots = new Map();
    let currentTraceSummary = null;
    let currentQuestionDsl = null;
    let currentEvidenceBundle = null;
    let currentFocusTargets = [];
    let currentPlaybackStepIndex = -1;
    let playbackController = null;
    let activeDetailNode = null;
    let detailCardFrame = null;

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
        const separatorIndex = value.indexOf('\uFF1A');
        if (separatorIndex === -1) {
          return `<li><strong>${value}</strong></li>`;
        }
        const key = value.slice(0, separatorIndex);
        const description = value.slice(separatorIndex + 1);
        return `<li><strong>${key}</strong>\uFF1A${description}</li>`;
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

    function repositionDetailCard() {
      if (detailCardFrame !== null) {
        window.cancelAnimationFrame(detailCardFrame);
      }
      detailCardFrame = requestAnimationFrame(() => {
        detailCardFrame = null;
        if (!activeDetailNode || floatingDetailCard.classList.contains('hidden')) return;
        const stageRect = graphStage.getBoundingClientRect();
        const previousVisibility = floatingDetailCard.style.visibility;
        floatingDetailCard.style.visibility = 'hidden';
        const cardRect = floatingDetailCard.getBoundingClientRect();
        const pos = activeDetailNode.renderedPosition();
        let left = pos.x + 20;
        let top = pos.y - 20;
        const maxLeft = Math.max(12, stageRect.width - cardRect.width - 12);
        const maxTop = Math.max(12, stageRect.height - cardRect.height - 12);
        left = Math.max(12, Math.min(left, maxLeft));
        top = Math.max(12, Math.min(top, maxTop));
        floatingDetailCard.style.left = `${left}px`;
        floatingDetailCard.style.top = `${top}px`;
        floatingDetailCard.style.visibility = previousVisibility === 'hidden' ? 'visible' : (previousVisibility || 'visible');
      });
    }

    function showInlineDetailCard(node, htmlContent) {
      activeDetailNode = node;
      floatingDetailCard.innerHTML = htmlContent;
      floatingDetailCard.classList.remove('hidden');
      floatingDetailCard.style.visibility = 'hidden';
      repositionDetailCard();
    }

    function hideInlineDetailCard() {
      activeDetailNode = null;
      if (detailCardFrame !== null) {
        window.cancelAnimationFrame(detailCardFrame);
        detailCardFrame = null;
      }
      floatingDetailCard.classList.add('hidden');
      floatingDetailCard.innerHTML = defaultPanelHtml;
      floatingDetailCard.style.visibility = 'visible';
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
      qaStatusBody.textContent = message || '\\u7b49\\u5f85\\u63d0\\u95ee';
    }

    function setQaActiveTab(tab) {
      const isAnswer = tab == 'answer';
      const isEvidence = tab == 'evidence';
      const isFocus = tab == 'focus';
      qaTabAnswer.classList.toggle('active', isAnswer);
      qaTabEvidence.classList.toggle('active', isEvidence);
      qaTabFocus.classList.toggle('active', isFocus);
      qaPanelAnswer.classList.toggle('hidden', !isAnswer);
      qaPanelEvidence.classList.toggle('hidden', !isEvidence);
      qaPanelFocus.classList.toggle('hidden', !isFocus);
    }

    function clearQaAnswerTabState() {
      qaAnswerMode.classList.add('hidden');
      qaAnswerMode.textContent = '';
    }

    function setQaAnswerTabState(used_fallback) {
      qaAnswerMode.classList.remove('hidden');
      qaAnswerMode.textContent = used_fallback ? '基础回答' : 'AI总结';
    }

    function setQaAnswer(message) {
      qaAnswerCard.classList.remove('hidden');
      qaAnswerText.innerHTML = escapeHtml(message || '');
    }

    function resetQaSummaryPanels() {
      if (qaAnswerBasis) qaAnswerBasis.innerHTML = '<div class="muted">等待回答</div>';
      if (qaAnswerGaps) qaAnswerGaps.innerHTML = '<div class="muted">等待检索</div>';
      if (qaEvidenceCards) qaEvidenceCards.innerHTML = '<div class="muted">等待证据</div>';
      if (qaFocusList) qaFocusList.innerHTML = '<div class="muted">等待可定位对象</div>';
    }

    function renderAnswerInsights(traceSummary) {
      const compact = traceSummary && traceSummary.compact && typeof traceSummary.compact === 'object'
        ? traceSummary.compact
        : {};
      qaAnswerInsights.id = 'qa-answer-insights';
      qaAnswerBasis.innerHTML = formatAnswerInsightList(compact.reasoning_basis, '暂无结论依据');
      qaAnswerGaps.innerHTML = formatAnswerGapList(compact.data_gaps, '暂无明显数据缺口');
    }

    function formatAnswerInsightList(items, emptyText) {
      if (!Array.isArray(items) || !items.length) {
        return `<div class="qa-answer-insight-empty">${escapeHtml(emptyText)}</div>`;
      }
      return `<ul class="qa-answer-insight-list">${items.map(item => `<li>${escapeHtml(String(item || ''))}</li>`).join('')}</ul>`;
    }

    function formatAnswerGapList(items, emptyText) {
      if (!Array.isArray(items) || !items.length) {
        return `<div class="qa-answer-insight-empty">${escapeHtml(emptyText)}</div>`;
      }
      return `<ul class="qa-answer-insight-list">${items.map(item => {
        if (item && typeof item === 'object') {
          return `<li>${escapeHtml(String(item.message || ''))}</li>`;
        }
        return `<li>${escapeHtml(String(item || ''))}</li>`;
      }).join('')}</ul>`;
    }

    function formatEvidenceValue(value) {
      if (Array.isArray(value)) return value.map(item => String(item || '')).filter(Boolean).join('\u3001');
      if (value && typeof value === 'object') return JSON.stringify(value);
      return String(value || '');
    }

    function pickEvidenceTitle(instance) {
      const entries = Object.entries(instance || {}).filter(([, value]) => value !== null && value !== undefined && String(value).trim() !== '');
      const preferred = entries.find(([key]) => /(^id$|_id$|-id$)/i.test(key))
        || entries.find(([key]) => /name/i.test(key))
        || entries[0];
      if (!preferred) return '实例';
      return `${preferred[0]}=${formatEvidenceValue(preferred[1])}`;
    }

    function buildEvidenceCard(entity, label, instance) {
      const safeInstance = instance && typeof instance === 'object' ? instance : {};
      const attrs = Object.entries(safeInstance).filter(([, value]) => value !== null && value !== undefined && String(value).trim() !== '');
      const attrsHtml = attrs.length
        ? attrs.map(([key, value]) => `<div><strong>${escapeHtml(key)}</strong>\uff1a${escapeHtml(formatEvidenceValue(value))}</div>`).join('')
        : '<div class="muted">暂无实例属性</div>';
      return `<div class="evidence-card"><div class="evidence-card-tag">${escapeHtml(label || entity || '关键证据')}</div><div class="evidence-card-title">${escapeHtml(pickEvidenceTitle(safeInstance))}</div><div class="evidence-card-entity">${escapeHtml(entity || '')}</div><div class="evidence-card-attrs">${attrsHtml}</div></div>`;
    }

    function renderEvidenceCards(traceSummary) {
      if (!qaEvidenceCards) return;
      const compactHits = traceSummary && traceSummary.compact && traceSummary.compact.key_evidence && traceSummary.compact.key_evidence.direct_hits
        ? traceSummary.compact.key_evidence.direct_hits
        : {};
      const detailedGroups = Array.isArray(traceSummary && traceSummary.expanded && traceSummary.expanded.detailed_evidence)
        ? traceSummary.expanded.detailed_evidence
        : [];
      const cards = [];
      if (detailedGroups.length) {
        detailedGroups.forEach(group => {
          const safeGroup = group && typeof group === 'object' ? group : {};
          const entity = String(safeGroup.entity || '').trim();
          const label = safeGroup.label || entity;
          const instances = Array.isArray(safeGroup.instances) ? safeGroup.instances : [];
          instances.forEach(instance => cards.push(buildEvidenceCard(entity, label, instance)));
          const total = Number(compactHits[entity] && compactHits[entity].total ? compactHits[entity].total : instances.length);
          const overflow = Math.max(total - instances.length, 0);
          if (overflow > 0) {
            cards.push(`<div class="evidence-card evidence-card-overflow"><div class="evidence-card-tag">${escapeHtml(label)}</div><div class="evidence-card-title">其余 ${overflow} 条已折叠</div></div>`);
          }
        });
      } else {
        Object.entries(compactHits).forEach(([entity, payload]) => {
          const safePayload = payload && typeof payload === 'object' ? payload : {};
          const label = safePayload.label || entity;
          const items = Array.isArray(safePayload.items) ? safePayload.items : [];
          if (!items.length) {
            cards.push(`<div class="evidence-card"><div class="evidence-card-tag">${escapeHtml(label)}</div><div class="evidence-card-title">命中 ${Number(safePayload.total || 0)} 个</div><div class="evidence-card-entity">${escapeHtml(entity)}</div><div class="evidence-card-attrs"><div class="muted">暂无实例预览</div></div></div>`);
            return;
          }
          items.forEach(item => cards.push(buildEvidenceCard(entity, label, item)));
        });
      }
      qaEvidenceCards.innerHTML = cards.length
        ? cards.join('')
        : '<div class="muted">暂无关键证据</div>';
    }

    function renderFocusTargets(traceSummary) {
      if (!qaFocusList) return;
      const targets = [];
      const seen = new Set();
      const keyPaths = Array.isArray(traceSummary && traceSummary.expanded && traceSummary.expanded.key_paths)
        ? traceSummary.expanded.key_paths
        : [];
      keyPaths.forEach(item => {
        const summary = item && typeof item === 'object' ? String(item.path_summary || '').trim() : String(item || '').trim();
        if (!summary || seen.has(`path:${summary}`)) return;
        const entities = [];
        const regex = /([A-Za-z][A-Za-z0-9_]*)\\s+[^\\s,;]+/g;
        let match;
        while ((match = regex.exec(summary)) !== null) {
          entities.push(match[1]);
        }
        targets.push({ label: summary, node_ids: findNodeIdsForEntityNames(entities), edge_ids: [] });
        seen.add(`path:${summary}`);
      });
      const groups = Array.isArray(traceSummary && traceSummary.expanded && traceSummary.expanded.detailed_evidence)
        ? traceSummary.expanded.detailed_evidence
        : [];
      groups.forEach(group => {
        const safeGroup = group && typeof group === 'object' ? group : {};
        const entity = String(safeGroup.entity || '').trim();
        if (!entity) return;
        const nodeIds = findNodeIdsForEntityNames([entity]);
        const label = safeGroup.label || entity;
        const instances = Array.isArray(safeGroup.instances) ? safeGroup.instances : [];
        if (!instances.length && !seen.has(`entity:${entity}`)) {
          targets.push({ label, node_ids: nodeIds, edge_ids: [] });
          seen.add(`entity:${entity}`);
          return;
        }
        instances.slice(0, 6).forEach(instance => {
          const targetLabel = `${label}\uff1a${pickEvidenceTitle(instance)}`;
          if (seen.has(`instance:${targetLabel}`)) return;
          targets.push({ label: targetLabel, node_ids: nodeIds, edge_ids: [] });
          seen.add(`instance:${targetLabel}`);
        });
      });
      currentFocusTargets = targets;
      qaFocusList.innerHTML = targets.length
        ? targets.map((target, index) => `<button type="button" class="qa-focus-target" data-focus-index="${index}">${escapeHtml(target.label)}</button>`).join('')
        : '<div class="muted">暂无可定位对象</div>';
      qaFocusList.querySelectorAll('[data-focus-index]').forEach(button => {
        button.addEventListener('click', () => {
          const index = Number(button.dataset.focusIndex);
          focusTraceTarget(currentFocusTargets[index]);
        });
      });
    }

    function focusTraceTarget(target) {
      if (!target) return;
      if (!Array.isArray(target.node_ids) || !target.node_ids.length) {
        setQaStatus(`暂无可对应的图谱节点：${target.label || '目标'}`);
        setQaActiveTab('focus');
        return;
      }
      replayFromSnapshot({ node_ids: target.node_ids, edge_ids: target.edge_ids || [] }, { fit: true, duration: 260, pulseDuration: 380 });
      setQaStatus(`已定位：${target.label || '目标'}`);
      setQaActiveTab('focus');
    }

    function setQaTraceSummary(traceSummary) {
      renderAnswerInsights(traceSummary);
      renderEvidenceCards(traceSummary);
      renderFocusTargets(traceSummary);
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

    function showTraceResetButton() {
      traceResetButton.classList.remove('hidden');
    }

    function hideTraceResetButton() {
      traceResetButton.classList.add('hidden');
    }

    function setFilteringState(active) {
      graphStage.classList.toggle('filtering-active', Boolean(active));
      if (active) {
        showTraceResetButton();
        return;
      }
      hideTraceResetButton();
    }

    function resetToExplorationMode(options = {}) {
      const shouldFit = options.fit !== false;
      const shouldResetInputs = options.resetInputs !== false;
      activeDetailNode = null;
      clearTraceClasses();
      cy.elements().removeClass('highlighted');
      cy.elements().removeClass('dimmed');
      if (playbackController) {
        playbackController.currentSnapshot = null;
      }
      if (shouldResetInputs) {
        relationFilter.value = 'all';
        searchInput.value = '';
        toggleMetricNodes(false);
        applyRelationFilter();
      }
      hideInlineDetailCard();
      setFilteringState(false);
      if (shouldFit) {
        cy.fit(cy.elements(':visible'), 70);
      }
    }

    function clearQaPresentation() {
      setQaStatus('\u7b49\u5f85\u63d0\u95ee');
      qaAnswerCard.classList.add('hidden');
      qaAnswerText.textContent = '\u7b49\u5f85\u56de\u7b54';
      clearQaAnswerTabState();
      setQaActiveTab('answer');
      resetQaSummaryPanels();
      currentFocusTargets = [];
      currentTraceSummary = null;
      currentQuestionDsl = null;
      currentEvidenceBundle = null;
      currentPlaybackStepIndex = -1;
      qaFocusPlaybackCard.classList.add('hidden');
      qaPlaybackCurrent.textContent = '\u7b49\u5f85\u5b9e\u4f53\u68c0\u7d22';
      qaFocusPlaybackBody.innerHTML = '<div class="muted">\u7b49\u5f85\u5b9e\u4f53\u68c0\u7d22</div>';
      persistedEvidenceChain = [];
      persistedEvidenceMap = new Map();
      evidenceSnapshots = new Map();
      updateFocusPlaybackControls();
      clearTraceClasses();
      setFilteringState(false);
      clearPlaybackTimers(playbackController);
      if (playbackController) {
        playbackController.queue = [];
        playbackController.running = false;
        playbackController.traceProtocolSeen = false;
        playbackController.instanceQaProtocolSeen = false;
        playbackController.currentSnapshot = null;
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
      if (playbackController) {
        playbackController.currentSnapshot = normalized;
      }
      const collection = buildFocusCollection(normalized.node_ids, normalized.edge_ids);
      if (!collection.length) {
        setFilteringState(false);
        cy.elements(':visible').removeClass('trace-dimmed');
        return normalized;
      }
      setFilteringState(true);
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

    function hasSnapshotData(snapshot) {
      return Boolean(snapshot) && ((Array.isArray(snapshot.node_ids) && snapshot.node_ids.length > 0) || (Array.isArray(snapshot.edge_ids) && snapshot.edge_ids.length > 0));
    }

    function updateFocusPlaybackControls() {
      const hasSteps = persistedEvidenceChain.length > 0;
      qaPlaybackPrev.disabled = !hasSteps || currentPlaybackStepIndex <= 0;
      qaPlaybackReplay.disabled = !hasSteps || currentPlaybackStepIndex < 0;
      qaPlaybackNext.disabled = !hasSteps || currentPlaybackStepIndex >= persistedEvidenceChain.length - 1;
      if (!hasSteps || currentPlaybackStepIndex < 0 || currentPlaybackStepIndex >= persistedEvidenceChain.length) {
        qaPlaybackCurrent.textContent = '等待检索';
        return;
      }
      const currentItem = persistedEvidenceChain[currentPlaybackStepIndex] || {};
      const stepLabel = currentItem.label || currentItem.kind || '检索步骤';
      const stepMessage = currentItem.message || '';
      qaPlaybackCurrent.textContent = `当前步骤 ${currentPlaybackStepIndex + 1}/${persistedEvidenceChain.length}：${stepLabel}${stepMessage ? ` — ${stepMessage}` : ''}`;
    }

    function setFocusPlaybackIndex(index, options = {}) {
      if (!persistedEvidenceChain.length) {
        currentPlaybackStepIndex = -1;
        updateFocusPlaybackControls();
        return;
      }
      const safeIndex = Math.max(0, Math.min(index, persistedEvidenceChain.length - 1));
      currentPlaybackStepIndex = safeIndex;
      updateFocusPlaybackControls();
      qaFocusPlaybackBody.querySelectorAll('[data-playback-index]').forEach(button => {
        button.classList.toggle('active', Number(button.dataset.playbackIndex) === safeIndex);
      });
      const item = persistedEvidenceChain[safeIndex] || {};
      const snapshot = evidenceSnapshots.get(item.evidence_id) || { node_ids: [], edge_ids: [] };
      if (options.replay !== false && hasSnapshotData(snapshot)) {
        replayFromSnapshot(snapshot, { fit: true, duration: 280, pulseDuration: 420 });
      }
      if (options.setStatus !== false) {
        setQaStatus(`检索步骤 ${safeIndex + 1}/${persistedEvidenceChain.length}：${item.label || item.kind || '证据'}`);
      }
      if (options.openTab) {
        setQaActiveTab('focus');
      }
    }

    function renderEvidenceTimeline(chain) {
      qaFocusPlaybackCard.classList.remove('hidden');
      if (!Array.isArray(chain) || chain.length === 0) {
        currentPlaybackStepIndex = -1;
        qaFocusPlaybackBody.innerHTML = '<div class="muted">暂无检索步骤</div>';
        updateFocusPlaybackControls();
        return;
      }
      qaFocusPlaybackBody.innerHTML = chain.map((item, index) => {
        const reasons = Array.isArray(item.why_matched) && item.why_matched.length
          ? `<div style="margin-top:6px;color:#93c5fd;font-size:12px;">${item.why_matched.map(reason => escapeHtml(reason)).join('<br />')}</div>`
          : '';
        const activeClass = index === currentPlaybackStepIndex ? ' active' : '';
        return `
          <button type="button" data-evidence-id="${escapeHtml(item.evidence_id)}" data-playback-index="${index}" class="qa-playback-step${activeClass}" style="display:block;width:100%;text-align:left;background:rgba(30,41,59,0.9);border:1px solid rgba(148,163,184,0.28);border-radius:12px;color:#e2e8f0;padding:10px 12px;margin:0 0 10px 0;cursor:pointer;">
            <div style="font-weight:700;color:#bfdbfe;">[${index + 1}] ${escapeHtml(item.label || item.kind || '证据')}</div>
            <div style="margin-top:4px;line-height:1.5;">${escapeHtml(item.message || '')}</div>
            ${reasons}
          </button>
        `;
      }).join('');
      qaFocusPlaybackBody.querySelectorAll('[data-playback-index]').forEach(button => {
        button.addEventListener('click', () => {
          setFocusPlaybackIndex(Number(button.dataset.playbackIndex), { replay: true, openTab: true });
        });
      });
      if (currentPlaybackStepIndex >= chain.length) {
        currentPlaybackStepIndex = chain.length - 1;
      }
      updateFocusPlaybackControls();
    }

    function upsertEvidenceItem(evidence, snapshot) {
      if (!evidence || !evidence.evidence_id) return;
      persistedEvidenceMap.set(evidence.evidence_id, evidence);
      if (snapshot) {
        evidenceSnapshots.set(evidence.evidence_id, normalizeSnapshot(snapshot));
      }
      persistedEvidenceChain = Array.from(persistedEvidenceMap.values());
      renderEvidenceTimeline(persistedEvidenceChain);
      const playbackIndex = persistedEvidenceChain.findIndex(item => item.evidence_id === evidence.evidence_id);
      if (playbackIndex >= 0 && hasSnapshotData(evidenceSnapshots.get(evidence.evidence_id))) {
        setFocusPlaybackIndex(playbackIndex, { replay: true, setStatus: false });
      }
    }

    function appendEvidenceIncrementally(evidence) {
      upsertEvidenceItem(evidence, evidence && evidence.snapshot ? evidence.snapshot : null);
    }

    function persistFinalEvidence(result) {
      persistedEvidenceChain = Array.isArray(result.evidence_chain) ? result.evidence_chain : [];
      persistedEvidenceMap = new Map(persistedEvidenceChain.map(item => [item.evidence_id, item]));
      evidenceSnapshots = buildEvidenceSnapshots(persistedEvidenceChain, result.search_trace || {});
      renderEvidenceTimeline(persistedEvidenceChain);
      if (persistedEvidenceChain.length && currentPlaybackStepIndex < 0) {
        setFocusPlaybackIndex(persistedEvidenceChain.length - 1, { replay: false, setStatus: false });
      }
    }

    function findNodeIdsForEntityNames(entityNames) {
      const wanted = new Set((entityNames || []).map(value => String(value || '').trim()).filter(Boolean));
      if (!wanted.size) return [];
      return cy.nodes().filter(node => wanted.has(String(node.data('display_name') || '').trim())).map(node => node.id());
    }

    function findEdgeIdsForRelationTriples(triples) {
      const matchers = (triples || []).filter(Boolean);
      if (!matchers.length) return [];
      const edgeIds = [];
      cy.edges().forEach(edge => {
        const sourceNode = edge.source();
        const targetNode = edge.target();
        const relation = String(edge.data('relation') || '').trim();
        const sourceName = String(sourceNode.data('display_name') || '').trim();
        const targetName = String(targetNode.data('display_name') || '').trim();
        const matched = matchers.some(item => {
          const relationMatches = !item.relation || String(item.relation).trim() === relation;
          const sourceMatches = !item.source || String(item.source).trim() === sourceName;
          const targetMatches = !item.target || String(item.target).trim() === targetName;
          return relationMatches && sourceMatches && targetMatches;
        });
        if (matched) {
          edgeIds.push(edge.id());
        }
      });
      return [...new Set(edgeIds)];
    }

    function buildTypedbResultSnapshot(factPack) {
      const counts = factPack && typeof factPack === 'object' && factPack.counts && typeof factPack.counts === 'object'
        ? Object.keys(factPack.counts)
        : [];
      const instances = factPack && typeof factPack === 'object' && factPack.instances && typeof factPack.instances === 'object'
        ? Object.keys(factPack.instances)
        : [];
      const links = Array.isArray(factPack && factPack.links) ? factPack.links : [];
      return {
        node_ids: findNodeIdsForEntityNames([...counts, ...instances]),
        edge_ids: findEdgeIdsForRelationTriples(links.map(link => ({
          source: link.source_entity,
          relation: link.relation,
          target: link.target_entity,
        }))),
      };
    }

    function buildReasoningSnapshot(reasoning) {
      const affected = Array.isArray(reasoning && reasoning.affected_entities) ? reasoning.affected_entities : [];
      return {
        node_ids: findNodeIdsForEntityNames(affected.map(item => item && item.entity)),
        edge_ids: [],
      };
    }

    function collectSchemaRetrievalEntities(questionDsl, evidenceBundle) {
      const result = [];
      const seen = new Set();
      function pushEntity(value) {
        const text = String(value || '').trim();
        if (!text || seen.has(text)) return;
        seen.add(text);
        result.push(text);
      }
      const anchor = questionDsl && typeof questionDsl === 'object' && questionDsl.anchor && typeof questionDsl.anchor === 'object'
        ? questionDsl.anchor
        : {};
      pushEntity(anchor.entity);
      const understanding = evidenceBundle && typeof evidenceBundle === 'object' && evidenceBundle.understanding && typeof evidenceBundle.understanding === 'object'
        ? evidenceBundle.understanding
        : {};
      const understandingAnchor = understanding.anchor && typeof understanding.anchor === 'object' ? understanding.anchor : {};
      pushEntity(understandingAnchor.entity);
      const groups = Array.isArray(evidenceBundle && evidenceBundle.positive_evidence) ? evidenceBundle.positive_evidence : [];
      groups.forEach(group => pushEntity(group && group.entity));
      const emptyEntities = Array.isArray(evidenceBundle && evidenceBundle.empty_entities) ? evidenceBundle.empty_entities : [];
      emptyEntities.forEach(item => pushEntity(item && item.entity));
      const unrelatedEntities = Array.isArray(evidenceBundle && evidenceBundle.unrelated_entities) ? evidenceBundle.unrelated_entities : [];
      unrelatedEntities.forEach(item => pushEntity(item && item.entity));
      const omittedEntities = Array.isArray(evidenceBundle && evidenceBundle.omitted_entities) ? evidenceBundle.omitted_entities : [];
      omittedEntities.forEach(item => pushEntity(item && item.entity));
      const edges = Array.isArray(evidenceBundle && evidenceBundle.edges) ? evidenceBundle.edges : [];
      edges.forEach(edge => {
        pushEntity(edge && edge.source_entity);
        pushEntity(edge && edge.target_entity);
      });
      return result;
    }

    function buildSchemaPathTriples(pathText) {
      const text = String(pathText || '').trim();
      if (!text) return [];
      const nodes = [];
      const nodePattern = /([A-Za-z][A-Za-z0-9_]*)\([^)]*\)/g;
      let nodeMatch;
      while ((nodeMatch = nodePattern.exec(text)) !== null) {
        nodes.push({ entity: nodeMatch[1], index: nodeMatch.index, raw: nodeMatch[0] });
      }
      if (nodes.length < 2) return [];
      const triples = [];
      for (let index = 0; index < nodes.length - 1; index += 1) {
        const current = nodes[index];
        const next = nodes[index + 1];
        const between = text.slice(current.index + current.raw.length, next.index).trim();
        let relationMatch = between.match(/--([^<>-]+)-->/);
        if (relationMatch) {
          triples.push({ source: current.entity, relation: String(relationMatch[1] || '').trim(), target: next.entity, reason: text });
          continue;
        }
        relationMatch = between.match(/<--([^<>-]+)--/);
        if (relationMatch) {
          triples.push({ source: next.entity, relation: String(relationMatch[1] || '').trim(), target: current.entity, reason: text });
        }
      }
      return triples;
    }

    function dedupeSchemaTriples(triples) {
      const result = [];
      const seen = new Set();
      (triples || []).forEach(item => {
        const source = String(item && item.source || '').trim();
        const relation = String(item && item.relation || '').trim();
        const target = String(item && item.target || '').trim();
        if (!source || !relation || !target) return;
        const key = `${source}|${relation}|${target}`;
        if (seen.has(key)) return;
        seen.add(key);
        result.push({ source, relation, target, reason: String(item && item.reason || '').trim() });
      });
      return result;
    }

    function buildSchemaRetrievalEdgeTriples(evidenceBundle) {
      const pathTriples = [];
      const paths = Array.isArray(evidenceBundle && evidenceBundle.paths) ? evidenceBundle.paths : [];
      paths.forEach(path => {
        buildSchemaPathTriples(path).forEach(item => pathTriples.push(item));
      });
      if (pathTriples.length) return dedupeSchemaTriples(pathTriples);
      const edges = Array.isArray(evidenceBundle && evidenceBundle.edges) ? evidenceBundle.edges : [];
      return dedupeSchemaTriples(edges.map(edge => ({
        source: edge && edge.source_entity,
        relation: edge && edge.relation,
        target: edge && edge.target_entity,
        reason: '',
      })));
    }

    function buildSchemaRetrievalPlaybackSteps(questionDsl, evidenceBundle) {
      const steps = [];
      const anchor = questionDsl && typeof questionDsl === 'object' && questionDsl.anchor && typeof questionDsl.anchor === 'object'
        ? questionDsl.anchor
        : {};
      const anchorEntity = String(anchor.entity || '').trim();
      const cumulativeEntities = [];
      const seenEntities = new Set();
      const cumulativeTriples = [];
      function pushEntity(value) {
        const text = String(value || '').trim();
        if (!text || seenEntities.has(text)) return;
        seenEntities.add(text);
        cumulativeEntities.push(text);
      }
      if (anchorEntity) {
        pushEntity(anchorEntity);
        steps.push({
          evidence_id: 'schema:anchor',
          kind: 'schema_retrieval',
          label: '\u8bc6\u522b\u951a\u70b9\u5b9e\u4f53',
          message: `\u4ece ${anchorEntity} \u5f00\u59cb\u68c0\u7d22\u76f8\u5173\u672c\u4f53\u5b9e\u4f53`,
          node_ids: findNodeIdsForEntityNames([anchorEntity]),
          edge_ids: [],
          why_matched: [],
        });
      }
      buildSchemaRetrievalEdgeTriples(evidenceBundle).forEach((triple, index) => {
        pushEntity(triple.source);
        pushEntity(triple.target);
        cumulativeTriples.push({ source: triple.source, relation: triple.relation, target: triple.target });
        const whyMatched = triple.reason ? [triple.reason] : [];
        steps.push({
          evidence_id: `schema:expand:${index + 1}`,
          kind: 'schema_retrieval',
          label: `\u6269\u5c55\u5230 ${triple.target}`,
          message: `${triple.source} \u901a\u8fc7 ${triple.relation} \u5173\u8054\u5230 ${triple.target}`,
          node_ids: findNodeIdsForEntityNames(cumulativeEntities),
          edge_ids: findEdgeIdsForRelationTriples(cumulativeTriples),
          why_matched: whyMatched,
        });
      });
      const finalEntities = collectSchemaRetrievalEntities(questionDsl, evidenceBundle);
      const finalTriples = buildSchemaRetrievalEdgeTriples(evidenceBundle).map(item => ({ source: item.source, relation: item.relation, target: item.target }));
      const finalNodeIds = findNodeIdsForEntityNames(finalEntities);
      const finalEdgeIds = findEdgeIdsForRelationTriples(finalTriples);
      if (finalNodeIds.length || finalEdgeIds.length) {
        steps.push({
          evidence_id: 'schema:final',
          kind: 'schema_retrieval',
          label: '\u6700\u7ec8\u5b9a\u4f4d\u5b50\u56fe',
          message: finalEntities.length ? `\u6700\u7ec8\u5b9a\u4f4d\u5230 ${finalEntities.join('\u3001')}` : '\u6700\u7ec8\u5b9a\u4f4d\u5230\u76f8\u5173\u672c\u4f53\u5b50\u56fe',
          node_ids: finalNodeIds,
          edge_ids: finalEdgeIds,
          why_matched: [],
        });
      }
      return steps;
    }

    function setSchemaRetrievalPlayback(questionDsl, evidenceBundle) {
      const steps = buildSchemaRetrievalPlaybackSteps(questionDsl, evidenceBundle);
      persistedEvidenceChain = steps;
      persistedEvidenceMap = new Map(steps.map(item => [item.evidence_id, item]));
      evidenceSnapshots = new Map(steps.map(item => [item.evidence_id, normalizeSnapshot({ node_ids: item.node_ids || [], edge_ids: item.edge_ids || [] })]));
      currentPlaybackStepIndex = -1;
      renderEvidenceTimeline(persistedEvidenceChain);
      if (persistedEvidenceChain.length) {
        setFocusPlaybackIndex(0, { replay: false, setStatus: false });
      }
    }

    function handleInstanceQaStageEvent(eventType, payload) {
      const safePayload = payload && typeof payload === 'object' ? payload : {};
      if (eventType === 'trace_summary_ready') {
        currentTraceSummary = safePayload.trace_summary && typeof safePayload.trace_summary === 'object'
          ? safePayload.trace_summary
          : null;
        setQaTraceSummary(currentTraceSummary);
        setQaStatus('\u5df2\u751f\u6210\u56de\u7b54\u6458\u8981');
        return;
      }

      if (eventType === 'question_parsed') {
        const message = safePayload.normalized_query
          ? `\u5df2\u89e3\u6790\u95ee\u9898\uff1a${safePayload.normalized_query}`
          : '\u5df2\u5b8c\u6210\u95ee\u9898\u89e3\u6790';
        setQaStatus(message);
        return;
      }

      if (eventType === 'question_dsl') {
        currentQuestionDsl = safePayload.question_dsl && typeof safePayload.question_dsl === 'object'
          ? safePayload.question_dsl
          : null;
        const anchor = currentQuestionDsl && currentQuestionDsl.anchor && typeof currentQuestionDsl.anchor === 'object'
          ? currentQuestionDsl.anchor
          : {};
        const scenario = currentQuestionDsl && currentQuestionDsl.scenario && typeof currentQuestionDsl.scenario === 'object'
          ? currentQuestionDsl.scenario
          : {};
        setQaStatus(`\u5df2\u8bc6\u522b\u9526\u70b9 ${anchor.entity || '-'} / \u4e8b\u4ef6 ${scenario.event_type || '-'} / \u6a21\u5f0f ${currentQuestionDsl && currentQuestionDsl.mode || '-'}`);
        if ((!playbackController || !playbackController.traceProtocolSeen) && currentEvidenceBundle) {
          setSchemaRetrievalPlayback(currentQuestionDsl, currentEvidenceBundle);
        }
        return;
      }

      if (eventType === 'fact_query_planned') {
        const factQueries = Array.isArray(safePayload.fact_queries) ? safePayload.fact_queries : [];
        setQaStatus(`\u5df2\u751f\u6210 ${factQueries.length} \u6761\u5b9e\u4f8b\u67e5\u8be2\u8ba1\u5212`);
        return;
      }

      if (eventType === 'typedb_query') {
        setQaStatus('\u6b63\u5728\u67e5\u8be2\u5b9e\u4f8b\u6570\u636e');
        return;
      }

      if (eventType === 'typedb_result') {
        const factPack = safePayload.fact_pack && typeof safePayload.fact_pack === 'object' ? safePayload.fact_pack : {};
        const counts = factPack.counts && typeof factPack.counts === 'object' ? factPack.counts : {};
        const total = Object.values(counts).reduce((sum, value) => sum + (Number(value) || 0), 0);
        setQaStatus(total > 0 ? `\u5df2\u547d\u4e2d ${total} \u6761\u5b9e\u4f8b\u7ed3\u679c` : '\u5f53\u524d\u672a\u547d\u4e2d\u5b9e\u4f8b\u7ed3\u679c');
        return;
      }

      if (eventType === 'evidence_bundle_ready') {
        currentEvidenceBundle = safePayload.evidence_bundle && typeof safePayload.evidence_bundle === 'object'
          ? safePayload.evidence_bundle
          : null;
        if ((!playbackController || !playbackController.traceProtocolSeen) && currentQuestionDsl && currentEvidenceBundle) {
          setSchemaRetrievalPlayback(currentQuestionDsl, currentEvidenceBundle);
        }
        setQaStatus('\u5df2\u751f\u6210\u5b9e\u4f53\u68c0\u7d22\u56de\u653e');
        return;
      }

      if (eventType === 'reasoning_done') {
        const reasoning = safePayload.reasoning && typeof safePayload.reasoning === 'object' ? safePayload.reasoning : {};
        const summary = reasoning.summary && typeof reasoning.summary === 'object' ? reasoning.summary : {};
        setQaStatus(`\u5df2\u5b8c\u6210\u63a8\u7406\uff1a${summary.answer_type || 'result'}`);
      }
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
        this.instanceQaProtocolSeen = false;
        this.currentSnapshot = null;
      }

      enqueue(eventType, payload) {
        if (['trace_anchor', 'trace_expand', 'evidence_final'].includes(eventType)) {
          this.traceProtocolSeen = true;
        }
        if (['question_parsed', 'question_dsl', 'fact_query_planned', 'typedb_query', 'typedb_result', 'evidence_bundle_ready', 'reasoning_done', 'trace_summary_ready'].includes(eventType)) {
          this.instanceQaProtocolSeen = true;
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
        if (['question_parsed', 'question_dsl', 'fact_query_planned', 'typedb_query', 'typedb_result', 'evidence_bundle_ready', 'reasoning_done', 'trace_summary_ready'].includes(eventType)) {
          handleInstanceQaStageEvent(eventType, payload || {});
          return;
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
        if (eventType === 'answer_delta') {
          setQaAnswer(payload.answer_text_so_far || payload.delta || '');
          return;
        }
        if (eventType === 'answer_done') {
          if (!this.traceProtocolSeen && !this.instanceQaProtocolSeen) {
            persistFinalEvidence(payload || {});
          }
          setQaAnswer(payload.answer_text || payload.answer || '');
          setQaAnswerTabState(Boolean(payload.used_fallback));
          if (payload.trace_summary) {
            currentTraceSummary = payload.trace_summary;
            setQaTraceSummary(payload.trace_summary);
          }
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
      setQaStatus('\\u6b63\\u5728\\u68c0\\u7d22\\u672c\\u4f53\\u8bc1\\u636e...');
      const eventSource = new EventSource(`/api/qa/stream?q=${encodeURIComponent(trimmedQuestion)}`);
      qaEventSource = eventSource;
      ['question_parsed', 'question_dsl', 'fact_query_planned', 'typedb_query', 'typedb_result', 'evidence_bundle_ready', 'reasoning_done', 'trace_summary_ready', 'trace_anchor', 'trace_expand', 'evidence_final', 'answer_delta', 'answer_done'].forEach(eventType => {
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
        setQaStatus('\\u95ee\\u7b54\\u6d41\\u5df2\\u4e2d\\u65ad');
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
        ? `<div class="detail-card"><div class="section-title">关系摘要</div><div class="summary-box"><strong>入边：</strong>${inRelations.length} &nbsp; <strong>出边：</strong>${outRelations.length}</div><div style="height:8px"></div><div class="pill-row">${relationTypes.length ? relationTypes.map(item => `<span class="pill">${item}</span>`).join('') : '<span class=\"muted\">\u65e0</span>'}</div><div class="actions"><button id="toggle-relations">展开关系明细</button></div></div><div id="relation-details" class="hidden">${renderRelations('\u5165\u8fb9\u660e\u7ec6', inRelations)}${renderRelations('\u51fa\u8fb9\u660e\u7ec6', outRelations)}</div>`
        : '';
      const groupChipHtml = attrs.display_group ? `<span class="group-chip">${attrs.display_group}</span>` : '';
      const htmlContent = `
        <div class="hero-card">
          <div class="hero-title">${data.display_name}</div>
          <div class="hero-subtitle">
            <span class="type-chip">${data.type}</span>
            ${groupChipHtml}
          </div>
        </div>
        ${renderSection('\u4e2d\u6587\u91ca\u4e49', `<p class=\"detail-text\">${attrs.chinese_description || attrs.description}</p>`, Boolean(attrs.chinese_description || attrs.description))}
        ${renderSection('\u8bed\u4e49\u5b9a\u4e49', `<p class=\"detail-text\">${attrs.semantic_definition}</p>`, Boolean(attrs.semantic_definition))}
        ${renderSection('\u5173\u952e\u5c5e\u6027', formatPropertyLines(attrs.key_property_lines || []), hasStringList(attrs.key_property_lines))}
        ${renderSection('\u72b6\u6001\u5efa\u8bae', formatPropertyLines(attrs.status_value_lines || []), hasStringList(attrs.status_value_lines))}
        ${renderSection('\u89c4\u5219\u7ea6\u675f', formatStringList(attrs.rule_lines || attrs.rules || []), hasStringList(attrs.rule_lines || attrs.rules))}
        ${renderSection('\u8bf4\u660e', formatStringList(attrs.note_lines || attrs.notes || []), hasStringList(attrs.note_lines || attrs.notes))}
        ${relationSummaryHtml}
      `;
      showInlineDetailCard(node, htmlContent);
      const button = document.getElementById('toggle-relations');
      if (button) {
        button.addEventListener('click', () => {
          const details = document.getElementById('relation-details');
          details.classList.toggle('hidden');
          button.textContent = details.classList.contains('hidden') ? '展开关系明细' : '收起关系明细';
          repositionDetailCard();
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
        ${renderSection('\u8bf4\u660e', `<p class=\"detail-text\">${attrs.description}</p>`, Boolean(attrs.description))}
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
      if (playbackController) {
        playbackController.currentSnapshot = normalizeSnapshot({
          node_ids: neighborhood.nodes().map(item => item.id()),
          edge_ids: neighborhood.edges().map(item => item.id()),
        });
      }
      cy.elements(':visible').addClass('dimmed');
      neighborhood.removeClass('dimmed');
      neighborhood.addClass('highlighted');
      setFilteringState(true);
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
        resetToExplorationMode({ fit: false, resetInputs: false });
      }
    });

    cy.on('pan zoom resize', repositionDetailCard);

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

    traceResetButton.addEventListener('click', () => {
      resetToExplorationMode({ fit: false, resetInputs: false });
    });

    resetButton.addEventListener('click', () => {
      if (qaEventSource) {
        qaEventSource.close();
        qaEventSource = null;
      }
      resetToExplorationMode();
    });

    qaAssistantToggle.addEventListener('click', () => {
      qaAnswerPanel.classList.toggle('hidden');
    });

    qaTabAnswer.addEventListener('click', () => setQaActiveTab('answer'));
    qaTabEvidence.addEventListener('click', () => setQaActiveTab('evidence'));
    qaTabFocus.addEventListener('click', () => setQaActiveTab('focus'));
    qaPlaybackPrev.addEventListener('click', () => setFocusPlaybackIndex(currentPlaybackStepIndex - 1, { replay: true, openTab: true }));
    qaPlaybackReplay.addEventListener('click', () => setFocusPlaybackIndex(currentPlaybackStepIndex >= 0 ? currentPlaybackStepIndex : persistedEvidenceChain.length - 1, { replay: true, openTab: true }));
    qaPlaybackNext.addEventListener('click', () => setFocusPlaybackIndex(currentPlaybackStepIndex + 1, { replay: true, openTab: true }));

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
      setQaActiveTab('answer');
      cy.fit(cy.elements(':visible'), 70);
    });
  </script>
</body>
</html>"""
    return (
        template
        .replace('__TITLE__', html.escape(title))
        .replace('__RELATION_LEGEND__', relation_legend_html)
        .replace('__DEFAULT_PANEL__', default_panel_html)
        .replace('__DEFAULT_PANEL_JSON__', json.dumps(default_panel_html, ensure_ascii=False))
        .replace('__PAYLOAD__', payload_json)
        .replace('__CYTOSCAPE_BUNDLE__', cytoscape_bundle)
    )



def export_interactive_graph_html(graph: OntologyGraph, output_html_path: str | Path, title: str = 'Interactive Ontology Graph') -> Path:
    output_path = Path(output_html_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(build_interactive_graph_html(graph, title=title), encoding='utf-8')
    return output_path



def export_graph_pdf(graph: OntologyGraph, output_pdf_path: str | Path, title: str = 'Ontology Definition Graph') -> Path:
    output_path = Path(output_pdf_path).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    html_text = build_interactive_graph_html(graph, title=title)
    browser = _find_browser_executable()
    with TemporaryDirectory() as temp_dir:
        html_path = Path(temp_dir) / 'ontology_definition_graph.html'
        html_path.write_text(html_text, encoding='utf-8')
        subprocess.run(
            [
                str(browser),
                '--headless=new',
                '--disable-gpu',
                '--run-all-compositor-stages-before-draw',
                '--virtual-time-budget=20000',
                f'--print-to-pdf={output_path}',
                html_path.as_uri(),
            ],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    return output_path



def _find_browser_executable() -> Path:
    for candidate in BROWSER_CANDIDATES:
        if candidate.exists():
            return candidate
    raise FileNotFoundError('No supported browser executable found for PDF export.')



def build_graph_payload(graph: OntologyGraph) -> dict[str, object]:
    mainline_order = _flatten_mainline(graph.metadata.get('mainline', []))
    objects = [obj for obj in graph.objects.values() if obj.type != 'DerivedMetric']
    metric_nodes = [obj for obj in graph.objects.values() if obj.type == 'DerivedMetric']
    positions = _build_positions(objects, metric_nodes, mainline_order, graph.relations)

    relation_types = list(dict.fromkeys(relation.relation for relation in graph.relations))
    relation_legend = [
        {'relation': relation, 'translation': RELATION_TRANSLATIONS.get(relation, '未翻译')}
        for relation in relation_types
    ]

    elements: list[dict[str, object]] = []
    metric_node_ids: list[str] = []
    metric_edge_ids: list[str] = []

    for obj in objects:
        attrs = dict(obj.attributes)
        raw_group = attrs.get('group', '')
        display_group = _strip_group_prefix(raw_group)
        attrs['display_group'] = display_group
        attrs['key_property_lines'] = _named_items_to_lines(attrs.get('key_properties'))
        attrs['status_value_lines'] = _named_items_to_lines(attrs.get('status_values'))
        attrs['rule_lines'] = _string_items_to_lines(attrs.get('rules'))
        attrs['note_lines'] = _string_items_to_lines(attrs.get('notes'))
        label = f"{obj.name}\n{display_group}" if display_group else obj.name
        search_tokens = [obj.name]
        if display_group:
            search_tokens.append(display_group)
        if raw_group:
            search_tokens.append(raw_group)
        search_tokens.append(json.dumps(attrs, ensure_ascii=False))
        elements.append(
            {
                'data': {
                    'id': obj.id,
                    'label': label,
                    'display_name': obj.name,
                    'type': obj.type,
                    'attributes': attrs,
                    'color': _color_for_group(display_group, obj.type),
                    'search_text': ' '.join(search_tokens).lower(),
                },
                'position': positions[obj.id],
            }
        )

    if metric_nodes:
        metric_names = [metric.name for metric in metric_nodes]
        elements.append(
            {
                'data': {
                    'id': METRIC_GROUP_ID,
                    'label': '关键派生指标',
                    'display_name': '关键派生指标',
                    'type': 'MetricGroup',
                    'attributes': {
                        'display_group': '关键派生指标',
                        'description': '点击图中该节点可原地展开或收起详细指标。',
                        'metric_names': metric_names,
                    },
                    'color': DEFAULT_TYPE_COLORS['MetricGroup'],
                    'search_text': ('关键派生指标 ' + ' '.join(metric_names)).lower(),
                },
                'position': positions[METRIC_GROUP_ID],
            }
        )
        for index, metric in enumerate(metric_nodes, start=1):
            attrs = dict(metric.attributes)
            attrs['display_group'] = '关键派生指标'
            attrs['rule_lines'] = _string_items_to_lines(attrs.get('rules'))
            attrs['note_lines'] = _string_items_to_lines(attrs.get('notes'))
            metric_node_ids.append(metric.id)
            elements.append(
                {
                    'data': {
                        'id': metric.id,
                        'label': metric.name,
                        'display_name': metric.name,
                        'type': metric.type,
                        'attributes': attrs,
                        'color': DEFAULT_TYPE_COLORS['DerivedMetric'],
                        'search_text': f"{metric.name} 关键派生指标 {json.dumps(attrs, ensure_ascii=False)}".lower(),
                    },
                    'classes': 'metric-hidden',
                    'position': positions[metric.id],
                }
            )
            metric_edge_id = f'metric_edge:{index}'
            metric_edge_ids.append(metric_edge_id)
            elements.append(
                {
                    'data': {
                        'id': metric_edge_id,
                        'source': METRIC_GROUP_ID,
                        'target': metric.id,
                        'label': '',
                        'relation': '__METRIC__',
                        'synthetic': True,
                        'edgeColor': '#c4b5fd',
                        'lineStyle': 'dashed',
                        'width': 2,
                    },
                    'classes': 'metric-hidden',
                }
            )

    for index, relation in enumerate(graph.relations, start=1):
        elements.append(
            {
                'data': {
                    'id': f'e{index}',
                    'source': relation.source_id,
                    'target': relation.target_id,
                    'label': relation.relation,
                    'relation': relation.relation,
                    'attributes': dict(relation.attributes),
                    'synthetic': False,
                    'edgeColor': '#94a3b8',
                    'lineStyle': 'solid',
                    'width': 3,
                }
            }
        )

    return {
        'elements': elements,
        'relationTypes': relation_types,
        'relationLegend': relation_legend,
        'metricGroupId': METRIC_GROUP_ID,
        'metricNodeIds': metric_node_ids,
        'metricEdgeIds': metric_edge_ids,
    }



def _build_positions(objects: list, metric_nodes: list, mainline_order: list[str], relations: list) -> dict[str, dict[str, float]]:
    grouped: dict[str, list] = {}
    group_order = ['项目与目标层', '空间层', '设备与物流层', '活动与排期层', '施工执行层', '决策与解释层']
    for obj in objects:
        display_group = _strip_group_prefix(obj.attributes.get('group', '')) or '未分组'
        grouped.setdefault(display_group, []).append(obj)

    ordered_groups = [name for name in group_order if name in grouped]
    ordered_groups.extend(sorted(name for name in grouped if name not in ordered_groups))

    mainline_rank = {name: index for index, name in enumerate(mainline_order)}
    positions: dict[str, dict[str, float]] = {}
    start_x = 180.0
    lane_gap = 330.0
    center_y = 320.0
    node_gap_y = 150.0

    for group_index, group_name in enumerate(ordered_groups):
        items = grouped[group_name]
        items.sort(key=lambda obj: (0 if obj.name in mainline_rank else 1, mainline_rank.get(obj.name, 999), obj.name))
        offsets = _symmetric_offsets(len(items), node_gap_y)
        x = start_x + group_index * lane_gap
        for obj, offset in zip(items, offsets):
            positions[obj.id] = {'x': x, 'y': center_y + offset}

    if metric_nodes:
        metric_group_x = start_x + max(len(ordered_groups), 1) * lane_gap
        metric_group_y = center_y
        positions[METRIC_GROUP_ID] = {'x': metric_group_x, 'y': metric_group_y}
        for index, metric in enumerate(metric_nodes):
            row = index // 2
            col = index % 2
            x = metric_group_x + (-110 if col == 0 else 110)
            y = metric_group_y + 130 + row * 110
            positions[metric.id] = {'x': x, 'y': y}

    return positions


def _guess_anchor_id(obj, objects_by_name: dict[str, object], fallback_mainline: str) -> str:
    display_group = _strip_group_prefix(obj.attributes.get('group', ''))
    preferred_names = {
        '项目与目标层': ['Project'],
        '空间层': ['Room', 'PoDPosition', 'Building'],
        '设备与物流层': ['PoD', 'Building'],
        '活动与排期层': ['ActivityInstance', 'PoD'],
        '施工执行层': ['ActivityInstance', 'PoD'],
        '决策与解释层': ['PoD', 'ActivityInstance'],
    }.get(display_group, [])
    for name in preferred_names:
        candidate = objects_by_name.get(name)
        if candidate is not None:
            return candidate.id
    return fallback_mainline


def _balanced_angle_offsets(count: int, spread: float) -> list[float]:
    if count <= 0:
        return []
    if count == 1:
        return [0.0]
    if count == 2:
        return [-0.35, 0.35]
    step = spread / max(count - 1, 1)
    start = -spread / 2
    return [start + index * step for index in range(count)]


def _flatten_mainline(raw_mainline: list[str]) -> list[str]:
    names: list[str] = []
    for item in raw_mainline:
        parts = [part.strip() for part in re.split(r'/', item) if part.strip() and part.strip() != '---']
        names.extend(parts)
    return names


def _symmetric_offsets(count: int, gap: float) -> list[float]:
    if count <= 0:
        return []
    offsets = [0.0]
    for index in range(1, count):
        step = ((index + 1) // 2) * gap
        offsets.append(-step if index % 2 == 1 else step)
    return offsets


def _strip_group_prefix(group: str) -> str:
    return re.sub(r'^\d+(?:\.\d+)?\s*', '', group or '').strip()



def _named_items_to_lines(values: object) -> list[str]:
    if not isinstance(values, list):
        return []
    lines: list[str] = []
    for item in values:
        if isinstance(item, dict):
            name = str(item.get('name', '') or '').strip()
            description = str(item.get('description', '') or '').strip()
            if name and description:
                lines.append(f'{name}：{description}')
            elif name:
                lines.append(name)
            elif description:
                lines.append(description)
            continue
        value = str(item or '').strip()
        if value:
            lines.append(value)
    return lines



def _string_items_to_lines(values: object) -> list[str]:
    if not isinstance(values, list):
        return []
    return [value for value in (str(item or '').strip() for item in values) if value]



def _color_for_group(display_group: str, node_type: str) -> str:
    palette = {
        '项目与目标层': '#f59e0b',
        '空间层': '#0ea5e9',
        '设备与物流层': '#14b8a6',
        '活动与排期层': '#6366f1',
        '施工执行层': '#10b981',
        '决策与解释层': '#ef4444',
        '关键派生指标': '#7c3aed',
    }
    return palette.get(display_group, DEFAULT_TYPE_COLORS.get(node_type, '#475569'))
