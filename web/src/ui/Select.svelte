<script>
  import { ChevronDown } from "@lucide/svelte";
  /** options: [{value, label}] */
  let { id, value = $bindable(), options, disabled = false, onchange, describedby } = $props();
</script>

<div class="sel" class:disabled>
  <select {id} bind:value {disabled} aria-describedby={describedby} {onchange}>
    {#each options as o (String(o.value))}
      <option value={o.value}>{o.label}</option>
    {/each}
  </select>
  <ChevronDown size={16} aria-hidden="true" />
</div>

<style>
  .sel {
    position: relative;
    display: flex;
    align-items: center;
  }
  select {
    appearance: none;
    width: 100%;
    height: 48px;
    padding: 0 2.5rem 0 1rem;
    background: var(--glass);
    border: 1px solid var(--line);
    border-radius: var(--radius);
    font-size: var(--t-md);
    cursor: pointer;
    transition:
      border-color 150ms var(--ease),
      box-shadow 150ms var(--ease);
  }
  select:hover:not(:disabled) {
    border-color: #a1a1aa;
  }
  select:focus-visible {
    outline: none;
    border-color: rgb(167 139 250 / 0.7);
    background: var(--glass-focus);
    box-shadow: var(--focus);
  }
  select:disabled {
    background: var(--rail);
    border-color: var(--line);
    color: var(--ink-3);
    cursor: not-allowed;
  }
  .sel :global(svg) {
    position: absolute;
    right: 0.75rem;
    pointer-events: none;
    color: var(--ink-3);
  }
</style>
