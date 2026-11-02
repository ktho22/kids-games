// Cloud save backend for 영서 히어로 대작전 (hero-squad).
//
// Same "friendly, not fortified" model as cloud.mjs: a save is keyed by a
// short code, the device that created it holds a secret ownerToken, and a
// second device takes over with code + 4-digit PIN (`claim`). Wrong PINs
// are counted and lock claiming for a while.
//
// Unlike Pocket Mini Adventure there are no conflicts to ask about:
// everything in this game only grows (cards, Pokémon, stars, episodes),
// so every push is merged with what is stored and the merged state is
// sent back. Two devices playing offline both keep what they earned.
import { getStore } from '@netlify/blobs';
import crypto from 'node:crypto';

const WORDS = ['HERO','STAR','MOON','SPARK','FLAME','STORM','CLOUD','COMET','NOVA','EMBER',
  'IRON','GOLD','RUBY','JADE','PEARL','FOX','WOLF','BEAR','HAWK','LYNX','OTTER','TIGER',
  'LION','EAGLE','SHARK','ZAP','BOLT','ROCK','WAVE','LEAF'];
const PIN_MAX_FAILS = 8;
const PIN_LOCK_MS = 10 * 60 * 1000;

// The game is also served from GitHub Pages, which calls this cross-origin.
// Auth is the owner token in the body (no cookies), so any origin is fine.
const CORS = {
  'access-control-allow-origin': '*',
  'access-control-allow-methods': 'POST, OPTIONS',
  'access-control-allow-headers': 'content-type',
  'access-control-max-age': '86400',
};
function json(status, body) {
  return { status, headers: { 'content-type': 'application/json', ...CORS }, body: JSON.stringify(body) };
}
const randToken = () => crypto.randomBytes(18).toString('hex');
const randCode = () => WORDS[Math.floor(Math.random() * WORDS.length)] + (100 + Math.floor(Math.random() * 900));
const randPin = () => String(crypto.randomInt(0, 10000)).padStart(4, '0');
const pinHash = (code, pin) => crypto.createHash('sha256').update(code + ':' + pin).digest('hex');
const clean = (s, max) => (typeof s === 'string' ? s : '').trim().slice(0, max || 24);

async function uniqueCode(store) {
  for (let i = 0; i < 25; i++) {
    const c = randCode();
    if (!(await store.get(c))) return c;
  }
  throw new Error('could not allocate a code');
}

const num = (v, lo, hi, d) => (Number.isFinite(+v) ? Math.min(hi, Math.max(lo, Math.round(+v))) : d);
const list = (v, max) => (Array.isArray(v) ? v.filter(x => typeof x === 'string' || Number.isFinite(x)).slice(0, max) : []);
// Keeps only fields the game uses, with sane bounds.
function sanitize(s) {
  s = s && typeof s === 'object' ? s : {};
  return {
    episode: num(s.episode, 1, 9999, 1),
    level: num(s.level, 1, 6, 1),
    streak: num(s.streak, 0, 99, 0),
    recent: list(s.recent, 6).map(x => (x ? 1 : 0)),
    heroes: list(s.heroes, 100),
    pokes: list(s.pokes, 200),
    villains: list(s.villains, 100),
    stars: num(s.stars, 0, 1e6, 0),
    savedAt: num(s.savedAt, 0, 1e15, 0),
  };
}
// Collections are unions (stored order first, so "newest hero" stays last),
// counters take the larger value, and the difficulty state comes from
// whichever device changed it most recently.
export function mergeState(stored, incoming) {
  const a = sanitize(stored), b = sanitize(incoming);
  const union = (x, y) => [...x, ...y.filter(v => !x.includes(v))];
  const newer = b.savedAt >= a.savedAt ? b : a;
  return {
    episode: Math.max(a.episode, b.episode),
    stars: Math.max(a.stars, b.stars),
    heroes: union(a.heroes, b.heroes),
    pokes: union(a.pokes, b.pokes),
    villains: union(a.villains, b.villains),
    level: newer.level,
    streak: newer.streak,
    recent: newer.recent,
    savedAt: Math.max(a.savedAt, b.savedAt),
  };
}

export async function handleRequest(method, bodyText, store) {
  if (method === 'OPTIONS') return { status: 204, headers: CORS, body: '' };
  if (method !== 'POST') return json(405, { error: 'POST only' });
  let body;
  try { body = JSON.parse(bodyText || '{}'); } catch (e) { return json(400, { error: 'bad json' }); }

  async function loadOwned() {
    const rec = await store.get(clean(body.code, 12).toUpperCase(), { type: 'json' });
    if (!rec) return { error: json(404, { error: 'no save with that code' }) };
    if (rec.ownerToken !== body.ownerToken) return { error: json(403, { error: 'wrong owner token' }) };
    return { rec };
  }

  try {
    if (body.action === 'create') {
      const code = await uniqueCode(store);
      const ownerToken = randToken();
      const pin = randPin();
      const rec = { code, ownerToken, pinHash: pinHash(code, pin), pinFails: 0, pinLockUntil: 0, state: sanitize(body.state), updatedAt: Date.now() };
      await store.setJSON(code, rec);
      return json(200, { code, ownerToken, pin, state: rec.state });
    }

    // Another device takes over the same save: code + PIN → owner token + state.
    if (body.action === 'claim') {
      const code = clean(body.code, 12).toUpperCase();
      const rec = await store.get(code, { type: 'json' });
      if (!rec) return json(404, { error: 'no save with that code' });
      if ((rec.pinLockUntil || 0) > Date.now()) return json(429, { error: 'too many wrong PINs' });
      if (pinHash(code, clean(body.pin, 8)) !== rec.pinHash) {
        rec.pinFails = (rec.pinFails || 0) + 1;
        if (rec.pinFails >= PIN_MAX_FAILS) { rec.pinFails = 0; rec.pinLockUntil = Date.now() + PIN_LOCK_MS; }
        await store.setJSON(code, rec);
        return json(403, { error: 'wrong PIN' });
      }
      if (rec.pinFails) { rec.pinFails = 0; await store.setJSON(code, rec); }
      return json(200, { code, ownerToken: rec.ownerToken, state: rec.state });
    }

    // Merge this device's progress in and hand back the combined save.
    if (body.action === 'sync') {
      const { error, rec } = await loadOwned();
      if (error) return error;
      const merged = mergeState(rec.state, body.state);
      if (JSON.stringify(merged) !== JSON.stringify(rec.state)) {
        rec.state = merged;
        rec.updatedAt = Date.now();
        await store.setJSON(rec.code, rec);
      }
      return json(200, { state: merged });
    }

    return json(400, { error: 'unknown action' });
  } catch (e) {
    return json(500, { error: 'server hiccup, try again in a moment' });
  }
}

// Functions v2 wires up Blobs credentials automatically. 'strong' so a save
// written by one device reads back immediately on the next.
export default async (req) => {
  const store = getStore({ name: 'hero-squad-saves', consistency: 'strong' });
  const r = await handleRequest(req.method, req.method === 'POST' ? await req.text() : '', store);
  return new Response(r.status === 204 ? null : r.body, { status: r.status, headers: r.headers });
};
