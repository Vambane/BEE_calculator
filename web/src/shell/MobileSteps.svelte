<script>
  import { ChevronDown } from "@lucide/svelte";
  import { app, steps } from "../lib/state.svelte.js";

  let { open = $bindable(false) } = $props();
  const list = $derived(steps());
  const pct = $derived(list.length ? ((app.step + 1) / list.length) * 100 : 0);
</script>

<div class="mobile">
  <button
    id="steps-toggle"
    type="button"
    aria-expanded={open}
    aria-controls="step-rail"
    onclick={() => (open = !open)}
  >
    <span class="count">Step {app.step + 1} of {list.length}</span>
    <span class="name">{list[app.step]?.name}</span>
    <span class="chev" class:flip={open}><ChevronDown size={18} aria-hidden="true" /></span>
  </button>
  <div class="bar" aria-hidden="true"><span style="width:{pct}%"></span></div>
</div>

<style>
  .mobile {
    display: none;
    margin-bottom: 1rem;
  }
  @media (max-width: 900px) {
    .mobile {
      display: block;
    }
  }
  button {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    width: 100%;
    min-height: 44px;
    padding: 0.65rem 0.85rem;
    border: 1px solid var(--line);
    border-radius: var(--radius);
    background: var(--surface);
    text-align: left;
    cursor: pointer;
    box-shadow: var(--shadow-1);
  }
  button:focus-visible {
    outline: none;
    box-shadow: var(--focus);
  }
  .count {
    flex: none;
    font-size: var(--t-xs);
    font-weight: 700;
    color: var(--accent);
    white-space: nowrap;
  }
  .name {
    flex: 1;
    min-width: 0;
    font-weight: 650;
    line-height: 1.3;
  }
  .chev {
    display: grid;
    flex: none;
    color: var(--ink-2);
    transition: transform 150ms var(--ease);
  }
  .chev.flip {
    transform: rotate(180deg);
  }
  .bar {
    height: 3px;
    margin-top: 0.5rem;
    background: var(--line);
    border-radius: 3px;
    overflow: hidden;
  }
  .bar span {
    display: block;
    height: 100%;
    background: var(--accent);
  }
</style>
