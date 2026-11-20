// Submission harness for the gta6-trophy-guide-01 entry.
//
// The entry is app/: plain static files with no build step, opened at
// app/index.html, that read app/data/trophies.json from their own folder and
// load nothing over the network. This program only packages it:
//
//   out/app/          a copy of app/
//   out/screenshots/  a copy of screenshots/
//   out/dossier.json  the summary the judge reads, written by the vendored
//                     make.fun library from what actually landed in out/
//
// Leave vendor/makefun-frontend.ts untouched: the scorer compares
// dossier.json byte for byte against what its own copy of that library
// produces, so changing how the dossier is built changes nothing for the
// better and risks a mismatch.
//
// Inside the grader's container the output is /output. Elsewhere:
//
//   mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts
//
// Serve the app for a local look with `node serve.ts`.

import { cpSync, existsSync, mkdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

import { buildDossier } from './vendor/makefun-frontend.ts';

const here = fileURLToPath(new URL('.', import.meta.url));
const out = process.env.MAKEFUN_OUTPUT_DIR ?? '/output';

// Caps mirror reference/gate.json. text_max_bytes shapes the dossier's own
// size; the rest reject an entry the scorer would reject: more than four
// screenshots or any over 256 KiB, and an app/ larger than 993 entries or
// 48 MiB, which sits beside /output's own 1000-entry ceiling.
const CAPS = {
  text_max_bytes: 163_840,
  screenshots: { max: 4, max_bytes: 262_144 },
  app_max_files: 993,
  app_max_bytes: 50_331_648,
} as const;

mkdirSync(out, { recursive: true });
cpSync(join(here, 'app'), join(out, 'app'), { recursive: true });
mkdirSync(join(out, 'screenshots'), { recursive: true });
if (existsSync(join(here, 'screenshots'))) {
  cpSync(join(here, 'screenshots'), join(out, 'screenshots'), { recursive: true });
}

const dossier = buildDossier(out, CAPS);
writeFileSync(join(out, 'dossier.json'), dossier);

console.log(`packaged ${out}`);
console.log(`  dossier.json  ${Buffer.byteLength(dossier)} bytes`);
