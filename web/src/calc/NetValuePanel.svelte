<script>
  import { Check } from "@lucide/svelte";
  import Disclosure from "../ui/Disclosure.svelte";
  import Field from "../ui/Field.svelte";
  import NumberInput from "../ui/NumberInput.svelte";
  import Button from "../ui/Button.svelte";
  import Notice from "../ui/Notice.svelte";
  import { app } from "../lib/state.svelte.js";
  import { engine } from "../lib/engine.js";
  import { g } from "../lib/format.js";
  import { untrack } from "svelte";

  /** Annexe 100(E) Net Value. `nv` is the element's Net Value spec; `points` is bindable. */
  let { el, nv, mode, vals, economicInterest = null, points = $bindable(0) } = $props();

  const today = new Date().toISOString().slice(0, 10);
  const key = untrack(() => el.key); // re-created per step
  const defaults = {
    black_equity_value: 0,
    acquisition_debt: 0,
    entity_value: 0,
    economic_interest_pct: null,
    equity_date: null,
    measurement_date: null,
    target_pct: app.meta.net_value_target,
  };
  // Older or partial files may lack keys; merge over the defaults.
  app.session.store.net_value[key] = { ...defaults, ...(app.session.store.net_value[key] ?? {}) };
  const box = $derived(app.session.store.net_value[key]);
  untrack(() => {
    if (box.economic_interest_pct === null && economicInterest !== null) box.economic_interest_pct = economicInterest;
  });

  let open = $state(untrack(() => Boolean(box.entity_value)));
  let res = $state(null);
  let applied = $state(false);

  const dates = {
    get equity() {
      return box.equity_date ?? today;
    },
    set equity(v) {
      box.equity_date = v || null;
    },
    get measure() {
      return box.measurement_date ?? today;
    },
    set measure(v) {
      box.measurement_date = v || null;
    },
  };

  let seq = 0;
  $effect(() => {
    const snapshot = JSON.stringify(box);
    const t = setTimeout(async () => {
      const mySeq = ++seq;
      const out = await engine("net_value", app.session, key, JSON.parse(snapshot));
      if (mySeq === seq) res = out;
    }, 150);
    return () => clearTimeout(t);
  });

  function apply() {
    points = res.points;
    applied = true;
    setTimeout(() => (applied = false), 4000);
  }
</script>

<Disclosure
  title="Calculate Net Value from share values"
  summary="Annexe 100(E): the lower of Formula A and Formula B"
  bind:open
>
  <p class="explain">
    <strong>Formula A</strong> takes the black shareholders' equity less the debt still owed on it, as
    a share of the company's value, against the target scaled by how long they have held it.
    <strong>Formula B</strong> takes their economic interest against the target. Use values on the
    measurement date; for an unlisted company, from a competent person's valuation.
  </p>
  <div class="grid">
    <Field id="nv-d-{key}" label="Value of the company">
      <NumberInput id="nv-d-{key}" prefix="R" bind:value={box.entity_value} />
    </Field>
    <Field id="nv-b-{key}" label="Value of black-held shares">
      <NumberInput id="nv-b-{key}" prefix="R" bind:value={box.black_equity_value} />
    </Field>
    <Field id="nv-c-{key}" label="Acquisition debt still owed" help="Loans and vendor finance used to buy those shares, including unpaid notional funding.">
      <NumberInput id="nv-c-{key}" prefix="R" bind:value={box.acquisition_debt} />
    </Field>
    <Field id="nv-e-{key}" label="Black economic interest" help="Usually the same figure as the economic interest indicator.">
      <NumberInput id="nv-e-{key}" suffix="%" decimals={2} min={0} max={100} bind:value={box.economic_interest_pct} />
    </Field>
    <Field id="nv-t0-{key}" label="Current equity interest date" help="When the shareholding became effective and unconditional. Year 1 is the first 12 months.">
      <input class="date" id="nv-t0-{key}" type="date" max={today} bind:value={dates.equity} />
    </Field>
    <Field id="nv-t1-{key}" label="Measurement date" help="End of the period your verification covers.">
      <input class="date" id="nv-t1-{key}" type="date" bind:value={dates.measure} />
    </Field>
    <Field id="nv-tp-{key}" label="Net Value target" help="{g(app.meta.net_value_target)}% on the Generic and QSE scorecards. Check your sector code.">
      <NumberInput id="nv-tp-{key}" suffix="%" decimals={1} min={0.5} max={100} bind:value={box.target_pct} />
    </Field>
  </div>

  {#if res && !res.ok}
    <p class="note">{res.reason}</p>
  {:else if res?.ok}
    <table class="data kv">
      <tbody>
        {#each res.rows as [k, v] (k)}<tr><th scope="row">{k}</th><td class="r">{v}</td></tr>{/each}
        <tr class="total"><th scope="row">Net Value points (lower of A and B)</th><td class="r">{g(res.points)} of {g(res.max)}</td></tr>
      </tbody>
    </table>
    {#each res.notes as n, i (i)}<p class="note">{n}</p>{/each}
    {#if res.below_submin}
      <Notice tone="warning" compact>Below the {g(res.submin)}-point sub-minimum: the overall level drops by one.</Notice>
    {/if}
    {#if economicInterest !== null && Math.abs(economicInterest - (box.economic_interest_pct ?? 0)) > 1e-9}
      <p class="note">The economic interest indicator on this step is {g(economicInterest)}%, not {g(box.economic_interest_pct)}%. Check which is right.</p>
    {/if}
    <div class="row">
      <Button variant="primary" size="sm" icon={Check} onclick={apply}>Use this figure</Button>
      {#if applied}<span class="done" role="status">Net Value points set from this calculation.</span>{/if}
    </div>
  {/if}
</Disclosure>

<style>
  .explain {
    color: var(--ink-2);
    font-size: var(--t-sm);
    max-width: 74ch;
  }
  .grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 1rem 1.1rem;
  }
  .date {
    height: 40px;
    width: 100%;
    padding: 0 0.75rem;
    border: 1px solid var(--line-strong);
    border-radius: var(--radius);
    background: var(--surface);
    font-size: var(--t-md);
    font-variant-numeric: tabular-nums;
  }
  .date:focus-visible {
    outline: none;
    border-color: var(--primary);
    box-shadow: var(--focus);
  }
  .kv th {
    font-weight: 500;
    color: var(--ink-2);
  }
  .total th,
  .total td {
    font-weight: 700;
    color: var(--ink);
    background: var(--primary-tint);
  }
  .note {
    font-size: var(--t-xs);
    color: var(--ink-3);
  }
  .row {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }
  .done {
    font-size: var(--t-sm);
    color: var(--success);
    font-weight: 600;
  }
  @media (max-width: 640px) {
    .grid {
      grid-template-columns: 1fr;
    }
  }
</style>
