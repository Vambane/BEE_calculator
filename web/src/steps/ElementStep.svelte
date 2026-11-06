<script>
  import StepFrame from "./StepFrame.svelte";
  import IndicatorInput from "./IndicatorInput.svelte";
  import Card from "../ui/Card.svelte";
  import Field from "../ui/Field.svelte";
  import NumberInput from "../ui/NumberInput.svelte";
  import Segmented from "../ui/Segmented.svelte";
  import ProcurementPanel from "../calc/ProcurementPanel.svelte";
  import ContributionsPanel from "../calc/ContributionsPanel.svelte";
  import NetValuePanel from "../calc/NetValuePanel.svelte";
  import { app } from "../lib/state.svelte.js";
  import { engine } from "../lib/engine.js";
  import { untrack } from "svelte";
  import { rand, g } from "../lib/format.js";

  let { spec } = $props();

  const store = $derived(app.session.store);
  const key = $derived(spec.key);

  // app.py records the effective entry choice and mode on every render; do the same once.
  // The component is re-created per step, so reading `spec` once here is intended.
  untrack(() => {
    if (!(spec.key in app.session.store.entry)) app.session.store.entry[spec.key] = spec.entry;
    if (!(spec.key in app.session.store.modes)) app.session.store.modes[spec.key] = spec.mode;
  });

  const entry = $derived(store.entry[key] ?? spec.entry);
  const mode = $derived(spec.mode);

  // Value buckets must exist before inputs bind to them (also after a mode conversion).
  function ensureBuckets() {
    untrack(() => {
      const st = app.session.store;
      for (const m of ["rand", "pct"]) if (!st.values[m][spec.key]) st.values[m][spec.key] = {};
      if (!st.points[spec.key]) st.points[spec.key] = {};
    });
  }
  ensureBuckets();
  const vals = $derived(store.values[mode][key] ?? {});
  const pts = $derived(store.points[key] ?? {});

  let converting = $state(false);
  async function switchMode(next) {
    converting = true;
    try {
      const updated = await engine("convert_mode", app.session, key, next);
      updated.consent = app.session.store.consent;
      app.session.store = updated;
      ensureBuckets();
    } finally {
      converting = false;
    }
  }

  // Net Value: the engine takes "% of target achieved"; people enter points.
  const nvPoints = {
    get v() {
      const x = vals[spec.net_value.clause];
      return Math.round(((typeof x === "number" ? x : 0) * spec.net_value.points) / 100 * 100) / 100;
    },
    set v(p) {
      vals[spec.net_value.clause] = ((p ?? 0) / spec.net_value.points) * 100;
    },
  };

  const economicInterest = $derived.by(() => {
    if (mode !== "pct") return null;
    for (const u of spec.units) {
      for (const ind of u.kind === "pair" ? [u.black] : [u.ind]) {
        const low = ind.name.toLowerCase();
        if (low.includes("economic interest") && low.includes("black") && !/women|female|designated/.test(low)) {
          const v = vals[ind.clause];
          return typeof v === "number" ? v : null;
        }
      }
    }
    return null;
  });

  const intro = $derived(
    entry === "pts"
      ? "Enter the points from your verification agency or consultant."
      : mode === "rand"
        ? "Enter rand amounts for the measurement year. They are converted using the bases in your profile."
        : "Enter each indicator as a percentage. Leave anything you do not have at zero.",
  );
</script>

<StepFrame title={spec.name} {intro}>
  {#snippet aside()}
    <div class="max"><span>Up to</span> <strong>{g(spec.max)}</strong> <span>points</span></div>
  {/snippet}

  {#if spec.entry_options.length > 1 || spec.can_rand}
    <div class="switches">
      {#if spec.entry_options.length > 1}
        <div class="sw">
          <span class="sw-label" id="entry-{key}">Enter</span>
          <Segmented
            label="How to enter {spec.name}"
            bind:value={store.entry[key]}
            options={[
              { value: "ind", label: "Indicators" },
              { value: "pts", label: "Points (pre-calculated)" },
            ]}
          />
        </div>
      {/if}
      {#if entry === "ind" && spec.can_rand}
        <div class="sw">
          <span class="sw-label">Amounts as</span>
          <Segmented
            label="Enter amounts as"
            value={mode}
            disabled={converting}
            onchange={switchMode}
            options={[
              { value: "rand", label: "Rand amounts" },
              { value: "pct", label: "Percentages" },
            ]}
          />
        </div>
      {/if}
    </div>
  {/if}

  {#if entry === "pts"}
    <Card title="Points" description="Each field is capped at its weighting on this scorecard.">
      <div class="grid">
        {#each spec.point_groups as grp (grp.key)}
          <Field id="pt-{key}-{grp.key}" label={grp.label} aside={undefined}>
            <NumberInput id="pt-{key}-{grp.key}" bind:value={pts[grp.key]} decimals={1} min={0} max={grp.max} suffix="of {g(grp.max)}" />
          </Field>
        {/each}
        {#if spec.bonus_max}
          <Field id="pt-{key}-bonus" label="Bonus points">
            <NumberInput id="pt-{key}-bonus" bind:value={pts.bonus} decimals={1} min={0} max={spec.bonus_max} suffix="of {g(spec.bonus_max)}" />
          </Field>
        {/if}
      </div>
    </Card>
  {:else}
    {#if spec.procurement}<ProcurementPanel el={spec} {mode} {vals} />{/if}
    {#if spec.contributions.length}<ContributionsPanel el={spec} {mode} {vals} />{/if}

    {#if spec.net_value}
      <Card
        title="Net Value"
        description="Calculate it from share values and debt, or enter your verification agency's figure (needed for flow-through structures)."
      >
        <NetValuePanel el={spec} nv={spec.net_value} {mode} {vals} {economicInterest} bind:points={nvPoints.v} />
        <div class="nv-field">
          <Field
            id="nv-pts-{key}"
            label="Net Value points"
            help={(spec.net_value.submin ? `Sub-minimum ${g(spec.net_value.submin)} of ${g(spec.net_value.points)}. ` : "") +
              "No figure yet? Leave 0 and Ownership is flagged as at risk."}
          >
            <NumberInput id="nv-pts-{key}" bind:value={nvPoints.v} decimals={2} min={0} max={spec.net_value.points} suffix="of {g(spec.net_value.points)}" />
          </Field>
        </div>
      </Card>
    {/if}

    <Card title="Indicators" description={spec.eap_note ? "Targets are the gazetted percentages. Any EAP demographic adjustment is applied by your verification agency." : ""}>
      <div class="units">
        {#each spec.units as u, i (i)}
          {#if u.kind === "pair"}
            <fieldset class="pair">
              <legend>{u.heading}</legend>
              <div class="grid">
                <IndicatorInput ind={u.black} label={u.labels[0]} {vals} />
                <IndicatorInput ind={u.women} label={u.labels[1]} {vals} />
              </div>
              <p class="pair-note">
                Black women / Black female is scored on its own line. Enter it even when it is already
                included in the Black people figure.
              </p>
            </fieldset>
          {:else}
            <div class="single">
              <IndicatorInput ind={u.ind} label={u.ind.name} {vals} />
            </div>
          {/if}
        {/each}
      </div>
      {#if mode === "rand" && spec.bases.length}
        <p class="bases">
          Bases from your profile:
          {#each spec.bases as b, i (b.label)}{i ? ", " : ""}{b.label} <strong>{b.label === "headcount" ? g(b.value) : rand(b.value)}</strong>{/each}
        </p>
      {/if}
    </Card>
  {/if}

  {#if spec.submins.length}
    <section class="submins" aria-labelledby="submins-h">
      <h2 id="submins-h">Sub-minimums</h2>
      <p>Missing any of these drops the overall level by one.</p>
      <ul>
        {#each spec.submins as sm, i (i)}
          <li>
            <span class="what">{sm.group ?? `${spec.name} total`}</span>
            <span class="need"><strong>{g(sm.required)}</strong> points</span>
            <span class="cl">{sm.clause}</span>
          </li>
        {/each}
      </ul>
    </section>
  {/if}
</StepFrame>

<style>
  .max {
    font-size: var(--t-sm);
    color: var(--ink-3);
    white-space: nowrap;
  }
  .max strong {
    font-size: var(--t-xl);
    color: var(--ink);
    font-weight: 700;
    margin: 0 0.15rem;
  }
  .switches {
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem 1.5rem;
    align-items: center;
  }
  .sw {
    display: flex;
    align-items: center;
    gap: 0.6rem;
  }
  .sw-label {
    font-size: var(--t-sm);
    font-weight: 600;
    color: var(--ink-2);
  }
  .grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 1rem 1.1rem;
    align-items: start;
  }
  .units {
    display: grid;
    gap: 0;
  }
  .single,
  .pair {
    padding: 1rem 0;
    border-top: 1px solid var(--line);
  }
  .units > :first-child {
    padding-top: 0;
    border-top: 0;
  }
  .single {
    max-width: calc(50% - 0.55rem);
  }
  .pair {
    margin: 0;
    border-left: 0;
    border-right: 0;
    border-bottom: 0;
    display: grid;
    gap: 0.75rem;
  }
  legend {
    padding: 0;
    float: left;
    width: 100%;
    font-weight: 650;
    font-size: var(--t-md);
    margin-bottom: 0.75rem;
  }
  .pair .grid {
    clear: both;
  }
  .pair-note {
    font-size: var(--t-xs);
    color: var(--ink-3);
  }
  .nv-field {
    max-width: calc(50% - 0.55rem);
  }
  .bases {
    font-size: var(--t-xs);
    color: var(--ink-3);
    padding-top: 0.75rem;
    border-top: 1px solid var(--line);
  }
  .bases strong {
    color: var(--ink-2);
  }
  .submins {
    padding: 1rem 1.25rem;
    border: 1px solid var(--line);
    border-radius: var(--radius-lg);
    background: var(--surface-2);
    font-size: var(--t-sm);
    color: var(--ink-2);
  }
  .submins h2 {
    font-size: var(--t-md);
    font-weight: 650;
    color: var(--ink);
  }
  .submins p {
    margin: 0.15rem 0 0.6rem;
    color: var(--ink-3);
  }
  .submins ul {
    margin: 0;
    padding: 0;
    list-style: none;
  }
  .submins li {
    display: grid;
    grid-template-columns: minmax(0, 1fr) auto;
    gap: 0 1rem;
    padding: 0.5rem 0;
    border-top: 1px solid var(--line);
  }
  .submins .what {
    color: var(--ink);
    font-weight: 600;
  }
  .submins .need {
    text-align: right;
  }
  .submins .need strong {
    color: var(--ink);
  }
  .submins .cl {
    grid-column: 1 / -1;
    font-size: var(--t-xs);
    color: var(--ink-3);
  }
  @media (max-width: 640px) {
    .grid {
      grid-template-columns: 1fr;
    }
    .single,
    .nv-field {
      max-width: none;
    }
  }
</style>
