// Promise API over the engine worker. Every call returns plain JSON from bee_web.api.

const worker = new Worker(new URL("./engine.worker.js", import.meta.url), { type: "module" });
const pending = new Map();
let nextId = 1;

let resolveReady;
let rejectReady;
/** Resolves once Pyodide and the engine are loaded; rejects if start-up fails. */
export const engineReady = new Promise((res, rej) => {
  resolveReady = res;
  rejectReady = rej;
});

worker.onmessage = ({ data }) => {
  if (data.type === "ready") return resolveReady();
  if (data.type === "failed") return rejectReady(new Error(data.message));
  const p = pending.get(data.id);
  if (!p) return;
  pending.delete(data.id);
  if (data.error) p.reject(Object.assign(new Error(data.error), { detail: data.detail }));
  else p.resolve(data.result);
};
worker.onerror = (e) => rejectReady(new Error(e.message || "Engine failed to start"));

/**
 * Call a bee_web.api function.
 * @param {string} name
 * @param {...any} args
 */
export function engine(name, ...args) {
  const id = nextId++;
  return new Promise((resolve, reject) => {
    pending.set(id, { resolve, reject });
    // Svelte state proxies are not cloneable; send a plain snapshot.
    worker.postMessage({ id, name, args: JSON.parse(JSON.stringify(args)) });
  });
}
