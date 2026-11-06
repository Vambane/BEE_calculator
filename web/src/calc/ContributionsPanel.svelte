<script>
  import { Check } from "@lucide/svelte";
  import Disclosure from "../ui/Disclosure.svelte";
  import EditTable from "../ui/EditTable.svelte";
  import Button from "../ui/Button.svelte";
  import Notice from "../ui/Notice.svelte";
  import { app } from "../lib/state.svelte.js";
  import { engine } from "../lib/engine.js";
  import { g } from "../lib/format.js";
  import { untrack } from "svelte";

  let { el, mode, vals } = $props();

  const store = $derived(app.session.store);
  const key = untrack(() => el.key); // re-created per step
  if (!app.session.store.contributions[key]) {
    app.session.store.contributions[key] = { records: [], version: 0, current: null };
  }
  const box0 = app.session.store.contributions[key];
  if (box0.current) {
    box0.records = box0.current;
    box0.current = null;
  }

  let open = $state(box0.records.length > 0);
  let types = $state(null);
  let summary = $state(null);
  let applied = $state(false);

  $effect(() => {
    engine("contribution_types", app.session, key).then((t) => (types = t));
  });

  const columns = $derived(
    types
      ? [
          { key: "b", label: "Beneficiary", type: "text", width: "11rem" },
          { key: "c", label: "Counts towards", type: "select", options: types.targets, required: true, default: types.targets[0], width: "12rem" },
          { key: "t", label: "Contribution type", type: "select", options: types.types, required: true, default: types.types[0], width: "14rem" },
          { key: "a", label: "Amount (R)", type: "number", decimals: 2, width: "8rem" },
          { key: "p", label: "Prime / ordinary rate %", type: "number", width: "7rem", help: "Lower-interest loans: prime. Lower-dividend investments: the ordinary dividend rate." },
          { key: "r", label: "Actual rate %", type: "number", width: "6rem", help: "The rate actually charged or paid" },
        ]
      : [],
  );

  let seq = 0;
  $effect(() => {
    JSON.stringify(store.contributions[key].records);
    JSON.stringify(store.fin);
    const t = setTimeout(async () => {
      const mySeq = ++seq;
      const out = await engine("contributions_summary", app.session, key, store.contributions[key].records);
      if (mySeq === seq) summary = out;
    }, 150);
    return () => clearTimeout(t);
  });

  function apply() {
    for (const [clause, v] of Object.entries(summary.apply)) vals[clause] = v;
    applied = true;
    setTimeout(() => (applied = false), 4000);
  }
</script>

<Disclosure
  title="Value contributions with benefit factors"
  summary="Applies the Annexe 400(B) / 500(A) benefit factors to each contribution"
  bind:open
>
  <p class="explain">
    List each contribution at face value and pick its type. The gazetted benefit factor is applied
    (for example an interest-free loan counts at 70%, a guarantee at 50%, staff time at 60%) and the
    recognised value is totalled per indicator.
  </p>
  {#if types}
    <EditTable
      {columns}
      bind:rows={store.contributions[key].records}
      caption="Contribution lines"
      emptyText="Add contribution lines to see their recognised value."
    />
  {/if}

  {#if summary?.errors?.length}
    <Notice tone="warning" title="Fix these lines to include them" lines={[...summary.errors, ...(summary.more_errors ? [`…and ${summary.more_errors} more`] : [])]} />
  {/if}

  {#if summary?.rows?.length}
    <div class="scroll">
      <table class="data">
        <thead>
          <tr><th>Indicator</th><th class="r">Face value</th><th class="r">Recognised</th><th class="r">% of NPAT</th><th class="r">Target</th><th class="r">Points</th></tr>
        </thead>
        <tbody>
          {#each summary.rows as r (r.indicator)}
            <tr>
              <td>{r.indicator}</td>
              <td class="r">{r.face}</td>
              <td class="r">{r.recognised}</td>
              <td class="r">{r.pct === null ? "Enter NPAT" : `${r.pct.toFixed(2)}%`}</td>
              <td class="r">{r.target}</td>
              <td class="r">{#if r.points === null}–{:else}<strong>{r.points.toFixed(2)}</strong> of {g(r.max)}{/if}</td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
    {#each summary.notes as n, i (i)}<p class="note">{n}</p>{/each}
    <p class="note">
      Shorter payment periods to SD beneficiaries use a separate formula: add them to the Supplier
      Development figure by hand.
    </p>
    {#if !summary.can_apply}
      <p class="note">Enter a positive NPAT (or the Turnover basis) in the profile to apply these values.</p>
    {/if}
    <div class="row">
      <Button variant="primary" size="sm" icon={Check} disabled={!summary.can_apply} onclick={apply}>Use these values</Button>
      {#if applied}<span class="done" role="status">Recognised contribution values filled in below.</span>{/if}
    </div>
  {/if}
</Disclosure>

<style>
  .explain {
    color: var(--ink-2);
    font-size: var(--t-sm);
    max-width: 72ch;
  }
  .scroll {
    overflow-x: auto;
  }
  .note {
    font-size: var(--t-xs);
    color: var(--ink-3);
    max-width: 80ch;
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
</style>
