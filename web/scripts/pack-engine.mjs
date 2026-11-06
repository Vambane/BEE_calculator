// Prepares the browser engine before `vite dev` / `vite build`:
//  1. packs the Python engine (bee/, bee_ui/core + client_file, bee_web/) into public/engine.zip
//  2. copies the Pyodide runtime files into public/pyodide/ so they are served same-origin
//  3. copies the in-app docs (how-to, privacy) into public/docs/
//  4. writes public/engine.json with a content hash used to cache-bust engine.zip
import { createHash } from "node:crypto";
import { copyFileSync, mkdirSync, readdirSync, readFileSync, statSync, writeFileSync } from "node:fs";
import { join, relative } from "node:path";
import { zipSync } from "fflate";

const web = new URL("..", import.meta.url).pathname;
const repo = join(web, "..");
const pub = join(web, "public");
mkdirSync(join(pub, "pyodide"), { recursive: true });
mkdirSync(join(pub, "docs"), { recursive: true });

const include = ["bee", "bee_ui/__init__.py", "bee_ui/core.py", "bee_ui/client_file.py", "bee_web"];
const files = {};
function add(path) {
  if (statSync(path).isDirectory()) {
    for (const name of readdirSync(path).sort()) if (name !== "__pycache__") add(join(path, name));
    return;
  }
  if (/\.(py|csv)$/.test(path)) files[relative(repo, path)] = readFileSync(path);
}
for (const p of include) add(join(repo, p));
// Fixed timestamps keep the zip byte-identical for identical sources (stable hash).
const zip = zipSync(
  Object.fromEntries(Object.entries(files).map(([k, v]) => [k, [v, { mtime: new Date("2020-01-01") }]])),
  { level: 9 },
);
writeFileSync(join(pub, "engine.zip"), zip);

const runtime = ["pyodide.mjs", "pyodide.asm.mjs", "pyodide.asm.wasm", "python_stdlib.zip", "pyodide-lock.json"];
const pyodideDir = join(web, "node_modules", "pyodide");
for (const f of runtime) copyFileSync(join(pyodideDir, f), join(pub, "pyodide", f));
const pyodideVersion = JSON.parse(readFileSync(join(pyodideDir, "package.json"), "utf8")).version;

for (const doc of ["HOW_TO.md", "PRIVACY_WEB.md"]) copyFileSync(join(repo, "docs", doc), join(pub, "docs", doc));

const hash = createHash("sha256").update(zip).digest("hex").slice(0, 12);
writeFileSync(join(pub, "engine.json"), JSON.stringify({ hash, pyodide: pyodideVersion }) + "\n");
console.log(`engine.zip: ${Object.keys(files).length} files, hash ${hash}; pyodide ${pyodideVersion}`);
