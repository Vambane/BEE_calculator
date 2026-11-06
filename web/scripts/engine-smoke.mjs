// Smoke test: load the packed engine in Node's Pyodide and run one scorecard end to end.
// Run after `npm run prepare-engine` (npm run test:engine does both).
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { loadPyodide } from "pyodide";

const zip = fileURLToPath(new URL("../public/engine.zip", import.meta.url));
const py = await loadPyodide();
py.unpackArchive(new Uint8Array(readFileSync(zip)), "zip", { extractDir: "/engine" });
py.runPython("import sys; sys.path.insert(0, '/engine'); from bee_web import api");

const call = (name, args) => {
  const out = JSON.parse(py.runPython(`api.call(${JSON.stringify(name)}, ${JSON.stringify(JSON.stringify(args))})`));
  if (out && out.error) throw new Error(`${name}: ${out.error} ${out.detail ?? ""}`);
  return out;
};
const check = (cond, msg) => {
  if (!cond) throw new Error(`engine smoke: ${msg}`);
};

const meta = call("meta", []);
const store = meta.fresh_store;
store.consent = true;
Object.assign(store.profile, { company: "Smoke Test (Pty) Ltd", revenue: 120e6, black_ownership: 40 });
Object.assign(store.fin, { npat: 8e6, leviable_amount: 30e6, tmps: 60e6, employees: 150 });
store.values.pct.ownership = { "100 2.2.1": 30, "100 2.3.1": 80 };
const session = { store, sector: "generic", draft: false, default_mode: "rand" };

const ctx = call("context", [session]);
check(ctx.steps.length === 7, `expected 7 steps, got ${ctx.steps.length}`);
const score = call("score", [session]);
check(typeof score.total === "number" && score.total > 0, "score total should be positive");
const report = call("report", [session]);
check(report.ok, "report should build");
const saved = call("client_save", [session]);
const reopened = call("client_open", [saved.text]);
check(reopened.ok && reopened.store.profile.company === store.profile.company, "client file should round-trip");

console.log(`engine smoke ok: Python ${py.version}, ${score.level_label}, ${score.total.toFixed(1)} pts`);
