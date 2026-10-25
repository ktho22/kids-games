// Cloud save backend for Pocket Mini Adventure.
//
// Everything lives in one Netlify Blobs store, keyed by a short human
// code (e.g. "PINE482"). There are no user accounts: whoever created a
// save holds a secret `ownerToken` that proves they can write to it —
// anyone who just has the *code* can read a public snapshot of the team
// and drop a trade offer or a battle result into that save's inbox, but
// cannot overwrite it, cancel its trade post, or read anything private.
//
// To continue the SAME save on another device, the owner also gets a
// 4-digit PIN: code + PIN hands that device the owner token (`claim`).
// Wrong PINs are counted and lock the save's claim for a while, so the
// 10,000 combinations can't just be tried one after another.
//
// Pushes carry the revision (`baseRev`) the device last synced from. If
// another device has pushed since, the push is refused with the newer
// state instead of silently overwriting it — the game then asks the
// player which version to keep.
//
// This is a kids' game played within a household/friend group, not a
// public service — the model is "friendly, not fortified": enough to
// stop accidents and stray typos, not a real security boundary.
const { getStore } = require('@netlify/blobs');

const WORDS = ['PINE','LEAF','ROCK','WAVE','STAR','MOON','GLOW','SPARK','FLAME','FROST',
  'STORM','CLOUD','RAIN','SNOW','WIND','PEAK','CAVE','REEF','DUNE','MIST','DAWN','DUSK',
  'NOVA','COMET','EMBER','CORAL','MAPLE','BIRCH','CEDAR','FERN','MOSS','CLAY','IRON',
  'GOLD','RUBY','JADE','OPAL','PEARL','AMBER','FOX','WOLF','BEAR','DUCK','FROG','VINE',
  'HAWK','LYNX','OTTER','CRAB'];
const MAX_INBOX = 20;
const MAX_OFFERS = 10;
const PIN_MAX_FAILS = 8;
const PIN_LOCK_MS = 10 * 60 * 1000;

// The game is also served from GitHub Pages, which calls this function
// cross-origin. No cookies are involved (auth is the owner token in the
// body), so allowing any origin exposes nothing extra.
const CORS = {
  'access-control-allow-origin': '*',
  'access-control-allow-methods': 'POST, OPTIONS',
  'access-control-allow-headers': 'content-type',
  'access-control-max-age': '86400',
};
function json(status, body){
  return { statusCode: status, headers: { 'content-type': 'application/json', ...CORS }, body: JSON.stringify(body) };
}
function randToken(){ return require('crypto').randomBytes(18).toString('hex'); }
function randCode(){
  const w = WORDS[Math.floor(Math.random()*WORDS.length)];
  const n = 100 + Math.floor(Math.random()*900);
  return w + n;
}
function randPin(){ return String(require('crypto').randomInt(0, 10000)).padStart(4, '0'); }
function pinHash(code, pin){ return require('crypto').createHash('sha256').update(code + ':' + pin).digest('hex'); }
function clean(s, max){ return (typeof s === 'string' ? s : '').trim().slice(0, max || 24); }

async function uniqueCode(store){
  for(let i=0;i<25;i++){
    const c = randCode();
    if(!(await store.get(c))) return c;
  }
  throw new Error('could not allocate a code');
}
function pushInbox(rec, text){
  rec.inbox = rec.inbox || [];
  rec.inbox.push({ id: randToken().slice(0,10), text, ts: Date.now() });
  if(rec.inbox.length > MAX_INBOX) rec.inbox = rec.inbox.slice(-MAX_INBOX);
}
function publicView(rec){
  return {
    name: rec.name || rec.code,
    code: rec.code,
    updatedAt: rec.updatedAt,
    party: (rec.state.party || []).map(m => ({ uid:m.uid, id:m.id, lv:m.lv })),
    badges: (rec.state.badges || []).length,
    dexCount: (rec.state.dex || []).length,
    tradePost: rec.tradePost || null,
  };
}

exports.handler = async (event) => {
  if(event.httpMethod === 'OPTIONS') return { statusCode: 204, headers: CORS, body: '' };
  if(event.httpMethod !== 'POST') return json(405, { error: 'POST only' });
  let body;
  try{ body = JSON.parse(event.body || '{}'); }catch(e){ return json(400, { error: 'bad json' }); }
  const { action } = body;
  // This CLI-deployed function doesn't get the automatic Blobs context that
  // git-linked deploys get, so it's wired up by hand with a personal access
  // token (BLOBS_API_TOKEN, set via `netlify env:set` — never in source).
  const store = getStore({
    name: 'pocket-saves',
    siteID: process.env.SITE_ID,
    token: process.env.BLOBS_API_TOKEN,
  });

  async function loadOwned(code, ownerToken){
    const rec = await store.get(code, { type: 'json' });
    if(!rec) return { error: json(404, { error: 'no save with that code' }) };
    if(rec.ownerToken !== ownerToken) return { error: json(403, { error: 'wrong owner token' }) };
    return { rec };
  }

  try{
    if(action === 'publish'){
      const code = await uniqueCode(store);
      const ownerToken = randToken();
      const pin = randPin();
      const rec = {
        code, ownerToken, name: clean(body.name, 24) || code,
        pinHash: pinHash(code, pin), pinFails: 0, pinLockUntil: 0,
        state: body.state || {}, updatedAt: Date.now(),
        tradePost: null, tradeOffers: [], inbox: [],
      };
      await store.setJSON(code, rec);
      return json(200, { code, ownerToken, pin, updatedAt: rec.updatedAt });
    }

    /* another device takes over the same save: code + PIN -> owner token + full state */
    if(action === 'claim'){
      const code = clean(body.code, 12).toUpperCase();
      const rec = await store.get(code, { type: 'json' });
      if(!rec || !rec.pinHash) return json(404, { error: 'no save with that code' });
      if((rec.pinLockUntil || 0) > Date.now()) return json(429, { error: 'too many wrong PINs — wait 10 minutes and try again' });
      if(pinHash(code, clean(body.pin, 8)) !== rec.pinHash){
        rec.pinFails = (rec.pinFails || 0) + 1;
        if(rec.pinFails >= PIN_MAX_FAILS){ rec.pinFails = 0; rec.pinLockUntil = Date.now() + PIN_LOCK_MS; }
        await store.setJSON(code, rec);
        return json(403, { error: 'wrong PIN' });
      }
      if(rec.pinFails){ rec.pinFails = 0; await store.setJSON(code, rec); }
      return json(200, { code, ownerToken: rec.ownerToken, name: rec.name, state: rec.state, updatedAt: rec.updatedAt });
    }

    /* saves linked before PINs existed (or a forgotten PIN) get a fresh one */
    if(action === 'newPin'){
      const { error, rec } = await loadOwned(body.code, body.ownerToken);
      if(error) return error;
      const pin = randPin();
      rec.pinHash = pinHash(rec.code, pin); rec.pinFails = 0; rec.pinLockUntil = 0;
      await store.setJSON(rec.code, rec);
      return json(200, { pin });
    }

    if(action === 'rename'){
      const { error, rec } = await loadOwned(body.code, body.ownerToken);
      if(error) return error;
      rec.name = clean(body.name, 24) || rec.code;
      await store.setJSON(rec.code, rec);
      return json(200, { ok: true });
    }

    if(action === 'push'){
      const { error, rec } = await loadOwned(body.code, body.ownerToken);
      if(error) return error;
      const baseRev = Number(body.baseRev);
      if(Number.isFinite(baseRev) && baseRev > 0 && rec.updatedAt > baseRev){
        return json(409, { error: 'another device saved newer progress', conflict: true, state: rec.state, updatedAt: rec.updatedAt });
      }
      rec.state = body.state || rec.state;
      if(body.state && typeof body.state.name === 'string' && body.state.name.trim()) rec.name = clean(body.state.name, 24);
      rec.updatedAt = Date.now();
      await store.setJSON(rec.code, rec);
      return json(200, { ok: true, updatedAt: rec.updatedAt });
    }

    /* pulls newer state (if any) AND drains any waiting notifications in one round trip —
       this is what the Town screen quietly calls every so often */
    if(action === 'check'){
      const { error, rec } = await loadOwned(body.code, body.ownerToken);
      if(error) return error;
      const since = Number(body.since) || 0;
      const newer = rec.updatedAt > since;
      const inbox = rec.inbox || [];
      if(inbox.length){ rec.inbox = []; await store.setJSON(rec.code, rec); }
      return json(200, {
        newer, updatedAt: rec.updatedAt,
        state: newer ? rec.state : undefined,
        inbox, tradePost: rec.tradePost || null, tradeOffers: rec.tradeOffers || [],
      });
    }

    if(action === 'fetchPublic'){
      const rec = await store.get(clean(body.code, 12).toUpperCase(), { type: 'json' });
      if(!rec) return json(404, { error: 'no save with that code' });
      return json(200, publicView(rec));
    }

    if(action === 'tradePost'){
      const { error, rec } = await loadOwned(body.code, body.ownerToken);
      if(error) return error;
      const mon = (rec.state.party || []).find(m => m.uid === body.monUid);
      if(!mon) return json(400, { error: "that Pokémon isn't on your team right now" });
      rec.tradePost = { monUid: mon.uid, mon: { id: mon.id, lv: mon.lv }, want: clean(body.want, 24) || null, postedAt: Date.now() };
      rec.tradeOffers = [];
      await store.setJSON(rec.code, rec);
      return json(200, { ok: true, tradePost: rec.tradePost });
    }

    if(action === 'tradeCancel'){
      const { error, rec } = await loadOwned(body.code, body.ownerToken);
      if(error) return error;
      rec.tradePost = null; rec.tradeOffers = [];
      await store.setJSON(rec.code, rec);
      return json(200, { ok: true });
    }

    if(action === 'tradeOffer'){
      const targetCode = clean(body.targetCode, 12).toUpperCase();
      const target = await store.get(targetCode, { type: 'json' });
      if(!target) return json(404, { error: 'no save with that code' });
      if(!target.tradePost) return json(400, { error: "that trainer isn't offering a trade right now" });
      const { error, rec: from } = await loadOwned(body.fromCode, body.fromOwnerToken);
      if(error) return error;
      const mon = (from.state.party || []).find(m => m.uid === body.offerMonUid);
      if(!mon) return json(400, { error: "that Pokémon isn't on your team right now" });
      target.tradeOffers = target.tradeOffers || [];
      target.tradeOffers = target.tradeOffers.filter(o => o.fromCode !== from.code); // one live offer per friend
      target.tradeOffers.push({ offerId: randToken().slice(0,10), fromCode: from.code, fromName: from.name, mon: { uid: mon.uid, id: mon.id, lv: mon.lv } });
      if(target.tradeOffers.length > MAX_OFFERS) target.tradeOffers = target.tradeOffers.slice(-MAX_OFFERS);
      pushInbox(target, `🔁 ${from.name} offered a ${mon.id} for your trade post!`);
      await store.setJSON(target.code, target);
      return json(200, { ok: true });
    }

    if(action === 'tradeAccept'){
      const { error, rec: mine } = await loadOwned(body.code, body.ownerToken);
      if(error) return error;
      if(!mine.tradePost) return json(400, { error: 'you have no active trade post' });
      const offer = (mine.tradeOffers || []).find(o => o.offerId === body.offerId);
      if(!offer) return json(400, { error: 'that offer is gone' });
      const myMonIdx = (mine.state.party || []).findIndex(m => m.uid === mine.tradePost.monUid);
      if(myMonIdx < 0){
        mine.tradePost = null; mine.tradeOffers = [];
        await store.setJSON(mine.code, mine);
        return json(409, { error: "the Pokémon you posted isn't on your team anymore" });
      }
      const theirs = await store.get(offer.fromCode, { type: 'json' });
      const theirMonIdx = theirs ? (theirs.state.party || []).findIndex(m => m.uid === offer.mon.uid) : -1;
      if(!theirs || theirMonIdx < 0){
        mine.tradeOffers = mine.tradeOffers.filter(o => o.offerId !== body.offerId);
        await store.setJSON(mine.code, mine);
        return json(409, { error: 'that Pokémon left their team before you could accept — pick another offer' });
      }
      const myMon = mine.state.party[myMonIdx];
      const theirMon = theirs.state.party[theirMonIdx];
      mine.state.party[myMonIdx] = theirMon;
      theirs.state.party[theirMonIdx] = myMon;
      mine.tradePost = null; mine.tradeOffers = [];
      mine.updatedAt = Date.now(); theirs.updatedAt = Date.now();
      pushInbox(theirs, `✅ ${mine.name} traded you a ${myMon.id} for your ${theirMon.id}!`);
      await store.setJSON(mine.code, mine);
      await store.setJSON(theirs.code, theirs);
      return json(200, { ok: true, gotMon: theirMon });
    }

    if(action === 'battleResult'){
      const targetCode = clean(body.code, 12).toUpperCase();
      const target = await store.get(targetCode, { type: 'json' });
      if(!target) return json(404, { error: 'no save with that code' });
      const fromName = clean(body.fromName, 24) || 'Someone';
      pushInbox(target, body.won
        ? `⚔️ ${fromName} challenged your team and WON! Nothing was lost — go get 'em back!`
        : `⚔️ ${fromName} challenged your team but lost. Nice defending!`);
      await store.setJSON(target.code, target);
      return json(200, { ok: true });
    }

    return json(400, { error: 'unknown action' });
  }catch(e){
    return json(500, { error: 'server hiccup, try again in a moment' });
  }
};
