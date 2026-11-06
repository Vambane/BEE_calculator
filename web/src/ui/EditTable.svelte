<script>
  import { Plus, Trash2, ChevronLeft, ChevronRight } from "@lucide/svelte";
  import { groupThousands, parseNumber } from "../lib/format.js";

  /**
   * Editable table for list calculators.
   * columns: [{ key, label, type: 'text'|'number'|'select'|'bool', options?, width?, help? }]
   * rows: array of plain objects keyed by column label (the engine's label-keyed records).
   */
  let { columns, rows = $bindable([]), onchange, caption, pageSize = 25, emptyText = "No rows yet." } = $props();

  let page = $state(0);
  const pages = $derived(Math.max(1, Math.ceil(rows.length / pageSize)));
  const start = $derived(page * pageSize);
  const visible = $derived(rows.slice(start, start + pageSize));

  $effect(() => {
    if (page > pages - 1) page = pages - 1;
  });

  function blank() {
    const r = {};
    for (const c of columns) r[c.label] = c.type === "bool" ? false : c.type === "number" ? null : c.default ?? "";
    return r;
  }
  function addRow() {
    rows = [...rows, blank()];
    page = Math.max(0, Math.ceil(rows.length / pageSize) - 1);
    onchange?.();
  }
  function removeRow(i) {
    rows = rows.filter((_, j) => j !== i);
    onchange?.();
  }
  function set(i, col, v) {
    rows[i] = { ...rows[i], [col.label]: v };
    onchange?.();
  }
  function shown(v, col) {
    if (v === null || v === undefined || v === "") return "";
    return col.decimals !== undefined ? groupThousands(Number(v), col.decimals) : String(v);
  }
</script>

<div class="tbl">
  <p class="hint">Swipe the table sideways to see every column.</p>
  <div class="scroll">
    <table>
      {#if caption}<caption class="visually-hidden">{caption}</caption>{/if}
      <thead>
        <tr>
          <th class="num-col" scope="col"><span class="visually-hidden">Row</span>#</th>
          {#each columns as c (c.key)}
            <th scope="col" style:min-width={c.width} title={c.help} class:right={c.type === "number"} class:center={c.type === "bool"}>{c.label}</th>
          {/each}
          <th scope="col"><span class="visually-hidden">Remove</span></th>
        </tr>
      </thead>
      <tbody>
        {#each visible as r, k (start + k)}
          {@const i = start + k}
          <tr>
            <td class="num-col">{i + 1}</td>
            {#each columns as c (c.key)}
              <td class:center={c.type === "bool"}>
                {#if c.type === "bool"}
                  <input
                    type="checkbox"
                    class="cb"
                    aria-label="{c.label}, row {i + 1}"
                    checked={r[c.label] === true}
                    onchange={(e) => set(i, c, e.currentTarget.checked)}
                  />
                {:else if c.type === "select"}
                  <select aria-label="{c.label}, row {i + 1}" value={r[c.label] ?? ""} onchange={(e) => set(i, c, e.currentTarget.value)}>
                    {#if !c.required}<option value=""></option>{/if}
                    {#each c.options as o (o)}<option value={o}>{o}</option>{/each}
                  </select>
                {:else if c.type === "number"}
                  <input
                    type="text"
                    inputmode="decimal"
                    class="right"
                    aria-label="{c.label}, row {i + 1}"
                    value={shown(r[c.label], c)}
                    onchange={(e) => set(i, c, parseNumber(e.currentTarget.value))}
                  />
                {:else}
                  <input type="text" aria-label="{c.label}, row {i + 1}" value={r[c.label] ?? ""} onchange={(e) => set(i, c, e.currentTarget.value)} />
                {/if}
              </td>
            {/each}
            <td class="del">
              <button aria-label="Remove row {i + 1}" title="Remove row" onclick={() => removeRow(i)}><Trash2 size={15} /></button>
            </td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
  {#if !rows.length}<p class="empty">{emptyText}</p>{/if}
  <div class="bar">
    <button class="add" onclick={addRow}><Plus size={16} aria-hidden="true" />Add row</button>
    {#if pages > 1}
      <div class="pager">
        <button aria-label="Previous page" disabled={page === 0} onclick={() => (page -= 1)}><ChevronLeft size={16} /></button>
        <span>Rows {start + 1} to {Math.min(start + pageSize, rows.length)} of {rows.length}</span>
        <button aria-label="Next page" disabled={page >= pages - 1} onclick={() => (page += 1)}><ChevronRight size={16} /></button>
      </div>
    {:else if rows.length}
      <span class="count">{rows.length} {rows.length === 1 ? "row" : "rows"}</span>
    {/if}
  </div>
</div>

<style>
  .tbl {
    border: 1px solid var(--line);
    border-radius: var(--radius);
    background: var(--surface);
    overflow: hidden;
  }
  /* Edge shadows show when the table scrolls sideways (they scroll away at each end). */
  .hint {
    display: none;
    margin: 0;
    padding: 0.5rem 0.75rem;
    font-size: var(--t-xs);
    color: var(--ink-3);
    border-bottom: 1px solid var(--line);
  }
  @media (max-width: 640px) {
    .hint {
      display: block;
    }
  }
  .scroll {
    overflow-x: auto;
    background:
      linear-gradient(to right, var(--surface) 30%, rgb(255 255 255 / 0)) left / 2.5rem 100% no-repeat local,
      linear-gradient(to left, var(--surface) 30%, rgb(255 255 255 / 0)) right / 2.5rem 100% no-repeat local,
      radial-gradient(farthest-side at 0 50%, rgb(16 24 40 / 0.14), transparent) left / 0.75rem 100% no-repeat scroll,
      radial-gradient(farthest-side at 100% 50%, rgb(16 24 40 / 0.14), transparent) right / 0.75rem 100% no-repeat scroll;
  }
  table {
    width: 100%;
    border-collapse: collapse;
    font-size: var(--t-sm);
  }
  th {
    position: sticky;
    top: 0;
    text-align: left;
    font-size: var(--t-xs);
    font-weight: 650;
    color: var(--ink-2);
    background: var(--surface-2);
    padding: 0.5rem 0.5rem;
    border-bottom: 1px solid var(--line);
    white-space: nowrap;
  }
  td {
    padding: 0.2rem 0.3rem;
    border-bottom: 1px solid var(--line);
    vertical-align: middle;
  }
  tbody tr:last-child td {
    border-bottom: 0;
  }
  tbody tr:hover td {
    background: #fafbfc;
  }
  .right {
    text-align: right;
  }
  .center {
    text-align: center;
  }
  .num-col {
    width: 2.5rem;
    color: var(--ink-3);
    font-size: var(--t-xs);
    text-align: right;
    padding-right: 0.6rem;
  }
  td input[type="text"],
  td select {
    width: 100%;
    height: 32px;
    padding: 0 0.45rem;
    border: 1px solid transparent;
    border-radius: var(--radius-sm);
    background: transparent;
    font-size: var(--t-sm);
  }
  td input[type="text"]:hover,
  td select:hover {
    border-color: var(--line-strong);
    background: var(--surface);
  }
  td input[type="text"]:focus,
  td select:focus {
    outline: none;
    border-color: var(--primary);
    box-shadow: var(--focus);
    background: var(--surface);
  }
  .cb {
    width: 16px;
    height: 16px;
    accent-color: var(--primary);
    cursor: pointer;
  }
  .del {
    width: 2.5rem;
    text-align: center;
  }
  .del button,
  .pager button {
    display: inline-grid;
    place-items: center;
    width: 30px;
    height: 30px;
    border: 0;
    border-radius: var(--radius-sm);
    background: transparent;
    color: var(--ink-3);
    cursor: pointer;
  }
  .del button:hover {
    background: var(--danger-tint);
    color: var(--danger);
  }
  .pager button:hover:not(:disabled) {
    background: var(--rail);
    color: var(--ink);
  }
  .pager button:disabled {
    opacity: 0.4;
    cursor: default;
  }
  .empty {
    margin: 0;
    padding: 1.25rem 1rem;
    text-align: center;
    border-bottom: 1px solid var(--line);
    color: var(--ink-3);
  }
  .bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    padding: 0.4rem 0.5rem;
    border-top: 1px solid var(--line);
    background: var(--surface-2);
  }
  .add {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    height: 32px;
    padding: 0 0.6rem;
    border: 0;
    border-radius: var(--radius-sm);
    background: transparent;
    color: var(--primary);
    font-weight: 650;
    font-size: var(--t-sm);
    cursor: pointer;
  }
  .add:hover {
    background: var(--primary-tint);
  }
  .add:focus-visible,
  .del button:focus-visible,
  .pager button:focus-visible {
    outline: none;
    box-shadow: var(--focus);
  }
  .pager {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    font-size: var(--t-xs);
    color: var(--ink-3);
  }
  .count {
    font-size: var(--t-xs);
    color: var(--ink-3);
  }
</style>
