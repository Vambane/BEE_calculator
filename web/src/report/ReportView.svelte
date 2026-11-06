<script>
  import { ArrowLeft, Printer } from "@lucide/svelte";
  import Button from "../ui/Button.svelte";
  import Notice from "../ui/Notice.svelte";
  import LevelLadder from "../results/LevelLadder.svelte";
  import { app } from "../lib/state.svelte.js";
  import { engine } from "../lib/engine.js";
  import { g } from "../lib/format.js";

  let rep = $state(null);
  $effect(() => {
    engine("report", JSON.parse(JSON.stringify(app.session))).then((r) => (rep = r));
  });

  const sc = $derived(rep?.score);
  const fileTitle = $derived(
    `BEE gap report · ${rep?.company?.name ?? ""} · ${rep?.prepared_date ?? ""}`.replace(/\s+·\s+$/, ""),
  );
  $effect(() => {
    if (!rep?.ok) return;
    const prev = document.title;
    document.title = fileTitle; // becomes the default PDF file name in most browsers
    return () => (document.title = prev);
  });
</script>

<div class="screen-bar">
  <a class="back" href="#/"><ArrowLeft size={16} aria-hidden="true" />Back to results</a>
  <p class="hint">Use <strong>Print</strong>, then choose “Save as PDF” as the destination to keep a PDF.</p>
  <Button variant="primary" icon={Printer} disabled={!rep?.ok} onclick={() => window.print()}>Print or save as PDF</Button>
</div>

<div class="page-wrap">
  {#if !rep}
    <div class="paper loading" aria-busy="true"></div>
  {:else if !rep.ok}
    <div class="paper"><Notice tone="warning" title="The gap report is not available yet" lines={rep.problems} /></div>
  {:else}
    <article class="paper" aria-label="Gap report">
      <header class="rh">
        <div class="brand">
          <svg width="18" height="18" viewBox="0 0 22 22" aria-hidden="true"><rect x="1" y="1" width="20" height="20" rx="5" fill="#18181b" /><path d="M6.2 11.4l3.1 3.1 6.5-7" fill="none" stroke="#fff" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round" /></svg>
          Klim · B-BBEE gap report
        </div>
        <div class="date">Prepared {rep.prepared_date}</div>
      </header>

      <section class="title">
        <h1>{rep.company.name}</h1>
        <p class="lab">{rep.scorecard_label.replace(/^Scorecard: /, "")}</p>
        {#if rep.sector_note}<p class="flag">{rep.sector_note}</p>{/if}
        {#if app.session.draft}<p class="flag">Draft 2026 rules applied (GG 54032): not in force.</p>{/if}
      </section>

      <section class="headline">
        <div class="big">
          <span class="k">Recognition level</span>
          <span class="lv" class:nc={sc.level === 9}>{rep.result.level_label}</span>
          <span class="s">{sc.recognition_pct}% procurement recognition</span>
        </div>
        <div><span class="k">Total points</span><span class="n">{g(Math.round(rep.result.total * 10) / 10)}<small>&nbsp;of {g(rep.result.max_total)}</small></span></div>
        <div><span class="k">{sc.next_gap ? `To Level ${sc.next_gap.level}` : "Next level"}</span><span class="n">{#if sc.next_gap}{g(Math.round(sc.next_gap.points * 10) / 10)}<small>&nbsp;pts</small>{:else}Level 1 reached{/if}</span></div>
        {#if sc.gender}<div><span class="k">Black women / Black female</span><span class="n">{g(sc.gender.achieved)}<small>&nbsp;of {g(sc.gender.max)} pts</small></span></div>{/if}
      </section>
      {#if sc.level_points !== null}
        <LevelLadder levels={app.meta.levels} points={sc.level_points} level={sc.discounted ? sc.level_before_discount : sc.level} />
      {/if}
      {#if rep.result.discount_applied}
        <p class="flag">Level discounted by one: {rep.result.discount_reason} ({rep.result.discount_clause}).</p>
      {/if}

      <h2>Scorecard</h2>
      <table class="t">
        <thead><tr><th>Element</th><th class="barc"></th><th class="r">Points</th><th class="r">Max</th><th class="r">Gap</th></tr></thead>
        <tbody>
          {#each rep.result.elements as e (e.name)}
            <tr>
              <td>{e.name}{#if e.submin_failed}<span class="star" title="Sub-minimum missed"> *</span>{/if}</td>
              <td class="barc"><span class="bar"><i class:low={e.submin_failed} style:width="{e.max ? Math.round((e.points / e.max) * 100) : 0}%"></i></span></td>
              <td class="r b">{g(Math.round(e.points * 10) / 10)}</td>
              <td class="r">{g(e.max)}</td>
              <td class="r">{g(Math.round(e.gap * 10) / 10)}</td>
            </tr>
          {/each}
        </tbody>
      </table>
      {#if rep.result.elements.some((e) => e.submin_failed)}<p class="fn">* Sub-minimum missed.</p>{/if}

      {#if rep.result.gaps.length}
        <h2>Top actions</h2>
        <ol class="actions">
          {#each rep.result.gaps.slice(0, 3) as gp (gp.name)}
            <li><strong>{gp.name}</strong> <span class="plus">+{g(Math.round(gp.points * 10) / 10)} pts</span><p>{gp.tip}</p></li>
          {/each}
        </ol>
      {/if}

      <section class="detail">
        <h2>Element detail</h2>
        {#each rep.result.elements as e (e.name)}
          <div class="el">
            <h3>{e.name} <span class="pts">{g(Math.round(e.points * 10) / 10)} of {g(e.max)}</span></h3>
            <p>{e.explainer}</p>
            <p class="fn">Main targets: {e.target_text}. Clauses: {e.clause}.</p>
            {#if e.gender_rows}
              <table class="t small">
                <thead><tr><th>Black women / Black female line</th><th class="r">Achieved</th><th class="r">Max</th><th class="r">Open</th></tr></thead>
                <tbody>{#each e.gender_rows as gr (gr.clause)}<tr><td>{gr.name} <span class="fn">cl. {gr.clause}</span></td><td class="r">{g(Math.round(gr.achieved * 10) / 10)}</td><td class="r">{g(gr.max)}</td><td class="r">{g(Math.round(gr.open * 10) / 10)}</td></tr>{/each}</tbody>
              </table>
            {/if}
          </div>
        {/each}
      </section>

      {#if rep.notes.length}
        <section class="notes">
          <h2>Interpretation notes</h2>
          <p class="fn">How this calculator reads points the codes leave open. Your verification agency may read them differently.</p>
          {#each rep.notes as n, i (i)}<p class="note"><strong>{n.title}.</strong> {n.body}</p>{/each}
        </section>
      {/if}

      <section class="method">
        <h2>Method, assumptions and disclaimer</h2>
        <p>{rep.method_text}</p>
        <ul>{#each rep.assumptions as a, i (i)}<li>{a}</li>{/each}</ul>
        <p class="fn">
          This report is a planning aid prepared with Klim ({rep.ruleset.id}). It is not a B-BBEE
          verification certificate. Confirm with a SANAS-accredited verification agency and the
          applicable sector code.
        </p>
      </section>
    </article>
  {/if}
</div>

<style>
  .screen-bar {
    position: sticky;
    top: 0;
    z-index: 5;
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 0.75rem 1.25rem;
    background: var(--surface);
    border-bottom: 1px solid var(--line);
  }
  .back {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    font-weight: 600;
    font-size: var(--t-sm);
    text-decoration: none;
  }
  .hint {
    margin-left: auto;
    font-size: var(--t-sm);
    color: var(--ink-3);
  }
  .page-wrap {
    padding: 2rem 1rem 4rem;
  }
  .paper {
    width: 210mm;
    max-width: 100%;
    min-height: 297mm;
    margin: 0 auto;
    padding: 16mm 16mm 18mm;
    background: #fff;
    box-shadow: var(--shadow-pop);
    border-radius: 4px;
    color: var(--ink);
    font-size: 10.5pt;
    line-height: 1.45;
  }
  .loading {
    min-height: 120mm;
  }
  .rh {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding-bottom: 4mm;
    border-bottom: 1px solid var(--line);
    font-size: 9pt;
    color: var(--ink-3);
  }
  .brand {
    display: inline-flex;
    align-items: center;
    gap: 2mm;
    font-weight: 700;
    color: var(--ink);
  }
  .title {
    padding: 7mm 0 4mm;
  }
  h1 {
    font-size: 22pt;
    letter-spacing: -0.02em;
  }
  .lab {
    margin-top: 1.5mm;
    color: var(--ink-2);
  }
  .flag {
    margin-top: 2mm;
    padding: 2mm 3mm;
    border-radius: 4px;
    background: var(--warning-tint);
    color: #713f12;
    font-size: 9pt;
  }
  .headline {
    display: grid;
    grid-template-columns: 1.4fr 1fr 1fr 1fr;
    border: 1px solid var(--line);
    border-radius: 6px;
  }
  .headline > div {
    display: grid;
    align-content: start;
    gap: 1mm;
    padding: 4mm 4.5mm;
    border-left: 1px solid var(--line);
  }
  .headline > div:first-child {
    border-left: 0;
  }
  .k {
    font-size: 8pt;
    font-weight: 650;
    color: var(--ink-3);
  }
  .lv {
    font-size: 22pt;
    font-weight: 750;
    line-height: 1.05;
    letter-spacing: -0.02em;
    color: var(--primary-active);
  }
  .lv.nc {
    font-size: 16pt;
    color: var(--ink);
  }
  .s {
    font-size: 8.5pt;
    color: var(--ink-2);
  }
  .n {
    font-size: 13pt;
    font-weight: 700;
  }
  .n small {
    font-size: 8.5pt;
    font-weight: 550;
    color: var(--ink-3);
  }
  h2 {
    font-size: 12.5pt;
    margin: 7mm 0 2.5mm;
  }
  h3 {
    font-size: 10.5pt;
    display: flex;
    justify-content: space-between;
    gap: 4mm;
  }
  .pts {
    font-weight: 600;
    color: var(--ink-3);
  }
  .t {
    width: 100%;
    border-collapse: collapse;
  }
  .t th {
    text-align: left;
    font-size: 8pt;
    font-weight: 650;
    color: var(--ink-3);
    padding: 1.5mm 2mm;
    border-bottom: 1px solid var(--line-strong);
  }
  .t td {
    padding: 1.8mm 2mm;
    border-bottom: 1px solid var(--line);
  }
  .t.small td,
  .t.small th {
    font-size: 8.5pt;
  }
  .r {
    text-align: right;
  }
  .b {
    font-weight: 700;
  }
  .barc {
    width: 34%;
  }
  .bar {
    display: block;
    height: 2.5mm;
    background: var(--rail);
    border-radius: 2mm;
    overflow: hidden;
    print-color-adjust: exact;
    -webkit-print-color-adjust: exact;
  }
  .bar i {
    display: block;
    height: 100%;
    background: var(--primary);
  }
  .bar i.low {
    background: var(--warning);
    print-color-adjust: exact;
    -webkit-print-color-adjust: exact;
  }
  .star {
    color: var(--warning);
    font-weight: 700;
  }
  .actions {
    margin: 0;
    padding-left: 5mm;
    display: grid;
    gap: 2.5mm;
  }
  .actions p {
    color: var(--ink-2);
    font-size: 9.5pt;
  }
  .plus {
    color: var(--primary);
    font-weight: 700;
    margin-left: 1.5mm;
  }
  .detail {
    break-before: page;
  }
  .el {
    padding: 3mm 0;
    border-bottom: 1px solid var(--line);
    break-inside: avoid;
  }
  .el p {
    margin-top: 1mm;
    color: var(--ink-2);
    font-size: 9.5pt;
  }
  .fn {
    font-size: 8pt;
    color: var(--ink-3);
  }
  .note {
    margin-top: 2mm;
    font-size: 9.5pt;
    color: var(--ink-2);
    break-inside: avoid;
  }
  .method ul {
    padding-left: 5mm;
    color: var(--ink-2);
    font-size: 9.5pt;
  }
  .method p {
    font-size: 9.5pt;
    color: var(--ink-2);
    margin-bottom: 2mm;
  }
  .paper :global(.ladder) {
    margin-top: 2mm;
  }
  @media (max-width: 820px) {
    .paper {
      padding: 6mm 5mm;
      min-height: 0;
    }
    .headline {
      grid-template-columns: 1fr 1fr;
    }
    .hint {
      display: none;
    }
  }
  @media print {
    @page {
      size: A4;
      margin: 14mm 14mm 16mm;
    }
    :global(body) {
      background: #fff;
    }
    .screen-bar {
      display: none;
    }
    .page-wrap {
      padding: 0;
    }
    .paper {
      width: auto;
      min-height: 0;
      padding: 0;
      box-shadow: none;
      border-radius: 0;
    }
  }
</style>
