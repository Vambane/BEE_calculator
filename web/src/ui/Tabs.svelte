<script>
  /** tabs: [{ id, label }]; `active` is bindable; content via the `panel` snippet. */
  let { tabs, active = $bindable(tabs[0]?.id), panel, label = "Sections" } = $props();
  const base = `tabs-${Math.random().toString(36).slice(2, 7)}`;

  function key(e, i) {
    let j = null;
    if (e.key === "ArrowRight") j = (i + 1) % tabs.length;
    if (e.key === "ArrowLeft") j = (i - 1 + tabs.length) % tabs.length;
    if (j === null) return;
    e.preventDefault();
    active = tabs[j].id;
    document.getElementById(`${base}-${tabs[j].id}`)?.focus();
  }
</script>

<div class="tabs">
  <div class="list" role="tablist" aria-label={label}>
    {#each tabs as t, i (t.id)}
      <button
        id="{base}-{t.id}"
        role="tab"
        aria-selected={active === t.id}
        aria-controls="{base}-panel"
        tabindex={active === t.id ? 0 : -1}
        onclick={() => (active = t.id)}
        onkeydown={(e) => key(e, i)}
      >
        {t.label}
        {#if t.count !== undefined}<span class="count">{t.count}</span>{/if}
      </button>
    {/each}
  </div>
  <div id="{base}-panel" role="tabpanel" aria-labelledby="{base}-{active}" class="panel">
    {@render panel(active)}
  </div>
</div>

<style>
  .tabs {
    min-width: 0;
  }
  .list {
    display: flex;
    gap: 0.25rem;
    border-bottom: 1px solid var(--line);
    overflow-x: auto;
  }
  button {
    position: relative;
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    height: 42px;
    padding: 0 0.85rem;
    border: 0;
    background: none;
    font-size: var(--t-sm);
    font-weight: 600;
    color: var(--ink-3);
    cursor: pointer;
    white-space: nowrap;
    border-radius: var(--radius-sm) var(--radius-sm) 0 0;
  }
  button:hover {
    color: var(--ink);
  }
  button[aria-selected="true"] {
    color: var(--ink);
  }
  button[aria-selected="true"]::after {
    content: "";
    position: absolute;
    left: 0.6rem;
    right: 0.6rem;
    bottom: -1px;
    height: 2px;
    border-radius: 2px;
    background: var(--primary);
  }
  button:focus-visible {
    outline: none;
    box-shadow: var(--focus);
  }
  .count {
    font-size: 0.72rem;
    font-weight: 700;
    padding: 0 0.4rem;
    border-radius: 999px;
    background: var(--rail);
    color: var(--ink-2);
  }
  .panel {
    padding-top: 1.1rem;
    overflow-x: auto;
  }
</style>
