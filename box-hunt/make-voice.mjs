// Records every spoken line of the game into voice/<key>.m4a with macOS `say`.
// iOS mutes speechSynthesis in silent mode but still plays audio files, so the game
// plays these and only falls back to speechSynthesis when a file is missing.
import { readFileSync, existsSync, mkdirSync, readdirSync, unlinkSync } from 'node:fs';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import vm from 'node:vm';

const run = promisify(execFile);
const here = new URL('.', import.meta.url).pathname;
const outDir = join(here, 'voice');
const VOICE = 'Yuna';
const RATE = '165';

const html = readFileSync(join(here, 'index.html'), 'utf8');
const block = html.split('// VOICE-DATA-START')[1].split('// VOICE-DATA-END')[0];
const ctx = vm.createContext({});
vm.runInContext(`${block}\nthis.out = allPhrases().map(t => [voiceKey(t), t]);`, ctx);
const lines = ctx.out;

mkdirSync(outDir, { recursive: true });
const wanted = new Set(lines.map(([key]) => `${key}.m4a`));
for (const f of readdirSync(outDir)) if (!wanted.has(f)) unlinkSync(join(outDir, f));

const todo = lines.filter(([key]) => !existsSync(join(outDir, `${key}.m4a`)));
let next = 0, made = 0;
async function worker() {
  while (next < todo.length) {
    const [key, text] = todo[next++];
    const aiff = join(tmpdir(), `boxhunt-${key}.aiff`);
    await run('say', ['-v', VOICE, '-r', RATE, '-o', aiff, text.replace(/"/g, '')]);
    await run('afconvert', ['-f', 'm4af', '-d', 'aac', '-b', '32000', aiff, join(outDir, `${key}.m4a`)]);
    unlinkSync(aiff);
    made++;
  }
}
await Promise.all(Array.from({ length: 6 }, worker));
console.log(`${lines.length} lines, ${made} newly recorded → ${outDir}`);
