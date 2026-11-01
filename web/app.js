'use strict';

const $ = (id) => document.getElementById(id);
let files = [];
let timer = null;
let startedAt = null;

function textNode(tag, value, className) {
  const node = document.createElement(tag);
  node.textContent = String(value ?? '');
  if (className) node.className = className;
  return node;
}

function selectFile(path, fromLine, toLine) {
  const file = files.find((item) => item.path === path || path.endsWith('/' + item.path));
  if (!file) return;
  $('source-title').textContent = file.path + (fromLine ? ` · lines ${fromLine}–${toLine || fromLine}` : '');
  const lines = file.text.split('\n');
  const source = $('source-content');
  const start = Number.isInteger(fromLine) && fromLine > 0 ? fromLine : 0;
  const end = Number.isInteger(toLine) && toLine >= start ? toLine : start;
  source.replaceChildren(...lines.map((line, index) => {
    const row = textNode('span', '', 'source-line');
    const number = textNode('span', String(index + 1).padStart(3), 'line-number');
    number.setAttribute('aria-hidden', 'true');
    row.append(number, document.createTextNode('  ' + line));
    if (start && index + 1 >= start && index + 1 <= end) row.classList.add('cited');
    return row;
  }));
  for (const button of $('file-list').querySelectorAll('button')) {
    button.classList.toggle('selected', button.dataset.path === file.path);
    button.setAttribute('aria-pressed', String(button.dataset.path === file.path));
  }
  const cited = source.querySelector('.cited');
  source.scrollTop = cited ? Math.max(0, cited.offsetTop - 12) : 0;
  if (cited) source.focus();
}

async function loadEvidence() {
  const response = await fetch('/api/evidence');
  if (!response.ok) throw new Error('Could not load the local evidence fixture.');
  const data = await response.json();
  files = Array.isArray(data.files) ? data.files : [];
  $('file-count').textContent = String(files.length).padStart(2, '0');
  $('file-list').replaceChildren();
  for (const file of files) {
    const button = textNode('button', file.path, 'file-button');
    button.type = 'button';
    button.dataset.path = file.path;
    button.addEventListener('click', () => selectFile(file.path));
    $('file-list').append(button);
  }
  if (files[0]) selectFile(files[0].path);
  else $('file-list').append(textNode('p', 'No fixture files available yet.', 'muted'));
}

function setList(section, target, values) {
  const items = Array.isArray(values) ? values : [];
  $(section).hidden = items.length === 0;
  $(target).replaceChildren(...items.map((item) => textNode('li', typeof item === 'string' ? item : JSON.stringify(item))));
}

function renderRun(run) {
  const report = run.report;
  $('report').hidden = !report;
  const toolEvents = Array.isArray(run.tool_events) ? run.tool_events : [];
  $('tool-events').replaceChildren(...toolEvents.map((event) => {
    const name = event.tool_name || event.name || event.tool || 'tool';
    const suffix = event.status ? ` · ${event.status}` : '';
    return textNode('li', name + suffix);
  }));
  if (!toolEvents.length) $('tool-events').append(textNode('li', 'No recorded tool calls.', 'muted'));
  const semantic = run.semantic_validation;
  const semanticValid = semantic === true || semantic?.valid === true || semantic?.passed === true;
  $('validation').textContent = run.typed_output_valid && semanticValid
    ? 'Typed report and evidence references passed the recorded checks.'
    : 'Validation is incomplete or needs review. Read the run details before relying on this handoff.';
  $('validation').classList.toggle('verified', Boolean(run.typed_output_valid && semanticValid));
  const modelName = typeof run.model === 'string' ? run.model : run.model?.name || 'Unknown';
  const details = [['Model', modelName], ['SDK', typeof run.sdk === 'string' ? run.sdk : JSON.stringify(run.sdk || {})], ['Run', run.run_id || run.runtime?.run_id || 'Not recorded'], ['Time', run.elapsed_ms ? `${(run.elapsed_ms / 1000).toFixed(1)}s` : 'Not recorded'], ['Checks', JSON.stringify(semantic ?? {})]];
  $('run-details').replaceChildren(...details.flatMap(([key, value]) => [textNode('dt', key), textNode('dd', value)]));
  if (!report) return;
  const claims = Array.isArray(report.claims) ? report.claims : [];
  const counts = { supported: 0, contradicted: 0, unknown: 0 };
  for (const claim of claims) counts[claim.status in counts ? claim.status : 'unknown']++;
  $('claim-summary').textContent = `${counts.supported} supported · ${counts.contradicted} contradicted · ${counts.unknown} unknown`;
  $('claims').replaceChildren();
  for (const claim of claims) {
    const card = textNode('article', '', 'claim');
    const top = textNode('div', '', 'claim-top');
    const status = ['supported', 'contradicted', 'unknown'].includes(claim.status) ? claim.status : 'unknown';
    top.append(textNode('h3', claim.title || claim.id), textNode('span', status, `badge ${status === 'supported' ? 'positive' : status === 'contradicted' ? 'negative' : 'attention'}`));
    card.append(top, textNode('p', claim.rationale));
    for (const refId of claim.evidence_refs || []) {
      const ref = (report.references || []).find((item) => item.id === refId);
      if (!ref) continue;
      const button = textNode('button', `${ref.source}:${ref.line_start}–${ref.line_end}`, 'reference-button');
      button.type = 'button';
      button.addEventListener('click', () => selectFile(ref.source, ref.line_start, ref.line_end));
      card.append(button);
    }
    $('claims').append(card);
  }
  setList('unknowns-section', 'unknowns', report.unknowns);
  setList('risks-section', 'risks', report.risks);
}

async function refreshState() {
  const response = await fetch('/api/state');
  if (!response.ok) throw new Error('The local review service is unavailable.');
  const state = await response.json();
  const running = state.phase === 'running';
  $('run-button').disabled = running;
  $('run-button').textContent = running ? 'Review in progress…' : 'Run evidence review ↗';
  $('empty-state').hidden = running || Boolean(state.run);
  $('running-state').hidden = !running;
  $('failure-state').hidden = state.phase !== 'failed';
  $('run-status').textContent = running ? 'Reading evidence' : state.phase === 'succeeded' ? 'Review ready' : state.phase === 'failed' ? 'Run failed' : 'Not run';
  $('run-status').className = `badge ${state.phase === 'succeeded' ? 'positive' : state.phase === 'failed' ? 'negative' : 'neutral'}`;
  if (running) {
    $('report').hidden = true;
    startedAt = state.started_at || startedAt;
    const seconds = startedAt ? Math.max(0, Math.floor((Date.now() - new Date(startedAt).getTime()) / 1000)) : 0;
    $('elapsed').textContent = `${seconds}s`;
    timer = setTimeout(() => refreshState().catch(showError), 1600);
  } else {
    clearTimeout(timer);
    if (state.run) renderRun(state.run);
    if (state.phase === 'failed') {
      const error = state.run?.error;
      $('failure-state').textContent = typeof error === 'string' ? error : error?.message || 'The real model run did not complete. No successful handoff is claimed.';
    }
  }
}

function showError(error) {
  clearTimeout(timer);
  $('run-button').disabled = false;
  $('running-state').hidden = true;
  $('failure-state').hidden = false;
  $('failure-state').textContent = error.message;
  $('run-status').textContent = 'Connection unavailable';
  $('run-status').className = 'badge negative';
}

$('run-button').addEventListener('click', async () => {
  $('run-button').disabled = true;
  $('failure-state').hidden = true;
  try {
    const response = await fetch('/api/run', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: '{}' });
    if (!response.ok && response.status !== 409) throw new Error('The review could not be started.');
    startedAt = new Date().toISOString();
    clearTimeout(timer);
    await refreshState();
  } catch (error) { showError(error); }
});

Promise.all([loadEvidence(), refreshState()]).catch(showError);
