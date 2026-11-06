<script>
  /** A two-to-four option switch. options: [{value, label}] */
  let { value = $bindable(), options, label, onchange, disabled = false } = $props();
  const name = `seg-${Math.random().toString(36).slice(2, 8)}`;
</script>

<div class="seg" role="radiogroup" aria-label={label}>
  {#each options as o (o.value)}
    <label class:on={value === o.value} class:disabled>
      <input
        type="radio"
        {name}
        value={o.value}
        checked={value === o.value}
        {disabled}
        onchange={() => {
          value = o.value;
          onchange?.(o.value);
        }}
      />
      <span>{o.label}</span>
    </label>
  {/each}
</div>

<style>
  .seg {
    display: inline-flex;
    padding: 3px;
    gap: 2px;
    background: var(--rail);
    border-radius: calc(var(--radius) + 2px);
    border: 1px solid var(--line);
  }
  label {
    position: relative;
    display: inline-flex;
    align-items: center;
    height: 32px;
    padding: 0 0.85rem;
    border-radius: var(--radius-sm);
    font-size: var(--t-sm);
    font-weight: 600;
    color: var(--ink-2);
    cursor: pointer;
    white-space: nowrap;
    transition:
      background-color 160ms var(--ease),
      color 160ms var(--ease),
      box-shadow 160ms var(--ease);
  }
  label:hover:not(.on):not(.disabled) {
    color: var(--ink);
    background: rgb(255 255 255 / 0.6);
  }
  .on {
    background: var(--surface);
    color: var(--ink);
    box-shadow: var(--shadow-1);
  }
  .disabled {
    cursor: not-allowed;
    opacity: 0.6;
  }
  input {
    position: absolute;
    opacity: 0;
    pointer-events: none;
  }
  label:has(input:focus-visible) {
    box-shadow: var(--focus);
  }
</style>
