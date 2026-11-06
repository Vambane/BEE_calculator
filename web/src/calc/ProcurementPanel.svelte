<script>
  import { FileDown, Upload, Check, Download } from "@lucide/svelte";
  import Disclosure from "../ui/Disclosure.svelte";
  import EditTable from "../ui/EditTable.svelte";
  import Button from "../ui/Button.svelte";
  import Notice from "../ui/Notice.svelte";
  import { app } from "../lib/state.svelte.js";
  import { engine } from "../lib/engine.js";
  import { downloadText, pickFile, readTextFile } from "../lib/files.js";
  import { rand, g } from "../lib/format.js";

  let { el, mode, vals } = $props();

  const store = $derived(app.session.store);
  if (!app.session.store.procurement) app.session.store.procurement = { records: [], version: 0 };
  // A file saved by the Streamlit app may carry the editor's live rows in "current".
  if (app.session.store.procurement.current) {
    app.session.store.procurement.records = app.session.store.procurement.current;
    app.session.store.procurement.current = null;
  }

  let open = $state(app.session.store.procurement.records.length > 0);
  let summary = $state(null);
  let uploadErrors = $state(null);
  let applied = $state(false);

  const m = app.meta.proc;
  const columns = [
    { key: "s", label: "Supplier", type: "text", width: "12rem" },
    { key: "sp", label: "Spend (R)", type: "number", decimals: 2, width: "8rem" },
    { key: "l", label: "B-BBEE level", type: "select", options: app.meta.level_options, width: "6rem", help: "1 to 8, or NC for no certificate" },
    { key: "z", label: "Size", type: "select", options: m.sizes, width: "7rem" },
    { key: "bo", label: "Black ownership %", type: "number", width: "7rem" },
    { key: "bw", label: "Black women ownership %", type: "number", width: "8rem" },
    { key: "dg", label: "Designated group", type: "bool", help: "At least 51% owned by black designated groups" },
    { key: "es", label: "Empowering supplier", type: "bool", help: "As stated on the certificate or affidavit; EMEs always are (cl. 3.3.4)" },
    { key: "mx", label: "1.2x multiplier", type: "bool", help: "Statement 400 cl. 3.5" },
    { key: "ex", label: "TMPS exclusion", type: "select", options: m.exclusions, required: true, default: m.exclusions[0], width: "12rem" },
  ];

  let seq = 0;
  async function recompute() {
    const mySeq = ++seq;
    const out = await engine("procurement_summary", app.session, el.key, store.procurement.records);
    if (mySeq === seq) summary = out;
  }
  $effect(() => {
    JSON.stringify(store.procurement.records);
    const t = setTimeout(recompute, 150);
    return () => clearTimeout(t);
  });

  async function template() {
    downloadText(await engine("procurement_template"), "supplier-list-template.csv", "text/csv");
  }
  async function upload() {
    const file = await pickFile(".csv,text/csv");
    if (!file) return;
    uploadErrors = null;
    try {
      const out = await engine("procurement_parse_csv", await readTextFile(file, m.max_csv_bytes));
      if (!out.ok) {
        uploadErrors = [...out.errors, ...(out.more ? [`…and ${out.more} more`] : [])];
        return;
      }
      store.procurement.records = out.records;
      store.procurement.version = (store.procurement.version ?? 0) + 1;
      open = true;
    } catch (err) {
      uploadErrors = [err.message];
    }
  }
  function apply() {
    const tmps = summary.tmps;
    store.fin.tmps = tmps;
    for (const [clause, pct] of Object.entries(summary.apply)) {
      vals[clause] = mode === "rand" ? (pct * tmps) / 100 : pct;
    }
    applied = true;
    setTimeout(() => (applied = false), 4000);
  }
</script>

<Disclosure
  title="Calculate procurement from a supplier list"
  summary="Works out TMPS and recognised spend for each procurement indicator"
  bind:open
>
  <p class="explain">
    List every supplier paid in the measurement year with their B-BBEE level, size and ownership from
    their certificate or affidavit. Only Empowering Suppliers count; suppliers with no certificate
    count at 0%.
  </p>
  <div class="row">
    <Button size="sm" icon={FileDown} onclick={template}>Download template (CSV)</Button>
    <Button size="sm" icon={Upload} onclick={upload}>Upload supplier list (CSV)</Button>
    <span class="hint">CSV in the template's format, up to 2 MB.</span>
  </div>
  {#if uploadErrors}
    <Notice tone="danger" title="Problems in that file. Fix them and upload again." lines={uploadErrors} />
  {/if}

  <EditTable
    {columns}
    bind:rows={store.procurement.records}
    caption="Supplier list"
    emptyText="Add suppliers here, or upload the template, to see the calculation."
  />

  {#if summary?.errors?.length}
    <Notice tone="warning" title="Fix these rows to include them" lines={[...summary.errors, ...(summary.more_errors ? [`…and ${summary.more_errors} more`] : [])]} />
  {/if}

  {#if summary?.tmps !== undefined}
    <dl class="metrics">
      <div><dt>Total spend</dt><dd>{rand(summary.total_spend)}</dd></div>
      <div><dt>Excluded</dt><dd>{rand(summary.excluded)}</dd></div>
      <div class="key"><dt>TMPS</dt><dd>{rand(summary.tmps)}</dd></div>
    </dl>
    {#if summary.rows.length}
      <div class="scroll">
        <table class="data">
          <thead>
            <tr><th>Indicator</th><th class="r">Recognised spend</th><th class="r">% of TMPS</th><th class="r">Target</th><th class="r">Points</th></tr>
          </thead>
          <tbody>
            {#each summary.rows as r (r.indicator)}
              <tr>
                <td>{r.indicator}</td>
                <td class="r">{r.recognised}</td>
                <td class="r">{r.pct.toFixed(2)}%</td>
                <td class="r">{r.target}</td>
                <td class="r"><strong>{r.points.toFixed(2)}</strong> of {g(r.max)}</td>
              </tr>
            {/each}
          </tbody>
        </table>
      </div>
    {/if}
    {#each summary.notes as n, i (i)}<p class="note">{n}</p>{/each}
    {#if summary.unmatched.length}
      <p class="note">Enter by hand (not measurable from the list): {summary.unmatched.join("; ")}.</p>
    {/if}
    <p class="note">
      Recognised spend = spend × the supplier's recognition % (Level 1 135% … Level 8 10%), × 1.2
      where ticked (cl. 3.5). Planning estimate: confirm exclusions, multipliers and supplier
      evidence with your verification agency.
    </p>
    <div class="row">
      <Button variant="primary" size="sm" icon={Check} disabled={!(summary.tmps > 0)} onclick={apply}>Use these figures</Button>
      <Button size="sm" icon={Download} onclick={() => downloadText(summary.csv, "supplier-list.csv", "text/csv")}>Download this list (CSV)</Button>
      {#if applied}<span class="done" role="status">TMPS set in the profile and procurement indicators filled in below.</span>{/if}
    </div>
  {/if}
</Disclosure>

<style>
  .explain {
    color: var(--ink-2);
    font-size: var(--t-sm);
    max-width: 72ch;
  }
  .row {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 0.5rem 0.6rem;
  }
  .hint {
    font-size: var(--t-xs);
    color: var(--ink-3);
  }
  .metrics {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 0.75rem;
    margin: 0;
  }
  .metrics div {
    padding: 0.7rem 0.85rem;
    border: 1px solid var(--line);
    border-radius: var(--radius);
    background: var(--surface-2);
  }
  .metrics .key {
    background: var(--primary-tint);
    border-color: var(--primary-tint-2);
  }
  dt {
    font-size: var(--t-xs);
    color: var(--ink-3);
    font-weight: 600;
  }
  dd {
    margin: 0.15rem 0 0;
    font-size: var(--t-lg);
    font-weight: 700;
  }
  .scroll {
    overflow-x: auto;
  }
  .note {
    font-size: var(--t-xs);
    color: var(--ink-3);
    max-width: 80ch;
  }
  .done {
    font-size: var(--t-sm);
    color: var(--success);
    font-weight: 600;
  }
  @media (max-width: 640px) {
    .metrics {
      grid-template-columns: 1fr;
    }
  }
</style>
