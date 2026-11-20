// Static file server for app/, standard library only, so the guide can be
// looked at without a build step: `node serve.ts` serves app/ on
// http://localhost:8080, `--port <n>` picks another port.
//
// It is a development convenience, not a web server: it resolves every path
// under app/ and refuses anything that escapes that folder, sends the MIME
// types a browser needs for modules and JSON, and deliberately sets no
// caching so edits show up on reload.

import { createReadStream, statSync } from 'node:fs';
import { createServer } from 'node:http';
import { extname, join, normalize, resolve, sep } from 'node:path';
import { fileURLToPath } from 'node:url';

type Response = { writeHead(status: number, headers?: Record<string, string | number>): Response; end(body?: string): void };

const ROOT = resolve(fileURLToPath(new URL('./app', import.meta.url)));
const DEFAULT_PORT = 8080;

const MIME: Readonly<Record<string, string>> = {
  '.html': 'text/html; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.webp': 'image/webp',
  '.avif': 'image/avif',
  '.ico': 'image/x-icon',
  '.woff2': 'font/woff2',
  '.webmanifest': 'application/manifest+json',
  '.txt': 'text/plain; charset=utf-8',
};

function portFromArgs(argv: readonly string[]): number {
  const at = argv.indexOf('--port');
  if (at === -1) return DEFAULT_PORT;
  const value = Number(argv[at + 1]);
  return Number.isInteger(value) && value > 0 && value < 65536 ? value : DEFAULT_PORT;
}

/** Resolve a request path to a file inside ROOT, or null if it escapes. */
function resolveWithinRoot(pathname: string): string | null {
  const target = resolve(join(ROOT, normalize(pathname)));
  if (target === ROOT) return null;
  return target.startsWith(ROOT + sep) ? target : null;
}

function fail(response: Response, status: number, message: string): void {
  response.writeHead(status, { 'content-type': 'text/plain; charset=utf-8' }).end(message);
}

const port = portFromArgs(process.argv.slice(2));

createServer((request, response) => {
  const url = new URL(request.url ?? '/', 'http://localhost');

  let pathname: string;
  try {
    pathname = decodeURIComponent(url.pathname);
  } catch {
    fail(response, 400, 'bad request');
    return;
  }

  if (pathname.endsWith('/')) pathname += 'index.html';
  const file = resolveWithinRoot(pathname);
  if (file === null) {
    fail(response, 403, 'forbidden');
    return;
  }

  let size: number;
  try {
    const stats = statSync(file);
    if (!stats.isFile()) throw new Error('not a file');
    size = stats.size;
  } catch {
    fail(response, 404, 'not found');
    return;
  }

  response.writeHead(200, {
    'content-type': MIME[extname(file).toLowerCase()] ?? 'application/octet-stream',
    'content-length': size,
    'cache-control': 'no-store',
  });
  createReadStream(file).pipe(response);
}).listen(port, '127.0.0.1', () => {
  console.log(`app/ is on http://localhost:${port}`);
});
