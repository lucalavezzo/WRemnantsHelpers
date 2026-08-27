<?php
// Study logbook viewer. Lives at ~/public_html/alphaS/studies/index.php, next to one
// symlink per published study pointing back into WRemnantsHelpers/studies/.
//
// Nothing here is generated ahead of time: the tree is globbed at request time and the
// markdown is fetched live by the browser, so a logbook edit shows up on reload and a new
// task directory shows up as soon as a worker creates it.
//
// Source of truth: WRemnantsHelpers/scripts/templates/study_viewer.php (installed by
// scripts/webpublish_study.sh). Edit it there, not here.

function fm_parse($path) {
    $out = ['title' => null, 'status' => null, 'updated' => null, 'study' => null, 'task' => null];
    $fh = @fopen($path, 'r');
    if (!$fh) return $out;
    $head = fread($fh, 4096);
    fclose($fh);
    if ($head === false) return $out;
    $head = str_replace("\r\n", "\n", $head);
    if (strncmp($head, "---\n", 4) === 0) {
        $end = strpos($head, "\n---", 3);
        $block = $end === false ? $head : substr($head, 4, $end - 3);
        foreach (['title', 'status', 'updated', 'study'] as $k) {
            if (preg_match('/^' . $k . ':[ \t]*(.*)$/m', $block, $m)) {
                $v = trim(preg_replace('/\s+#.*$/', '', $m[1]));
                if ($v !== '') $out[$k] = $v;
            }
        }
    }
    // no frontmatter title -> first markdown heading; no updated -> file mtime
    if ($out['title'] === null && preg_match('/^#\s+(.+)$/m', $head, $m)) {
        $out['title'] = trim(preg_replace('/\s+—\s+logbook\s*$/u', '', $m[1]));
    }
    if ($out['updated'] === null) {
        $t = @filemtime($path);
        if ($t) $out['updated'] = date('Y-m-d', $t);
    }
    if (preg_match('/^\*\*Task:\*\*\s*(.+)$/m', $head, $m)) $out['task'] = trim($m[1]);
    return $out;
}

function status_norm($s) {
    $s = strtolower(trim((string)$s));
    $map = ['running' => 'active', 'completed' => 'done', 'complete' => 'done',
            'finished' => 'done', 'closed' => 'done'];
    if (isset($map[$s])) return $map[$s];
    return in_array($s, ['active', 'done', 'paused', 'abandoned'], true) ? $s : '';
}

$RESERVED = ['scripts', 'logs', 'slides', 'docs', 'inputs', 'sessions', '__pycache__',
             '_TEMPLATE', 'vendor'];

$studies = [];
foreach (glob('*/LOGBOOK.md') as $p) {
    $slug = dirname($p);
    if (in_array($slug, $RESERVED, true)) continue;
    $fm = fm_parse($p);
    $studies[$slug] = [
        'slug'    => $slug,
        'title'   => $fm['title'] ?: $slug,
        'status'  => status_norm($fm['status']),
        'updated' => $fm['updated'] ?: '',
        'tasks'   => [],
    ];
}
// a task dir is any subdir of a study that contains a LOGBOOK.md
foreach (glob('*/*/LOGBOOK.md') as $p) {
    $parts = explode('/', $p);
    list($slug, $task) = [$parts[0], $parts[1]];
    if (!isset($studies[$slug]) || in_array($task, $RESERVED, true)) continue;
    $fm = fm_parse($p);
    $studies[$slug]['tasks'][] = [
        'slug'    => $task,
        'title'   => $fm['title'] ?: $task,
        'status'  => status_norm($fm['status']),
        'updated' => $fm['updated'] ?: '',
        'task'    => $fm['task'] ?: '',
        'plots'   => count(glob("$slug/$task/*.png")),
    ];
}
foreach ($studies as &$s) {
    usort($s['tasks'], function ($a, $b) { return strcmp($b['slug'], $a['slug']); });
}
unset($s);
uasort($studies, function ($a, $b) {
    $c = strcmp($b['updated'], $a['updated']);
    return $c !== 0 ? $c : strcmp($a['slug'], $b['slug']);
});
$TREE = json_encode(array_values($studies), JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);
?>
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>alphaS study logbooks</title>
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css">
<style>
  :root {
    color-scheme: light;
    --surface-1: #fcfcfb; --page: #f9f9f7;
    --text-1: #0b0b0b; --text-2: #52514e; --muted: #898781;
    --border: rgba(11,11,11,0.10); --rule: #e1e0d9;
    --accent: #2a78d6; --chip-on: rgba(42,120,214,0.12);
    --hover-wash: rgba(11,11,11,0.04);
    --ok: #1c7c4a; --warn: #9a6a00; --bad: #a01a2e;
    --code-bg: rgba(11,11,11,0.045);
  }
  @media (prefers-color-scheme: dark) {
    :root:where(:not([data-theme="light"])) {
      color-scheme: dark;
      --surface-1: #1a1a19; --page: #0d0d0d;
      --text-1: #ffffff; --text-2: #c3c2b7; --muted: #898781;
      --border: rgba(255,255,255,0.10); --rule: #2c2c2a;
      --accent: #3987e5; --chip-on: rgba(57,135,229,0.22);
      --hover-wash: rgba(255,255,255,0.06);
      --ok: #4bbd7d; --warn: #d6a341; --bad: #f2415a;
      --code-bg: rgba(255,255,255,0.06);
    }
  }
  :root[data-theme="dark"] {
    color-scheme: dark;
    --surface-1: #1a1a19; --page: #0d0d0d;
    --text-1: #ffffff; --text-2: #c3c2b7; --muted: #898781;
    --border: rgba(255,255,255,0.10); --rule: #2c2c2a;
    --accent: #3987e5; --chip-on: rgba(57,135,229,0.22);
    --hover-wash: rgba(255,255,255,0.06);
    --ok: #4bbd7d; --warn: #d6a341; --bad: #f2415a;
    --code-bg: rgba(255,255,255,0.06);
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; height: 100%; }
  body {
    background: var(--page); color: var(--text-1);
    font: 15px/1.62 -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
    display: grid; grid-template-columns: 310px minmax(0,1fr);
  }
  a { color: var(--accent); text-decoration: none; }
  a:hover { text-decoration: underline; }

  /* ---- sidebar ---- */
  #side {
    background: var(--surface-1); border-right: 1px solid var(--border);
    height: 100vh; overflow-y: auto; padding: 14px 0 40px;
  }
  #side h1 {
    font-size: 12px; letter-spacing: .09em; text-transform: uppercase;
    color: var(--muted); margin: 0 16px 10px; font-weight: 600;
  }
  #filter {
    width: calc(100% - 32px); margin: 0 16px 12px; padding: 6px 9px;
    font: inherit; font-size: 13px; color: var(--text-1);
    background: var(--page); border: 1px solid var(--border); border-radius: 6px;
  }
  .study { margin-bottom: 2px; }
  .study > a.slink {
    display: block; padding: 6px 16px; color: var(--text-1); font-weight: 600;
    font-size: 13.5px; border-left: 3px solid transparent;
  }
  .study > a.slink:hover { background: var(--hover-wash); text-decoration: none; }
  .study > a.slink.on { background: var(--chip-on); border-left-color: var(--accent); }
  .smeta { display: block; font-weight: 400; font-size: 11.5px; color: var(--muted); }
  .tasks { margin: 0 0 8px; }
  .tasks a {
    display: block; padding: 4px 16px 4px 30px; font-size: 12.5px; color: var(--text-2);
    border-left: 3px solid transparent;
  }
  .tasks a:hover { background: var(--hover-wash); text-decoration: none; }
  .tasks a.on { background: var(--chip-on); border-left-color: var(--accent); color: var(--text-1); }
  .badge {
    display: inline-block; font-size: 10px; padding: 0 5px; border-radius: 4px;
    border: 1px solid currentColor; margin-left: 5px; vertical-align: 1px;
  }
  .st-active { color: var(--accent); } .st-done { color: var(--ok); }
  .st-paused { color: var(--warn); }  .st-abandoned { color: var(--muted); }
  .empty { color: var(--muted); font-size: 12.5px; padding: 0 16px; }

  /* ---- main ---- */
  #main { height: 100vh; overflow-y: auto; }
  #wrap { max-width: 900px; margin: 0 auto; padding: 26px 34px 120px; }
  #crumb { font-size: 12.5px; color: var(--muted); margin-bottom: 6px; }
  #tools { float: right; font-size: 12px; }
  #tools a, #tools button {
    margin-left: 10px; font: inherit; font-size: 12px; color: var(--text-2);
    background: none; border: none; cursor: pointer; padding: 0;
  }
  #tools a:hover, #tools button:hover { color: var(--accent); }
  #doc { word-wrap: break-word; }
  #doc h1 { font-size: 24px; margin: 6px 0 14px; line-height: 1.25; }
  #doc h2 {
    font-size: 17px; margin: 30px 0 10px; padding-bottom: 5px;
    border-bottom: 1px solid var(--rule);
  }
  #doc h3 { font-size: 14.5px; margin: 20px 0 6px; color: var(--text-2); }
  #doc blockquote {
    margin: 12px 0; padding: 10px 14px; border-left: 3px solid var(--accent);
    background: var(--chip-on); border-radius: 0 6px 6px 0;
  }
  #doc blockquote p:first-child { margin-top: 0; } #doc blockquote p:last-child { margin-bottom: 0; }
  #doc code { background: var(--code-bg); padding: 1px 4px; border-radius: 4px; font-size: 12.5px; }
  #doc pre {
    background: var(--code-bg); padding: 11px 13px; border-radius: 7px;
    overflow-x: auto; font-size: 12.5px; line-height: 1.5;
  }
  #doc pre code { background: none; padding: 0; }
  #doc table { border-collapse: collapse; font-size: 13px; margin: 14px 0; display: block; overflow-x: auto; }
  #doc th, #doc td { border: 1px solid var(--rule); padding: 5px 9px; text-align: left; }
  #doc th { background: var(--code-bg); }
  #doc img { max-width: 100%; height: auto; border-radius: 5px; border: 1px solid var(--border); }
  #doc hr { border: none; border-top: 1px solid var(--rule); margin: 26px 0; }
  #doc ul, #doc ol { padding-left: 22px; }
  #doc li { margin: 2px 0; }
  #doc a[href$=".png"], #doc a[href$=".pdf"] { white-space: nowrap; }
  #toc {
    position: fixed; top: 26px; right: 14px; width: 190px; max-height: 78vh;
    overflow-y: auto; font-size: 11.5px; line-height: 1.5; color: var(--muted);
    border-left: 1px solid var(--border); padding-left: 10px;
  }
  #toc a { color: var(--text-2); display: block; padding: 1px 0; }
  #toc a.h3 { padding-left: 10px; color: var(--muted); }
  @media (max-width: 1400px) { #toc { display: none; } }
  @media (max-width: 820px) {
    body { grid-template-columns: 1fr; }
    #side { height: auto; max-height: 42vh; }
    #main { height: auto; }
    #wrap { padding: 18px 16px 80px; }
  }
</style>
</head>
<body>
<nav id="side">
  <h1>alphaS studies</h1>
  <input id="filter" type="search" placeholder="filter studies…" autocomplete="off">
  <div id="tree"></div>
</nav>
<div id="main"><div id="wrap">
  <div id="tools">
    <a id="raw" href="#" title="the markdown source">raw</a>
    <a id="plots" href="#" title="the plot gallery for this directory">plots ↗</a>
    <button id="theme" title="light / dark">◐</button>
  </div>
  <div id="crumb"></div>
  <div id="doc"></div>
</div><div id="toc"></div></div>

<script src="marked.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js"></script>
<script>
const TREE = <?php echo $TREE ?: '[]'; ?>;

/* ---------- theme ---------- */
const themeBtn = document.getElementById('theme');
try { const t = localStorage.getItem('logbook-theme'); if (t) document.documentElement.dataset.theme = t; } catch (e) {}
themeBtn.onclick = () => {
  const cur = document.documentElement.dataset.theme;
  const isDark = cur ? cur === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches;
  const next = isDark ? 'light' : 'dark';
  document.documentElement.dataset.theme = next;
  try { localStorage.setItem('logbook-theme', next); } catch (e) {}
};

/* ---------- sidebar ---------- */
function badge(st) { return st ? `<span class="badge st-${st}">${st}</span>` : ''; }

function renderTree(q) {
  const host = document.getElementById('tree');
  q = (q || '').toLowerCase();
  const hit = s => !q || s.slug.toLowerCase().includes(q) || (s.title || '').toLowerCase().includes(q)
                 || s.tasks.some(t => (t.slug + ' ' + t.title).toLowerCase().includes(q));
  const shown = TREE.filter(hit);
  if (!TREE.length) {
    host.innerHTML = '<p class="empty">No study is published yet.<br><br>' +
      'Publish one with<br><code>scripts/webpublish_study.sh &lt;slug&gt;</code></p>';
    return;
  }
  if (!shown.length) { host.innerHTML = '<p class="empty">nothing matches</p>'; return; }
  host.innerHTML = shown.map(s => `
    <div class="study">
      <a class="slink" data-h="${s.slug}" href="#${s.slug}">${esc(s.title)}${badge(s.status)}
        <span class="smeta">${s.slug}${s.updated ? ' · ' + s.updated : ''}</span></a>
      <div class="tasks">${s.tasks.map(t => `
        <a data-h="${s.slug}/${t.slug}" href="#${s.slug}/${t.slug}"
           title="${esc(t.task || t.title)}">${esc(t.title)}${badge(t.status)}
           ${t.plots ? `<span class="smeta">${t.slug} · ${t.plots} plot${t.plots > 1 ? 's' : ''}</span>`
                     : `<span class="smeta">${t.slug}</span>`}</a>`).join('')}</div>
    </div>`).join('');
  markActive();
}
function markActive() {
  const h = location.hash.slice(1);
  document.querySelectorAll('#tree [data-h]').forEach(a => a.classList.toggle('on', a.dataset.h === h));
}
function esc(s) {
  return String(s == null ? '' : s).replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));
}
document.getElementById('filter').addEventListener('input', e => renderTree(e.target.value));

/* ---------- math: pull it out before markdown, put it back after ----------
   marked would eat the _ and ^ inside $p_T^{\ell\ell}$ as emphasis, so math spans are
   replaced by placeholders first. Code fences/spans are matched by the same regex but
   left untouched, so a $VAR in a shell snippet is never treated as math. */
function protectMath(src, store) {
  const re = /(```[\s\S]*?```|~~~[\s\S]*?~~~|`[^`\n]*`)|(\$\$[\s\S]+?\$\$)|(\\\[[\s\S]+?\\\])|(\$(?!\s)(?:\\.|[^$\\\n])+?\$)|(\\\((?:[\s\S]+?)\\\))/g;
  return src.replace(re, (m, code, dd, dbr, inl, ibr) => {
    if (code) return m;
    let tex, display = false;
    if (dd)       { tex = dd.slice(2, -2);  display = true; }
    else if (dbr) { tex = dbr.slice(2, -2); display = true; }
    else if (inl) { tex = inl.slice(1, -1); }
    else          { tex = ibr.slice(2, -2); }
    store.push({tex, display, raw: m});
    return '@@MATH' + (store.length - 1) + '@@';
  });
}
function restoreMath(html, store) {
  return html.replace(/@@MATH(\d+)@@/g, (_, i) => {
    const m = store[+i];
    if (!m) return '';
    if (typeof katex === 'undefined') return esc(m.raw);   // CDN blocked -> show source
    try {
      return katex.renderToString(m.tex, {displayMode: m.display, throwOnError: false});
    } catch (e) { return esc(m.raw); }
  });
}

/* ---------- render ---------- */
marked.setOptions({gfm: true, breaks: false, mangle: false, headerIds: false});

async function load() {
  const hash = decodeURIComponent(location.hash.slice(1));
  const doc = document.getElementById('doc');
  const crumb = document.getElementById('crumb');
  const toc = document.getElementById('toc');
  markActive();

  if (!hash) {
    crumb.textContent = '';
    toc.innerHTML = '';
    doc.innerHTML = `<h1>alphaS study logbooks</h1>
      <p>Pick a study on the left. A study's logbook is the orchestrator's record; the
      entries under it are the individual worker tasks, each with its own logbook and its
      own plot gallery.</p>
      <p>Nothing here is a build artifact — the pages read the markdown in
      <code>WRemnantsHelpers/studies/</code> live, so an edit shows up on reload and a new
      task appears as soon as it is created.</p>
      <p class="empty">${TREE.length} stud${TREE.length === 1 ? 'y' : 'ies'} published ·
      ${TREE.reduce((n, s) => n + s.tasks.length, 0)} tasks</p>`;
    return;
  }

  const parts = hash.split('/').filter(Boolean);
  const dir = parts.slice(0, 2).join('/');
  const url = dir + '/LOGBOOK.md';
  document.getElementById('raw').href = url;
  document.getElementById('plots').href = dir + '/';
  crumb.innerHTML = parts.length > 1
    ? `<a href="#${parts[0]}">${esc(parts[0])}</a> / ${esc(parts[1])}`
    : esc(parts[0]);

  doc.innerHTML = '<p class="empty">loading…</p>';
  let md;
  try {
    const r = await fetch(url + '?t=' + Date.now(), {cache: 'no-store'});
    if (!r.ok) throw new Error(r.status + ' ' + r.statusText);
    md = await r.text();
  } catch (e) {
    doc.innerHTML = `<h1>not found</h1><p><code>${esc(url)}</code> could not be read
      (${esc(e.message)}).</p><p>If the study was just created, publish it with
      <code>scripts/webpublish_study.sh ${esc(parts[0])}</code>.</p>`;
    toc.innerHTML = '';
    return;
  }

  const store = [];
  let html = marked.parse(protectMath(md.replace(/^---\n[\s\S]*?\n---\n/, ''), store));
  html = restoreMath(html, store);
  doc.innerHTML = html;

  // relative links/images are relative to the logbook, not to this page
  doc.querySelectorAll('img[src], a[href]').forEach(el => {
    const attr = el.tagName === 'IMG' ? 'src' : 'href';
    const v = el.getAttribute(attr);
    if (!v || /^([a-z]+:|\/\/|\/|#|mailto:)/i.test(v)) return;
    el.setAttribute(attr, dir + '/' + v);
    if (attr === 'href') el.setAttribute('target', '_blank');
  });

  // table of contents — these logbooks get long
  const hs = [...doc.querySelectorAll('h2, h3')];
  toc.innerHTML = hs.length < 3 ? '' : hs.map((h, i) => {
    h.id = 'h' + i;
    return `<a class="${h.tagName.toLowerCase()}" href="#${hash}" data-j="h${i}">${esc(h.textContent)}</a>`;
  }).join('');
  toc.querySelectorAll('[data-j]').forEach(a => a.onclick = e => {
    e.preventDefault();
    document.getElementById(a.dataset.j).scrollIntoView({behavior: 'smooth', block: 'start'});
  });
  document.getElementById('main').scrollTop = 0;
}

addEventListener('hashchange', load);
renderTree('');
load();
</script>
</body>
</html>
