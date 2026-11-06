// Single app state. The session (store + sector + draft + default entry mode) is the only
// data that matters; everything else is derived from the engine's context() call.
import { engine, engineReady } from "./engine.js";
import { downloadText } from "./files.js";

export const app = $state({
  ready: false,
  failed: null,
  meta: null,
  session: null, // { store, sector, draft, default_mode }
  ctx: null, // engine context(): steps, label, element form specs
  step: 0,
  maxStep: 0,
  stepErrors: {}, // { [stepKey]: string[] }
  dirty: false, // unsaved changes since last save/open
  notice: null, // { tone, title, lines }
  view: "app", // app | howto | privacy
});

let ctxSeq = 0;

export async function start() {
  try {
    await engineReady;
    app.meta = await engine("meta");
    app.session = {
      store: $state.snapshot(app.meta.fresh_store),
      sector: "generic",
      draft: false,
      default_mode: "rand",
    };
    await refresh();
    app.ready = true;
  } catch (err) {
    app.failed = err?.message || String(err);
  }
}

/** Re-derive steps and form specs from the engine. Later calls win over slower earlier ones. */
export async function refresh() {
  if (!app.session) return;
  const seq = ++ctxSeq;
  const ctx = await engine("context", app.session);
  if (seq !== ctxSeq) return;
  app.ctx = ctx;
  const last = ctx.steps.length - 1;
  if (app.step > last) app.step = last;
  if (app.maxStep > last) app.maxStep = last;
}

export function touch() {
  app.dirty = true;
}

export const steps = () => app.ctx?.steps ?? [{ key: "profile", name: "Profile" }];
export const currentStep = () => steps()[app.step] ?? steps()[0];
export const consented = () => Boolean(app.session?.store?.consent);

export function goTo(n) {
  if (!consented()) {
    app.step = 0;
    return;
  }
  app.step = Math.max(0, Math.min(n, steps().length - 1));
  app.maxStep = Math.max(app.maxStep, app.step);
  window.scrollTo({ top: 0 });
}

/** Validate the current step with the engine, then advance (app.py footer()). */
export async function continueStep() {
  const step = currentStep();
  const probs = await engine("problems", app.session, step.key);
  if (probs.length) {
    app.stepErrors = { ...app.stepErrors, [step.key]: probs };
    return false;
  }
  const { [step.key]: _drop, ...rest } = app.stepErrors;
  app.stepErrors = rest;
  goTo(app.step + 1);
  return true;
}

export function back() {
  goTo(app.step - 1);
}

export async function startOver() {
  app.session = {
    ...app.session,
    store: $state.snapshot(app.meta.fresh_store),
  };
  app.step = 0;
  app.maxStep = 0;
  app.stepErrors = {};
  app.dirty = false;
  app.notice = null;
  await refresh();
}

export async function saveClientFile() {
  const { text, filename } = await engine("client_save", app.session);
  downloadText(text, filename, "application/json");
  app.dirty = false;
}

/** Open a client file. Consent is never read from the file; the current one is kept. */
export async function openClientFile(text) {
  const out = await engine("client_open", text);
  if (!out.ok) {
    app.notice = { tone: "danger", title: "Could not open that file", lines: out.problems };
    return false;
  }
  const keepConsent = consented();
  const store = out.store;
  store.consent = keepConsent;
  const sectors = new Set(app.meta.sectors.map((s) => s.key));
  app.session = {
    ...app.session,
    store,
    sector: sectors.has(out.app?.sector) ? out.app.sector : app.session.sector,
    draft: Boolean(out.app?.draft),
  };
  app.step = 0;
  app.maxStep = keepConsent ? 99 : 0;
  app.stepErrors = {};
  app.dirty = false;
  const name = store.profile.company || "the client file";
  const when = out.app?.saved_at ? ` (saved ${out.app.saved_at.slice(0, 10)})` : "";
  app.notice = {
    tone: "success",
    title: `Opened ${name}${when}`,
    lines: [
      ...out.notes,
      ...(keepConsent ? [] : ["Agree to the privacy notice on Profile to continue."]),
    ],
  };
  await refresh();
  return true;
}
