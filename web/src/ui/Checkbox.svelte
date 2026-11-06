<script>
  import { Check } from "@lucide/svelte";
  let { id, checked = $bindable(false), disabled = false, children, help = "", onchange } = $props();
</script>

<label class="cb" class:disabled for={id}>
  <span class="box">
    <input {id} type="checkbox" bind:checked {disabled} {onchange} />
    <span class="mark" aria-hidden="true"><Check size={13} strokeWidth={3} /></span>
  </span>
  <span class="text">
    <span class="lab">{@render children()}</span>
    {#if help}<span class="help">{help}</span>{/if}
  </span>
</label>

<style>
  .cb {
    display: flex;
    gap: 0.65rem;
    align-items: flex-start;
    cursor: pointer;
    font-size: var(--t-md);
  }
  .disabled {
    cursor: not-allowed;
    color: var(--ink-3);
  }
  .box {
    position: relative;
    flex: none;
    width: 20px;
    height: 20px;
    margin-top: 1px;
  }
  input {
    position: absolute;
    inset: 0;
    margin: 0;
    opacity: 0;
    cursor: inherit;
  }
  .mark {
    position: absolute;
    inset: 0;
    pointer-events: none;
    display: grid;
    place-items: center;
    border: 1.5px solid #a1a1aa;
    border-radius: 5px;
    background: var(--surface);
    color: transparent;
    transition:
      background-color 140ms var(--ease),
      border-color 140ms var(--ease);
  }
  .cb:hover:not(.disabled) .mark {
    border-color: var(--primary);
  }
  input:checked + .mark {
    background: var(--primary);
    border-color: var(--primary);
    color: #fff;
  }
  input:focus-visible + .mark {
    box-shadow: var(--focus);
  }
  input:disabled + .mark {
    background: var(--surface-2);
    border-color: var(--line-strong);
  }
  .text {
    display: grid;
    gap: 0.15rem;
  }
  .help {
    font-size: var(--t-xs);
    color: var(--ink-3);
  }
</style>
