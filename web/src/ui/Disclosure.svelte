<script>
  import { ChevronRight } from "@lucide/svelte";
  /** A collapsible section built on <details>, for optional calculators and extras. */
  let { title, summary = "", open = $bindable(false), children, badge } = $props();
</script>

<details class="disc" bind:open>
  <summary>
    <ChevronRight size={18} strokeWidth={2.2} aria-hidden="true" />
    <span class="t">
      <span class="title">{title}</span>
      {#if summary}<span class="sum">{summary}</span>{/if}
    </span>
    {#if badge}<span class="badge">{@render badge()}</span>{/if}
  </summary>
  <div class="inner">{@render children()}</div>
</details>

<style>
  .disc {
    border: 1px solid var(--line);
    border-radius: var(--radius);
    background: var(--surface);
  }
  summary {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.8rem 0.95rem;
    cursor: pointer;
    list-style: none;
    border-radius: var(--radius);
    transition: background-color 150ms var(--ease);
  }
  summary::-webkit-details-marker {
    display: none;
  }
  summary:hover {
    background: var(--surface-2);
  }
  summary:focus-visible {
    outline: none;
    box-shadow: var(--focus);
  }
  summary > :global(svg) {
    flex: none;
    color: var(--ink-3);
    transition: transform 200ms var(--ease);
  }
  details[open] > summary > :global(svg) {
    transform: rotate(90deg);
  }
  details[open] > summary {
    border-bottom: 1px solid var(--line);
    border-radius: var(--radius) var(--radius) 0 0;
  }
  .t {
    display: grid;
    gap: 0.1rem;
    flex: 1;
    min-width: 0;
  }
  .title {
    font-weight: 620;
    font-size: var(--t-md);
  }
  .sum {
    font-size: var(--t-xs);
    color: var(--ink-3);
  }
  .badge {
    flex: none;
  }
  .inner {
    padding: 1rem 0.95rem 1.1rem;
    display: grid;
    gap: 1rem;
  }
</style>
