// Runs the Python scoring engine (bee_web.api) inside Pyodide, off the main thread.
// Messages in:  { id, name, args }   Messages out: { id, result } | { id, error }
// A first message { type: "ready" } (or { type: "failed", message }) reports start-up.

let call = null;

async function boot() {
  const { hash } = await (await fetch("/engine.json", { cache: "no-cache" })).json();
  const { loadPyodide } = await import(/* @vite-ignore */ `${self.location.origin}/pyodide/pyodide.mjs`);
  const [pyodide, engineZip] = await Promise.all([
    loadPyodide({ indexURL: `${self.location.origin}/pyodide/`, fullStdLib: false }),
    fetch(`/engine.zip?v=${hash}`).then((r) => {
      if (!r.ok) throw new Error(`engine.zip ${r.status}`);
      return r.arrayBuffer();
    }),
  ]);
  pyodide.unpackArchive(engineZip, "zip", { extractDir: "/engine" });
  pyodide.runPython("import sys; sys.path.insert(0, '/engine'); from bee_web import api");
  const apiCall = pyodide.globals.get("api").call;
  call = (name, args) => JSON.parse(apiCall(name, JSON.stringify(args ?? [])));
}

const ready = boot().then(
  () => self.postMessage({ type: "ready" }),
  (err) => self.postMessage({ type: "failed", message: String(err?.message || err) }),
);

self.onmessage = async ({ data }) => {
  await ready;
  if (!call) {
    self.postMessage({ id: data.id, error: "Engine not available" });
    return;
  }
  try {
    const result = call(data.name, data.args);
    if (result && typeof result === "object" && "error" in result && !Array.isArray(result)) {
      self.postMessage({ id: data.id, error: result.error, detail: result.detail });
    } else {
      self.postMessage({ id: data.id, result });
    }
  } catch (err) {
    self.postMessage({ id: data.id, error: String(err?.message || err) });
  }
};
