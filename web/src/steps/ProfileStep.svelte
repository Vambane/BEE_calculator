<script>
  import StepFrame from "./StepFrame.svelte";
  import Card from "../ui/Card.svelte";
  import Field from "../ui/Field.svelte";
  import NumberInput from "../ui/NumberInput.svelte";
  import Select from "../ui/Select.svelte";
  import Checkbox from "../ui/Checkbox.svelte";
  import Disclosure from "../ui/Disclosure.svelte";
  import Notice from "../ui/Notice.svelte";
  import { app, consented } from "../lib/state.svelte.js";

  const s = $derived(app.session.store);
  const p = $derived(s.profile);
  const f = $derived(s.fin);
  const ctx = $derived(app.ctx);
  const locked = $derived(!consented());

  const sectorOptions = $derived(app.meta.sectors.map((x) => ({ value: x.key, label: x.name })));
  const variantOptions = $derived(
    (ctx.variants ?? []).map((v) => ({ value: v, label: v.replaceAll("_", " ").replace(/^\w/, (c) => c.toUpperCase()) })),
  );
  const tierOptions = [
    { value: "none", label: "None" },
    { value: "target", label: "Target met" },
    { value: "1.5x", label: "1.5 times the target" },
    { value: "2x", label: "2 times the target" },
  ];
  const prevOptions = [{ value: "", label: "Not applicable" }, ...[1, 2, 3, 4, 5, 6, 7, 8].map((n) => ({ value: String(n), label: `Level ${n}` }))];

  let lowOpen = $state(false);
  $effect(() => {
    if ((f.npat ?? 0) < 0 || f.npat_avg_5y !== null || f.industry_norm_margin_pct || f.qualifying_margin_pct) lowOpen = true;
  });

  const lowTone = $derived(
    { npat: "info", info: "info", warning: "warning", error: "danger" }[ctx.low_profit?.state] ?? "info",
  );

  const prevLevel = {
    get value() {
      return p.yes_prev_level === null ? "" : String(p.yes_prev_level);
    },
    set value(v) {
      p.yes_prev_level = v === "" ? null : Number(v);
    },
  };
</script>

<StepFrame
  title="Company profile"
  intro="Start with the figures that set the scorecard: size, ownership and the bases that rand amounts are measured against. Enter what you know; you can come back to any step."
>
  <Card
    title="Privacy and consent"
    description="BEE Check runs entirely in your browser. Nothing you enter is sent to a server."
  >
    <div class="privacy">
      <p>
        We use the company figures you enter only to calculate a B-BBEE scorecard. Aggregates that
        relate to race or gender are special personal information under POPIA s26; they are
        processed only for this scorecard, on your device. We do not ask for ID numbers or
        individual names. Your figures are cleared when you close or reload the page, unless you
        save a client file.
      </p>
      <p class="links"><a href="#/privacy">Read the full privacy policy</a> · <a href="#/howto">How to use this calculator</a></p>
    </div>
    <div class="consent" class:ok={s.consent}>
      <Checkbox id="consent" bind:checked={s.consent}>
        I have read the privacy notice and agree to this processing for this scorecard.
      </Checkbox>
    </div>
  </Card>

  <Card title="Company" description={locked ? "Tick the consent box above to unlock these fields." : ""}>
    <div class="grid">
      <div class="span2">
        <Field id="company" label="Company name" optional help="Shown on the report and used to name the client file.">
          <input
            id="company"
            class="text"
            type="text"
            maxlength="120"
            autocomplete="organization"
            disabled={locked}
            bind:value={p.company}
          />
        </Field>
      </div>
      <Field id="sector" label="Sector code" help="The sector code the business is measured under. If unsure, keep Generic.">
        <Select id="sector" bind:value={app.session.sector} options={sectorOptions} disabled={locked} />
      </Field>
      {#if variantOptions.length}
        <Field id="variant" label="Scorecard variant">
          <Select id="variant" bind:value={p.variant} options={variantOptions} disabled={locked} />
        </Field>
      {/if}
    </div>

    <div class="grid">
      <Field id="revenue" label="Total revenue, last financial year">
        <NumberInput id="revenue" prefix="R" bind:value={p.revenue} disabled={locked} />
      </Field>
      <Field id="bo" label="Black ownership" help="Voting rights and economic interest, 0 to 100% (Statement 100).">
        <NumberInput id="bo" suffix="%" decimals={2} bind:value={p.black_ownership} disabled={locked} />
      </Field>
    </div>

    <div class="scorecard" aria-live="polite">
      <span class="size">{ctx.size}</span>
      <span class="lab">{ctx.label}</span>
      {#if ctx.badge}<span class="badge">{ctx.badge}</span>{/if}
    </div>
    {#if ctx.sector_warning}
      <Notice tone="warning" compact>{ctx.sector_warning}</Notice>
    {/if}
  </Card>

  <Card
    title="Measurement bases"
    description="Captured once and used whenever you enter rand amounts on later steps."
  >
    <div class="grid">
      <Field id="lev" label="Leviable payroll">
        <NumberInput id="lev" prefix="R" bind:value={f.leviable_amount} disabled={locked} />
      </Field>
      <Field id="npat" label="Net profit after tax (NPAT)" help="Enter a loss as a negative number.">
        <NumberInput id="npat" prefix="R" bind:value={f.npat} disabled={locked} />
      </Field>
      <Field id="tmps" label="Total measured procurement spend (TMPS)">
        <NumberInput id="tmps" prefix="R" bind:value={f.tmps} disabled={locked} />
      </Field>
      <Field id="emp" label="Headcount (employees)">
        <NumberInput id="emp" bind:value={f.employees} disabled={locked} />
      </Field>
    </div>

    <Disclosure
      title="Loss or low profit?"
      summary="NPAT targets on a Turnover basis (Statement 400 cl. 3.2.1)"
      bind:open={lowOpen}
    >
      <p class="explain">
        SD, ED and SED targets are a percentage of NPAT. If there was no profit last year or on average
        over five years, or the margin is below a quarter of the industry norm, they are set on
        Turnover × an Indicative Profit Margin instead. Industry norms are published by Stats SA.
      </p>
      <div class="grid three">
        <Field id="avg5" label="5-year average NPAT" optional help="Leave blank if you only have last year's NPAT.">
          <NumberInput id="avg5" prefix="R" allowNull bind:value={f.npat_avg_5y} disabled={locked} />
        </Field>
        <Field id="norm" label="Industry norm margin" optional help="Net profit margin norm (Stats SA).">
          <NumberInput id="norm" suffix="%" decimals={1} allowNull min={0} max={100} bind:value={f.industry_norm_margin_pct} disabled={locked} />
        </Field>
        <Field id="qual" label="Qualifying year margin" optional help="Latest year with at least a quarter of the norm.">
          <NumberInput id="qual" suffix="%" decimals={1} allowNull min={0} max={100} bind:value={f.qualifying_margin_pct} disabled={locked} />
        </Field>
      </div>
      {#if ctx.low_profit}
        <Notice tone={lowTone} compact>{ctx.low_profit.text}</Notice>
      {/if}
    </Disclosure>
  </Card>

  <Card title="Scoring options">
    <Checkbox
      id="opt-scored"
      bind:checked={p.opt_scored}
      disabled={locked}
      help="EMEs and some black-owned QSEs can use a deemed (affidavit) level. Tick this to see the full points breakdown instead."
    >
      Score on the full scorecard even if a deemed (affidavit) level applies
    </Checkbox>

    <Disclosure title="YES Initiative" summary="Optional: recognition for YES tiers achieved">
      <div class="grid">
        <Field id="yes-tier" label="YES tier achieved">
          <Select id="yes-tier" bind:value={p.yes_tier} options={tierOptions} disabled={locked} />
        </Field>
        <Field id="yes-prev" label="Previous B-BBEE level" help="Needed for YES recognition.">
          <Select id="yes-prev" bind:value={prevLevel.value} options={prevOptions} disabled={locked} />
        </Field>
      </div>
    </Disclosure>

    {#if ctx.financial_options}
      <Disclosure title="Financial Services options" summary="Interpretations the FSC leaves open" open>
        <Field id="fs-submin" label="Skills sub-minimum (cl. 3.3.1(b))">
          <Select
            id="fs-submin"
            bind:value={s.options.fs_skills_submin}
            options={[
              { value: 8, label: "8 points (40% of 20, default)" },
              { value: 6, label: "6 points (40% of 15, as printed)" },
            ]}
            disabled={locked}
          />
        </Field>
        <Checkbox id="fs-109" bind:checked={s.options.fs_rescale_109} disabled={locked}>
          Normalise Large scorecards to 109 before the level table
        </Checkbox>
      </Disclosure>
    {/if}
  </Card>
</StepFrame>

<style>
  .privacy {
    display: grid;
    gap: 0.6rem;
    color: var(--ink-2);
    font-size: var(--t-sm);
    max-width: 72ch;
  }
  .links {
    font-weight: 550;
  }
  .consent {
    padding: 0.85rem 0.95rem;
    border-radius: var(--radius);
    background: var(--surface-2);
    border: 1px solid var(--line);
    font-weight: 550;
    transition:
      background-color 200ms var(--ease),
      border-color 200ms var(--ease);
  }
  .consent.ok {
    background: var(--primary-tint);
    border-color: var(--primary-tint-2);
  }
  .grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 1rem 1.1rem;
  }
  .three {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
  .span2 {
    grid-column: span 2;
  }
  input.text {
    height: 40px;
    width: 100%;
    padding: 0 0.75rem;
    border: 1px solid var(--line-strong);
    border-radius: var(--radius);
    background: var(--surface);
    font-size: var(--t-md);
    transition:
      border-color 150ms var(--ease),
      box-shadow 150ms var(--ease);
  }
  input.text:hover:not(:disabled) {
    border-color: #aeb8c3;
  }
  input.text:focus-visible {
    outline: none;
    border-color: var(--primary);
    box-shadow: var(--focus);
  }
  input.text:disabled {
    background: var(--rail);
    border-color: var(--line);
    color: var(--ink-3);
    cursor: not-allowed;
  }
  .scorecard {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.5rem 0.75rem;
    padding: 0.75rem 0.9rem;
    border-radius: var(--radius);
    background: var(--surface-2);
    border: 1px solid var(--line);
    font-size: var(--t-sm);
  }
  .size {
    font-weight: 700;
    color: var(--primary);
    background: var(--primary-tint);
    padding: 0.1rem 0.55rem;
    border-radius: 999px;
  }
  .lab {
    color: var(--ink-2);
    font-weight: 550;
  }
  .badge {
    font-size: var(--t-xs);
    font-weight: 650;
    color: var(--success);
    background: var(--success-tint);
    padding: 0.1rem 0.5rem;
    border-radius: 999px;
  }
  .explain {
    color: var(--ink-2);
    font-size: var(--t-sm);
    max-width: 72ch;
  }
  @media (max-width: 640px) {
    .grid,
    .three {
      grid-template-columns: minmax(0, 1fr);
    }
    .span2 {
      grid-column: auto;
    }
  }
</style>
