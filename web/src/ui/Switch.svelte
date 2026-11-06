<script>
  let { id, checked = $bindable(false), label, help = "", disabled = false } = $props();
</script>

<label class="sw" for={id} class:disabled>
  <span class="text">
    <span class="lab">{label}</span>
    {#if help}<span class="help">{help}</span>{/if}
  </span>
  <span class="track">
    <input {id} type="checkbox" role="switch" bind:checked {disabled} />
    <span class="thumb" aria-hidden="true"></span>
  </span>
</label>

<style>
  .sw {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 0.75rem;
    cursor: pointer;
  }
  .disabled {
    cursor: not-allowed;
    opacity: 0.6;
  }
  .text {
    display: grid;
    gap: 0.1rem;
  }
  .lab {
    font-size: var(--t-sm);
    font-weight: 600;
    line-height: 1.3;
  }
  .help {
    font-size: var(--t-xs);
    color: var(--ink-3);
    line-height: 1.4;
  }
  .track {
    position: relative;
    flex: none;
    width: 36px;
    height: 20px;
    margin-top: 1px;
    border-radius: 999px;
    background: #b4bec8;
    transition: background-color 180ms var(--ease);
  }
  .track:has(input:checked) {
    background: var(--warning);
  }
  .track:has(input:focus-visible) {
    box-shadow: var(--focus);
  }
  input {
    position: absolute;
    inset: 0;
    margin: 0;
    opacity: 0;
    cursor: inherit;
  }
  .thumb {
    position: absolute;
    top: 2px;
    left: 2px;
    width: 16px;
    height: 16px;
    border-radius: 999px;
    background: #fff;
    box-shadow: 0 1px 2px rgb(16 24 40 / 0.25);
    transition: transform 200ms var(--ease);
    pointer-events: none;
  }
  input:checked + .thumb {
    transform: translateX(16px);
  }
</style>
