<script>
  import Notice from "../ui/Notice.svelte";
  import { app } from "../lib/state.svelte.js";
  import { engine } from "../lib/engine.js";
  import { rand, g } from "../lib/format.js";

  let { baseTotal } = $props();
  let budget = $state(null);
  let res = $state(null);

  $effect(() => {
    const b = budget;
    const snap = JSON.parse(JSON.stringify(app.session));
    const t = setTimeout(async () => {
      res = await engine("tf_routes", snap, b);
      if (res.ok && budget === null) budget = res.budget;
    }, 120);
    return () => clearTimeout(t);
  });
</script>

<div class="tf">
  <Notice tone="warning" compact title="Draft 2026 rules (GG 54032): not in force. Planning only." />
  {#if res && !res.ok}
    <p class="muted">{res.reason}</p>
  {:else if res}
    <label class="slider">
      <span class="lab">Contribution budget per year <strong>{rand(budget ?? res.budget)}</strong> <span class="muted">({res.pct_of_npat.toFixed(2)}% of NPAT)</span></span>
      <input type="range" min={res.min} max={res.max} step="1000" bind:value={budget} />
    </label>
    <p class="muted">The two routes are either/or.</p>
    <div class="routes">
      {#each res.routes as rt (rt.name)}
        <div class="route">
          <h3>{rt.name}</h3>
          <dl>
            <div><dt>ESD points</dt><dd>{g(Math.round(rt.esd_points * 10) / 10)}</dd></div>
            <div><dt>New total</dt><dd>{g(Math.round(rt.total * 10) / 10)} <span class:up={rt.delta > 0} class="delta">{rt.delta >= 0 ? "+" : ""}{g(Math.round(rt.delta * 10) / 10)}</span></dd></div>
            <div><dt>Level</dt><dd>{rt.level_label}</dd></div>
          </dl>
        </div>
      {/each}
    </div>
    <p class="muted small">{res.split_note}</p>
  {/if}
</div>

<style>
  .tf {
    display: grid;
    gap: 0.9rem;
  }
  .slider {
    display: grid;
    gap: 0.4rem;
  }
  .lab {
    font-size: var(--t-sm);
    font-weight: 600;
  }
  input[type="range"] {
    width: 100%;
    accent-color: var(--primary);
  }
  .routes {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.9rem;
  }
  .route {
    border: 1px solid var(--line);
    border-radius: var(--radius);
    padding: 0.9rem 1rem;
    background: var(--surface-2);
  }
  h3 {
    font-size: var(--t-md);
    margin-bottom: 0.6rem;
  }
  dl {
    margin: 0;
    display: grid;
    gap: 0.4rem;
  }
  dl div {
    display: flex;
    justify-content: space-between;
    gap: 1rem;
  }
  dt {
    color: var(--ink-3);
    font-size: var(--t-sm);
  }
  dd {
    margin: 0;
    font-weight: 700;
  }
  .delta {
    font-weight: 600;
    color: var(--ink-3);
    font-size: var(--t-sm);
  }
  .delta.up {
    color: var(--success);
  }
  .muted {
    color: var(--ink-3);
    font-size: var(--t-sm);
  }
  .small {
    font-size: var(--t-xs);
  }
  @media (max-width: 640px) {
    .routes {
      grid-template-columns: 1fr;
    }
  }
</style>
