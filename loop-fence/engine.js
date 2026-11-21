// 울타리 치기 퍼즐 엔진: 문제 생성 + 해가 하나뿐인지 검사하는 풀이기.
// 브라우저에서는 window.FenceEngine, node 에서는 require() 로 쓴다.
(function (root) {
  'use strict';

  // ---------- 난수 (시드 고정 가능) ----------
  function mulberry32(seed) {
    let a = seed >>> 0;
    return function () {
      a = (a + 0x6D2B79F5) >>> 0;
      let t = a;
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  // ---------- 격자 ----------
  // 점: (R+1)×(C+1), 가로 변: (R+1)×C, 세로 변: R×(C+1)
  function makeGeom(R, C) {
    const V = (R + 1) * (C + 1), H = (R + 1) * C, E = H + R * (C + 1);
    const vid = (r, c) => r * (C + 1) + c;
    const hid = (r, c) => r * C + c;
    const vvid = (r, c) => H + r * (C + 1) + c;
    const eA = new Int16Array(E), eB = new Int16Array(E);
    const vertEdges = Array.from({ length: V }, () => []);
    const edgeCells = Array.from({ length: E }, () => []);
    for (let r = 0; r <= R; r++) for (let c = 0; c < C; c++) {
      const e = hid(r, c); eA[e] = vid(r, c); eB[e] = vid(r, c + 1);
    }
    for (let r = 0; r < R; r++) for (let c = 0; c <= C; c++) {
      const e = vvid(r, c); eA[e] = vid(r, c); eB[e] = vid(r + 1, c);
    }
    for (let e = 0; e < E; e++) { vertEdges[eA[e]].push(e); vertEdges[eB[e]].push(e); }
    const cellEdges = [];
    for (let r = 0; r < R; r++) for (let c = 0; c < C; c++) {
      const i = r * C + c;
      const es = [hid(r, c), hid(r + 1, c), vvid(r, c), vvid(r, c + 1)];
      cellEdges.push(es);
      for (const e of es) edgeCells[e].push(i);
    }
    return { R, C, V, H, E, eA, eB, vertEdges, cellEdges, edgeCells, hid, vvid, vid };
  }

  // ---------- 풀이기 ----------
  // st: 0 미정, 1 선, 2 선 없음
  // opts.guess=false 이면 추론만으로 풀리는지 본다 (막히면 stuck).
  function solve(g, clues, opts) {
    opts = opts || {};
    const limit = opts.limit || 2;
    const maxNodes = opts.maxNodes || 20000;
    const guess = opts.guess !== false;
    const { E, V, cellEdges, vertEdges, eA, eB } = g;
    const N = cellEdges.length;
    let nodes = 0, count = 0, aborted = false, stuck = false, first = null;
    const parent = new Int16Array(V);
    const deg = new Int8Array(V);
    const compEdges = new Int16Array(V);
    const compVerts = new Int16Array(V);

    function find(x) {
      while (parent[x] !== x) { parent[x] = parent[parent[x]]; x = parent[x]; }
      return x;
    }

    function cluesOkIfRestOff(st, extra) {
      for (let i = 0; i < N; i++) {
        const k = clues[i];
        if (k < 0) continue;
        let on = 0;
        for (const e of cellEdges[i]) if (st[e] === 1 || e === extra) on++;
        if (on !== k) return false;
      }
      return true;
    }

    // 작은 고리를 막는 규칙. false=모순, true=변화 있음, null=변화 없음
    function loopRule(st) {
      for (let v = 0; v < V; v++) { parent[v] = v; deg[v] = 0; compEdges[v] = 0; compVerts[v] = 0; }
      let totalOn = 0;
      for (let e = 0; e < E; e++) {
        if (st[e] !== 1) continue;
        totalOn++;
        deg[eA[e]]++; deg[eB[e]]++;
        const a = find(eA[e]), b = find(eB[e]);
        if (a !== b) parent[a] = b;
      }
      if (totalOn === 0) return null;
      for (let e = 0; e < E; e++) if (st[e] === 1) compEdges[find(eA[e])]++;
      for (let v = 0; v < V; v++) if (deg[v] > 0) compVerts[find(v)]++;
      // 닫힌 고리가 있는가
      for (let v = 0; v < V; v++) {
        if (deg[v] === 0 || parent[v] !== v) continue;
        if (compEdges[v] === compVerts[v]) {
          if (compEdges[v] !== totalOn) return false; // 고리가 둘 이상
          let ch = false;
          for (let e = 0; e < E; e++) if (st[e] === 0) { st[e] = 2; ch = true; }
          return ch ? true : null;
        }
      }
      let ch = false;
      for (let e = 0; e < E; e++) {
        if (st[e] !== 0) continue;
        const a = eA[e], b = eB[e];
        if (deg[a] !== 1 || deg[b] !== 1) continue;
        const ra = find(a);
        if (ra !== find(b)) continue;
        // 이 변을 그으면 고리가 닫힌다
        if (compEdges[ra] !== totalOn || !cluesOkIfRestOff(st, e)) { st[e] = 2; ch = true; }
      }
      return ch ? true : null;
    }

    function propagate(st) {
      for (;;) {
        let changed = false;
        for (let i = 0; i < N; i++) {
          const k = clues[i];
          if (k < 0) continue;
          let on = 0, un = 0;
          const es = cellEdges[i];
          for (let j = 0; j < 4; j++) { const s = st[es[j]]; if (s === 1) on++; else if (s === 0) un++; }
          if (on > k || on + un < k) return false;
          if (un > 0 && (on === k || on + un === k)) {
            const val = on === k ? 2 : 1;
            for (let j = 0; j < 4; j++) if (st[es[j]] === 0) st[es[j]] = val;
            changed = true;
          }
        }
        for (let v = 0; v < V; v++) {
          let on = 0, un = 0;
          const es = vertEdges[v];
          for (let j = 0; j < es.length; j++) { const s = st[es[j]]; if (s === 1) on++; else if (s === 0) un++; }
          if (on > 2) return false;
          if (on === 1 && un === 0) return false;
          if (un === 0) continue;
          if (on === 2 || (on === 0 && un === 1)) {
            for (let j = 0; j < es.length; j++) if (st[es[j]] === 0) st[es[j]] = 2;
            changed = true;
          } else if (on === 1 && un === 1) {
            for (let j = 0; j < es.length; j++) if (st[es[j]] === 0) st[es[j]] = 1;
            changed = true;
          }
        }
        if (!changed) {
          const r = loopRule(st);
          if (r === false) return false;
          if (r === null) return true;
        }
      }
    }

    function pickEdge(st) {
      let fallback = -1;
      for (let v = 0; v < V; v++) {
        let on = 0, un = -1;
        for (const e of vertEdges[v]) { if (st[e] === 1) on++; else if (st[e] === 0) un = e; }
        if (on === 1 && un >= 0) return un;
      }
      for (let e = 0; e < E; e++) if (st[e] === 0) { fallback = e; break; }
      return fallback;
    }

    function dfs(st) {
      if (aborted || count >= limit) return;
      if (++nodes > maxNodes) { aborted = true; return; }
      if (!propagate(st)) return;
      const e = pickEdge(st);
      if (e < 0) {
        let any = false;
        for (let i = 0; i < E; i++) if (st[i] === 1) { any = true; break; }
        if (!any) return;
        count++;
        if (!first) first = st.slice();
        return;
      }
      if (!guess) { stuck = true; return; }
      const a = st.slice(); a[e] = 1; dfs(a);
      if (aborted || count >= limit) return;
      const b = st; b[e] = 2; dfs(b);
    }

    dfs(new Int8Array(E));
    return { count, aborted, stuck, solution: first, nodes };
  }

  // ---------- 영역(울타리 안쪽) 만들기 ----------
  function genRegion(R, C, rng) {
    const N = R * C;
    const inR = new Uint8Array(N);
    const at = (r, c) => (r < 0 || c < 0 || r >= R || c >= C) ? 0 : inR[r * C + c];

    function pinchFree(r, c) {
      // 이 칸의 네 꼭짓점에서 대각선으로만 맞닿는 모양이 생기면 안 된다
      for (let dr = 0; dr <= 1; dr++) for (let dc = 0; dc <= 1; dc++) {
        const vr = r + dr, vc = c + dc;
        const a = at(vr - 1, vc - 1), b = at(vr - 1, vc), cc = at(vr, vc - 1), d = at(vr, vc);
        if (a === d && b === cc && a !== b) return false;
      }
      return true;
    }
    function outsideConnected() {
      const seen = new Uint8Array(N);
      const q = [];
      let outCount = 0;
      for (let i = 0; i < N; i++) if (!inR[i]) outCount++;
      for (let r = 0; r < R; r++) for (let c = 0; c < C; c++) {
        if (r !== 0 && c !== 0 && r !== R - 1 && c !== C - 1) continue;
        const i = r * C + c;
        if (!inR[i] && !seen[i]) { seen[i] = 1; q.push(i); }
      }
      let n = 0;
      while (q.length) {
        const i = q.pop(); n++;
        const r = (i / C) | 0, c = i % C;
        const nb = [[r - 1, c], [r + 1, c], [r, c - 1], [r, c + 1]];
        for (const [nr, nc] of nb) {
          if (nr < 0 || nc < 0 || nr >= R || nc >= C) continue;
          const j = nr * C + nc;
          if (!inR[j] && !seen[j]) { seen[j] = 1; q.push(j); }
        }
      }
      return n === outCount;
    }

    const target = Math.floor(N * (0.42 + rng() * 0.16));
    const sr = 1 + Math.floor(rng() * Math.max(1, R - 2));
    const sc = 1 + Math.floor(rng() * Math.max(1, C - 2));
    inR[sr * C + sc] = 1;
    let count = 1, tries = 0;
    const accept = [0, 1, 0.55, 0.22, 0.08];
    while (count < target && tries < N * 60) {
      tries++;
      const frontier = [];
      for (let i = 0; i < N; i++) {
        if (inR[i]) continue;
        const r = (i / C) | 0, c = i % C;
        const k = at(r - 1, c) + at(r + 1, c) + at(r, c - 1) + at(r, c + 1);
        if (k > 0) frontier.push([i, k]);
      }
      if (!frontier.length) break;
      const [i, k] = frontier[Math.floor(rng() * frontier.length)];
      if (rng() > accept[k]) continue;
      const r = (i / C) | 0, c = i % C;
      inR[i] = 1;
      if (pinchFree(r, c) && outsideConnected()) count++;
      else inR[i] = 0;
    }
    return inR;
  }

  // ---------- 문제 생성 ----------
  // level: { R, C, guess, maxNodes, keep, budgetMs }
  function generate(level, seed) {
    const rng = mulberry32(seed == null ? (Math.random() * 2 ** 32) >>> 0 : seed);
    const g = makeGeom(level.R, level.C);
    const N = level.R * level.C;
    const now = () => (typeof performance !== 'undefined' ? performance.now() : Date.now());
    const t0 = now();
    let sol, clues;
    for (let attempt = 0; attempt < 20; attempt++) {
      const region = genRegion(level.R, level.C, rng);
      sol = new Uint8Array(g.E);
      for (let e = 0; e < g.E; e++) {
        const cs = g.edgeCells[e];
        const a = region[cs[0]], b = cs.length > 1 ? region[cs[1]] : 0;
        if (a !== b) sol[e] = 1;
      }
      clues = new Int8Array(N);
      for (let i = 0; i < N; i++) {
        let k = 0;
        for (const e of g.cellEdges[i]) k += sol[e];
        clues[i] = k;
      }
      if (level.guess) break;
      // 추론만으로 풀어야 하는 난이도: 숫자가 다 있어도 막히는 모양이면 다시 만든다
      const full = solve(g, clues, { guess: false, limit: 2 });
      if (!full.stuck && full.count === 1) break;
    }
    const order = Array.from({ length: N }, (_, i) => i);
    for (let i = N - 1; i > 0; i--) { const j = Math.floor(rng() * (i + 1)); [order[i], order[j]] = [order[j], order[i]]; }
    const minKeep = Math.ceil(N * (level.keep || 0));
    let kept = N;
    for (const i of order) {
      if (kept <= minKeep) break;
      if (now() - t0 > (level.budgetMs || 2500)) break;
      const old = clues[i];
      clues[i] = -1;
      const res = solve(g, clues, { guess: level.guess, maxNodes: level.maxNodes || 2000, limit: 2 });
      const ok = level.guess ? (res.count === 1 && !res.aborted) : (!res.stuck && res.count === 1);
      if (ok) kept--; else clues[i] = old;
    }
    return { R: level.R, C: level.C, clues: Array.from(clues), solution: Array.from(sol) };
  }

  // ---------- 플레이어 답 검사 ----------
  // 반환: { done, cellStatus: Int8Array(-1 넘침, 0 미완, 1 맞음), badVerts: [] }
  function check(g, clues, st) {
    const N = clues.length;
    const cellStatus = new Int8Array(N);
    let allClues = true;
    for (let i = 0; i < N; i++) {
      let on = 0;
      for (const e of g.cellEdges[i]) if (st[e] === 1) on++;
      if (clues[i] < 0) continue;
      cellStatus[i] = on > clues[i] ? -1 : on === clues[i] ? 1 : 0;
      if (on !== clues[i]) allClues = false;
    }
    const badVerts = [];
    let degOk = true, total = 0;
    for (let v = 0; v < g.V; v++) {
      let on = 0;
      for (const e of g.vertEdges[v]) if (st[e] === 1) on++;
      if (on > 2) badVerts.push(v);
      if (on !== 0 && on !== 2) degOk = false;
    }
    for (let e = 0; e < g.E; e++) if (st[e] === 1) total++;
    let single = false;
    if (degOk && total > 0) {
      // 선 하나를 따라 한 바퀴 돌아 전체 선 개수와 같은지 본다
      let start = -1;
      for (let e = 0; e < g.E; e++) if (st[e] === 1) { start = e; break; }
      let prevV = g.eA[start], cur = g.eB[start], prevE = start, steps = 1;
      while (cur !== prevV || steps === 1) {
        let next = -1;
        for (const e of g.vertEdges[cur]) if (st[e] === 1 && e !== prevE) { next = e; break; }
        if (next < 0) break;
        const nv = g.eA[next] === cur ? g.eB[next] : g.eA[next];
        prevE = next; cur = nv; steps++;
        if (cur === g.eA[start]) break;
        if (steps > g.E) break;
      }
      single = cur === g.eA[start] && steps === total;
    }
    return { done: allClues && degOk && single, cellStatus, badVerts };
  }

  const api = { mulberry32, makeGeom, solve, generate, check, genRegion };
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.FenceEngine = api;
})(typeof window !== 'undefined' ? window : this);
