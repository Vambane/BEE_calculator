<script>
  import { Check, Lock, BookOpen, ShieldCheck, RotateCcw } from "@lucide/svelte";
  import { app, steps, goTo, consented, startOver } from "../lib/state.svelte.js";
  import Switch from "../ui/Switch.svelte";

  let { onpicked } = $props();

  const list = $derived(app.ready ? steps() : []);

  function reachable(i) {
    return app.view === "app" && consented() && i <= app.maxStep;
  }
  function select(i) {
    if (app.view !== "app") location.hash = "#/";
    goTo(i);
    onpicked?.();
  }
  async function reset() {
    if (app.dirty && !confirm("Start over? This clears every figure for this client. Save the client file first if you need it.")) return;
    await startOver();
  }
</script>

<div class="rail-inner">
  {#if app.ready}
    <nav aria-label="Calculator steps">
      <p class="kicker" id="scorecard-steps">Scorecard</p>
      <ol aria-labelledby="scorecard-steps">
        {#each list as s, i (s.key)}
          {@const current = app.view === "app" && i === app.step}
          {@const done = consented() && i < app.maxStep && !current}
          {@const err = !!app.stepErrors[s.key]}
          <li>
            <button
              class="step"
              class:current
              class:done
              disabled={!reachable(i) && !current}
              aria-current={current ? "step" : undefined}
              onclick={() => select(i)}
            >
              <span class="dot" class:err aria-hidden="true">
                {#if done}<Check size={13} strokeWidth={3} />{:else if !reachable(i) && !current}<Lock size={11} strokeWidth={2.5} />{:else}{i + 1}{/if}
              </span>
              <span class="name">
                {s.name}
                {#if current}<span class="state">Current</span>{/if}
                {#if done}<span class="state">Done</span>{/if}
                {#if err}<span class="attn">Needs attention</span>{/if}
              </span>
            </button>
          </li>
        {/each}
      </ol>
    </nav>

    <div class="tools">
      <Switch
        id="draft-rules"
        bind:checked={app.session.draft}
        label={app.meta.draft_label}
        help="Draft Statement 400 / QSE CS600 of 2026 (GG 54032). Not in force."
      />
      <p class="ruleset">
        Amended Codes 2019, QSE CS600 (2015) and gazetted sector codes. A planning estimate, not a
        verification certificate.
      </p>
      <div class="links">
        <a href="#/howto"><BookOpen size={15} aria-hidden="true" />How to use</a>
        <a href="#/privacy"><ShieldCheck size={15} aria-hidden="true" />Privacy</a>
        <button class="link" onclick={reset}><RotateCcw size={15} aria-hidden="true" />Start over</button>
      </div>
    </div>
  {/if}
</div>

<style>
  .rail-inner {
    display: flex;
    flex-direction: column;
    gap: 1.5rem;
    min-height: 100%;
    padding: 1.25rem 0.9rem 1.25rem;
  }
  .kicker {
    margin: 0 0.55rem 0.4rem;
    font-size: 0.6875rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: var(--ink-3);
  }
  ol {
    list-style: none;
    margin: 0;
    padding: 0;
    display: grid;
    gap: 2px;
  }
  .step {
    width: 100%;
    display: flex;
    align-items: flex-start;
    gap: 0.7rem;
    padding: 0.45rem 0.55rem;
    border: 1px solid transparent;
    border-radius: var(--radius-sm);
    background: transparent;
    text-align: left;
    cursor: pointer;
    color: var(--ink-2);
    font-size: var(--t-sm);
    font-weight: 550;
    transition:
      background-color 150ms var(--ease),
      color 150ms var(--ease);
  }
  .step:hover:not(:disabled):not(.current) {
    background: rgb(9 9 11 / 0.05);
    color: var(--ink);
  }
  .step:focus-visible {
    outline: none;
    box-shadow: var(--focus);
  }
  .step:disabled {
    cursor: default;
  }
  .current {
    background: var(--surface);
    color: var(--ink);
    font-weight: 650;
    border-color: var(--line);
  }
  .dot {
    flex: none;
    display: grid;
    place-items: center;
    width: 24px;
    height: 24px;
    margin-top: 0.05rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 700;
    border: 1.5px solid var(--line-strong);
    background: var(--surface);
    color: var(--ink-2);
  }
  .current .dot {
    background: var(--primary);
    border-color: var(--primary);
    color: #fff;
  }
  .done .dot {
    background: var(--primary-tint);
    border-color: var(--accent);
    color: var(--accent);
  }
  .dot.err {
    border-color: var(--danger);
    color: var(--danger);
    background: var(--danger-tint);
  }
  .step:disabled {
    color: var(--ink-3);
  }
  .step:disabled .dot {
    background: transparent;
    color: var(--ink-3);
  }
  .name {
    min-width: 0;
    line-height: 1.3;
  }
  .state,
  .attn {
    display: block;
    margin-top: 0.1rem;
    font-size: 0.6875rem;
    font-weight: 650;
    letter-spacing: 0.01em;
    line-height: 1.3;
  }
  .state {
    color: var(--ink-3);
  }
  .current .state {
    color: var(--ink-2);
  }
  .attn {
    color: var(--danger);
  }
  .tools {
    margin-top: auto;
    display: grid;
    gap: 0.9rem;
    padding: 1rem 0.6rem 0;
    border-top: 1px solid var(--line);
  }
  .ruleset {
    font-size: var(--t-xs);
    color: var(--ink-3);
    line-height: 1.45;
  }
  .links {
    display: grid;
    gap: 0.15rem;
  }
  .links a,
  .link {
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.35rem 0.4rem;
    margin-left: -0.4rem;
    font-size: var(--t-sm);
    font-weight: 550;
    color: var(--ink-2);
    text-decoration: none;
    border-radius: var(--radius-sm);
    border: 0;
    background: none;
    cursor: pointer;
    justify-self: start;
  }
  .links a:hover,
  .link:hover {
    color: var(--ink);
    background: rgb(9 9 11 / 0.05);
  }
  .links a:focus-visible,
  .link:focus-visible {
    outline: none;
    box-shadow: var(--focus);
  }
</style>
