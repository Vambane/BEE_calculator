<script>
  import { FileText, Download, CircleCheck, TriangleAlert, ArrowUpRight } from "@lucide/svelte";
  import StepFrame from "./StepFrame.svelte";
  import Card from "../ui/Card.svelte";
  import Button from "../ui/Button.svelte";
  import Notice from "../ui/Notice.svelte";
  import Tabs from "../ui/Tabs.svelte";
  import Disclosure from "../ui/Disclosure.svelte";
  import LevelLadder from "../results/LevelLadder.svelte";
  import TfPlanner from "../results/TfPlanner.svelte";
  import { app, goTo, saveClientFile } from "../lib/state.svelte.js";
  import { engine } from "../lib/engine.js";
  import { g } from "../lib/format.js";

  let r = $state(null);
  let error = $state(null);
  let tab = $state("scorecard");

  $effect(() => {
    const snapshot = JSON.parse(JSON.stringify(app.session));
    engine("score", snapshot).then(
      (out) => {
        r = out;
        error = null;
      },
      () => (error = "We could not calculate this scorecard. Check your inputs and try again."),
    );
  });

  const gains = $derived(r?.ok ? [...r.elements].filter((e) => e.gap > 0).sort((a, b) => b.gap - a.gap) : []);
  const failedSubmins = $derived(r?.ok ? r.submins.filter((c) => !c.passed).length : 0);
  const tabs = $derived([
    { id: "scorecard", label: "Scorecard" },
    { id: "gain", label: "Where to gain points", count: gains.length || undefined },
    { id: "submins", label: "Sub-minimums", count: r?.submins?.length ? (failedSubmins ? `${failedSubmins} missed` : "all met") : undefined },
    ...(r?.tf_available ? [{ id: "tf", label: "TF vs ED/SD (draft)" }] : []),
    { id: "notes", label: "Interpretation notes", count: r?.notes?.length || undefined },
  ]);
  const scale = $derived(r?.ok ? Math.max(...r.elements.map((e) => e.max), 1) : 1);
</script>

<StepFrame title="Results" intro="A planning estimate from the figures entered. Confirm with your verification agency and sector code." wide>
  {#snippet aside()}
    {#if r?.ok && !r.deemed}
      <div class="actions">
        <Button icon={Download} onclick={saveClientFile}>Save client file</Button>
        <Button variant="primary" icon={FileText} onclick={() => (location.hash = "#/report")}>Gap report</Button>
      </div>
    {/if}
  {/snippet}

  {#if error}
    <Notice tone="danger" title={error} />
  {:else if !r}
    <div class="sk" aria-busy="true"></div>
  {:else if !r.ok}
    <Notice tone="danger" title="Some inputs need fixing" lines={r.problems} />
    <div><Button onclick={() => goTo(0)}>Go to profile</Button></div>
  {:else}
    <Card pad={false}>
      <div class="summary">
        <div class="level">
          <span class="k">Recognition level</span>
          <span class="v" class:nc={r.level === 9}>{r.level_label}</span>
          <span class="sub">{r.recognition_pct}% procurement recognition</span>
        </div>
        <div class="stat">
          <span class="k">Total points</span>
          <span class="v2">{#if r.deemed}Deemed{:else}{g(Math.round(r.total * 10) / 10)}{#if r.out_of}<small>&nbsp;of {g(r.out_of)}</small>{/if}{/if}</span>
        </div>
        <div class="stat">
          <span class="k">{r.next_gap ? `To Level ${r.next_gap.level}` : "Next level"}</span>
          <span class="v2">{#if r.next_gap}{g(Math.round(r.next_gap.points * 10) / 10)}<small>&nbsp;pts</small>{:else}–{/if}</span>
        </div>
        {#if r.gender}
          <div class="stat">
            <span class="k">Black women / Black female</span>
            <span class="v2">{g(r.gender.achieved)}<small>&nbsp;of {g(r.gender.max)} pts</small></span>
          </div>
        {/if}
      </div>
      {#if !r.deemed && r.level_points !== null}
        <div class="ladder-wrap">
          <LevelLadder levels={app.meta.levels} points={r.level_points} level={r.discounted ? r.level_before_discount : r.level} discounted={false} />
          {#if Math.abs(r.level_points - r.total) > 1e-9}
            <p class="fine">Points used for the level table after normalisation: {g(Math.round(r.level_points * 10) / 10)}.</p>
          {/if}
        </div>
      {/if}
    </Card>

    {#if r.empty}
      <Notice tone="info" title="No points entered yet">Enter indicators or points on the earlier steps to see the level and any sub-minimum effects.</Notice>
    {:else if r.discounted}
      <Notice tone="warning" title="Sub-minimum missed: discounted by one level">
        {#if r.level_before_discount < 9}
          On points alone this scorecard would be Level {r.level_before_discount}. See the Sub-minimums tab for what is short.
        {:else}
          The points are below Level 8, so the discount changes nothing yet. Once the points reach a level, the result will sit one level lower until the sub-minimums are met. See the Sub-minimums tab.
        {/if}
      </Notice>
    {/if}
    {#if r.yes_applied}
      <Notice tone="success" title="YES Initiative recognition applied" />
    {:else if r.yes_blocked_reason}
      <Notice tone="info" title="YES not applied">{r.yes_blocked_reason}</Notice>
    {/if}
    {#each r.warnings as w, i (i)}<Notice tone="warning">{w}</Notice>{/each}

    {#if r.deemed}
      <Notice tone="info" title="Deemed level (affidavit route)">
        This level comes from black ownership. Tick “Score on the full scorecard” in the profile for a
        points breakdown and the gap report.
      </Notice>
      {#if r.notes.length}
        <Card title="Interpretation notes">
          <ul class="notes">{#each r.notes as n, i (i)}<li>{n}</li>{/each}</ul>
        </Card>
      {/if}
    {:else}
      <Card pad={true}>
        <Tabs {tabs} bind:active={tab} label="Results sections">
          {#snippet panel(active)}
            {#if active === "scorecard"}
              <table class="data els">
                <thead>
                  <tr><th>Element</th><th class="bar-col"><span class="visually-hidden">Chart</span></th><th class="r">Points</th><th class="r">Max</th><th class="r">Gap</th></tr>
                </thead>
                <tbody>
                  {#each r.elements as e (e.key)}
                    <tr>
                      <td>
                        <button class="el-link" onclick={() => goTo(app.ctx.steps.findIndex((s) => s.key === e.key))}>{e.name}</button>
                        {#if e.submin_failed}<span class="flag" title="Sub-minimum missed"><TriangleAlert size={14} /> sub-minimum</span>{/if}
                      </td>
                      <td class="bar-col">
                        <div class="bar" style:width="{(e.max / scale) * 100}%" aria-hidden="true">
                          <span style:width="{e.max ? (e.points / e.max) * 100 : 0}%" class:low={e.submin_failed}></span>
                        </div>
                      </td>
                      <td class="r strong">{g(Math.round(e.points * 10) / 10)}</td>
                      <td class="r">{g(e.max)}</td>
                      <td class="r muted">{e.gap > 0 ? g(Math.round(e.gap * 10) / 10) : "–"}</td>
                    </tr>
                  {/each}
                </tbody>
                <tfoot>
                  <tr><th>Total</th><td></td><td class="r strong">{g(Math.round(r.total * 10) / 10)}</td><td class="r">{r.out_of ? g(r.out_of) : ""}</td><td></td></tr>
                </tfoot>
              </table>
              {#if r.groups.length}
                <Disclosure title="Points by group" summary="How each element's points split across its groups">
                  <table class="data">
                    <thead><tr><th>Element</th><th>Group</th><th class="r">Points</th></tr></thead>
                    <tbody>{#each r.groups as gr, i (i)}<tr><td>{gr.element}</td><td>{gr.group}</td><td class="r">{g(Math.round(gr.points * 100) / 100)}</td></tr>{/each}</tbody>
                  </table>
                </Disclosure>
              {/if}
            {:else if active === "gain"}
              {#if !gains.length}
                <p class="empty">No open points: every element is at its maximum.</p>
              {:else}
                <ol class="gains">
                  {#each gains as e (e.key)}
                    <li>
                      <div class="gain-head">
                        <button class="el-link big" onclick={() => goTo(app.ctx.steps.findIndex((s) => s.key === e.key))}>{e.name}<ArrowUpRight size={15} aria-hidden="true" /></button>
                        <span class="plus">+{g(Math.round(e.gap * 10) / 10)} pts available</span>
                      </div>
                      {#if e.tips.length}
                        <ul class="tips">
                          {#each e.tips as t (t.clause)}<li>{t.name}: target {t.target} ({g(t.points)} pts, cl. {t.clause})</li>{/each}
                        </ul>
                      {/if}
                    </li>
                  {/each}
                </ol>
                {#if r.gender_gaps.some((x) => x.open > 0)}
                  <h3 class="sub-h">Black women / Black female lines</h3>
                  <p class="fine">Scored separately from the Black people indicators.</p>
                  <table class="data">
                    <thead><tr><th>Indicator</th><th class="r">Achieved</th><th class="r">Open</th><th class="r">Target</th></tr></thead>
                    <tbody>
                      {#each r.gender_gaps.filter((x) => x.open > 0) as x (x.clause)}
                        <tr><td>{x.element_name} · {x.name} <span class="muted">cl. {x.clause}</span></td><td class="r">{g(x.achieved)} of {g(x.max)}</td><td class="r strong">+{g(x.open)}</td><td class="r">{g(x.target)}%</td></tr>
                      {/each}
                    </tbody>
                  </table>
                {/if}
              {/if}
            {:else if active === "submins"}
              {#if !r.submins.length}
                <p class="empty">No sub-minimums apply to this scorecard.</p>
              {:else}
                <ul class="submins">
                  {#each r.submins as c, i (i)}
                    <li class:fail={!c.passed}>
                      {#if c.passed}<CircleCheck size={18} aria-hidden="true" />{:else}<TriangleAlert size={18} aria-hidden="true" />{/if}
                      <span><strong>{c.element}{c.group ? ` · ${c.group}` : ""}</strong>: {g(Math.round(c.achieved * 10) / 10)} of {g(c.required)} required <span class="muted">({c.clause})</span></span>
                      <span class="status">{c.passed ? "Met" : "Missed"}</span>
                    </li>
                  {/each}
                </ul>
              {/if}
            {:else if active === "tf"}
              <TfPlanner baseTotal={r.total} />
            {:else if active === "notes"}
              <p class="fine">How this calculator reads points the codes leave open. Your verification agency may read them differently.</p>
              <ul class="notes">{#each r.notes as n, i (i)}<li>{n}</li>{/each}</ul>
            {/if}
          {/snippet}
        </Tabs>
      </Card>
    {/if}
  {/if}
</StepFrame>

<style>
  .actions {
    display: flex;
    gap: 0.5rem;
  }
  .sk {
    height: 220px;
    border-radius: var(--radius);
    background: var(--surface);
    border: 1px solid var(--line);
  }
  .summary {
    display: grid;
    grid-template-columns: 1.4fr repeat(3, 1fr);
    border-bottom: 1px solid var(--line);
  }
  .summary > div {
    display: grid;
    align-content: start;
    gap: 0.2rem;
    padding: 1.15rem 1.25rem;
    border-left: 1px solid var(--line);
  }
  .summary > div:first-child {
    border-left: 0;
  }
  .k {
    font-size: var(--t-xs);
    font-weight: 650;
    color: var(--ink-3);
  }
  .v {
    font-size: var(--t-3xl);
    font-weight: 750;
    line-height: 1.05;
    letter-spacing: -0.03em;
    color: var(--primary-active);
  }
  .v.nc {
    color: var(--danger);
    font-size: var(--t-2xl);
  }
  .sub {
    font-size: var(--t-sm);
    color: var(--ink-2);
  }
  .v2 {
    font-size: var(--t-2xl);
    font-weight: 700;
    letter-spacing: -0.02em;
    line-height: 1.15;
  }
  .v2 small {
    font-size: var(--t-sm);
    font-weight: 550;
    color: var(--ink-3);
    letter-spacing: 0;
  }
  .ladder-wrap {
    padding: 0.5rem 1.25rem 1rem;
  }
  .fine {
    font-size: var(--t-xs);
    color: var(--ink-3);
  }
  .els .bar-col {
    width: 34%;
  }
  .bar {
    height: 10px;
    border-radius: 5px;
    background: var(--rail);
    overflow: hidden;
  }
  .bar span {
    display: block;
    height: 100%;
    background: var(--primary);
    border-radius: 5px;
    transition: width 400ms var(--ease);
  }
  .bar span.low {
    background: var(--warning);
  }
  .el-link {
    padding: 0;
    border: 0;
    background: none;
    font: inherit;
    font-weight: 600;
    color: var(--ink);
    cursor: pointer;
    text-align: left;
    text-decoration: underline;
    text-decoration-color: transparent;
    text-underline-offset: 0.18em;
    transition: text-decoration-color 150ms var(--ease);
  }
  .el-link:hover {
    text-decoration-color: currentColor;
    color: var(--primary);
  }
  .el-link:focus-visible {
    outline: none;
    box-shadow: var(--focus);
    border-radius: 3px;
  }
  .el-link.big {
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    font-size: var(--t-md);
  }
  .flag {
    display: inline-flex;
    align-items: center;
    gap: 0.2rem;
    margin-left: 0.5rem;
    font-size: var(--t-xs);
    font-weight: 650;
    color: var(--warning);
  }
  .strong {
    font-weight: 700;
  }
  .muted {
    color: var(--ink-3);
  }
  .gains {
    list-style: none;
    margin: 0;
    padding: 0;
    display: grid;
  }
  .gains > li {
    padding: 0.85rem 0;
    border-bottom: 1px solid var(--line);
  }
  .gains > li:first-child {
    padding-top: 0;
  }
  .gain-head {
    display: flex;
    justify-content: space-between;
    align-items: baseline;
    gap: 1rem;
  }
  .plus {
    font-weight: 700;
    color: var(--primary);
    white-space: nowrap;
  }
  .tips {
    margin: 0.35rem 0 0;
    padding-left: 1.1rem;
    font-size: var(--t-sm);
    color: var(--ink-2);
  }
  .sub-h {
    margin-top: 1.5rem;
    font-size: var(--t-md);
  }
  .submins {
    list-style: none;
    margin: 0;
    padding: 0;
    display: grid;
    gap: 0.5rem;
  }
  .submins li {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.65rem 0.8rem;
    border-radius: var(--radius);
    background: var(--success-tint);
    color: #0b4f30;
    font-size: var(--t-sm);
  }
  .submins li.fail {
    background: var(--warning-tint);
    color: #6b4100;
  }
  .submins li > :global(svg) {
    flex: none;
  }
  .status {
    margin-left: auto;
    font-weight: 700;
  }
  .notes {
    margin: 0.5rem 0 0;
    padding-left: 1.1rem;
    display: grid;
    gap: 0.4rem;
    font-size: var(--t-sm);
    color: var(--ink-2);
    max-width: 80ch;
  }
  .empty {
    color: var(--ink-3);
    font-size: var(--t-sm);
  }
  @media (max-width: 900px) {
    .summary {
      grid-template-columns: 1fr 1fr;
    }
    .summary > div:nth-child(3) {
      border-left: 0;
    }
    .summary > div:nth-child(n + 3) {
      border-top: 1px solid var(--line);
    }
    .els .bar-col {
      display: none;
    }
  }
  @media (max-width: 640px) {
    .actions {
      width: 100%;
    }
  }
</style>
