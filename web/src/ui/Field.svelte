<script>
  /** Label + control + help/error. The control is passed as children and must use `id`. */
  let { id, label, help = "", error = "", optional = false, children, aside } = $props();
</script>

<div class="field" class:has-error={!!error}>
  <div class="label-row">
    <label for={id}>{label}{#if optional}<span class="opt">(optional)</span>{/if}</label>
    {#if aside}<span class="aside">{@render aside()}</span>{/if}
  </div>
  {@render children()}
  {#if error}
    <p class="error" id="{id}-error">{error}</p>
  {:else if help}
    <p class="help" id="{id}-help">{help}</p>
  {/if}
</div>

<style>
  .field {
    display: grid;
    gap: 0.35rem;
    min-width: 0;
    align-content: start;
  }
  .label-row {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 0.75rem;
  }
  label {
    font-size: var(--t-sm);
    font-weight: 600;
    color: var(--ink);
  }
  .opt {
    margin-left: 0.3em;
    font-weight: 450;
    color: var(--ink-3);
  }
  .aside {
    font-size: var(--t-xs);
    color: var(--ink-3);
    white-space: nowrap;
  }
  .help {
    font-size: var(--t-xs);
    color: var(--ink-3);
  }
  .error {
    font-size: var(--t-xs);
    color: var(--danger);
    font-weight: 550;
  }
</style>
