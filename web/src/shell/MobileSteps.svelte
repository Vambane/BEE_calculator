<script>
  import { ChevronDown, Check } from "@lucide/svelte";
  import { app, steps, goTo, consented } from "../lib/state.svelte.js";

  let open = $state(false);
  const list = $derived(steps());
  const pct = $derived(((app.step + 1) / list.length) * 100);
</script>

<div class="mobile">
  <details bind:open>
    <summary>
      <span class="count">Step {app.step + 1} of {list.length}</span>
      <span class="name">{list[app.step]?.name}</span>
      <ChevronDown size={18} aria-hidden="true" />
    </summary>
    <ol>
      {#each list as s, i (s.key)}
        <li>
          <button
            disabled={!(consented() && i <= app.maxStep)}
            class:current={i === app.step}
            onclick={() => {
              goTo(i);
              open = false;
            }}
          >
            <span class="n">{#if i < app.maxStep && i !== app.step && consented()}<Check size={13} strokeWidth={3} />{:else}{i + 1}{/if}</span>
            {s.name}
          </button>
        </li>
      {/each}
    </ol>
  </details>
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
  details {
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: var(--radius);
  }
  summary {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.7rem 0.85rem;
    list-style: none;
    cursor: pointer;
  }
  summary::-webkit-details-marker {
    display: none;
  }
  .count {
    font-size: var(--t-xs);
    font-weight: 650;
    color: var(--primary);
    white-space: nowrap;
  }
  .name {
    flex: 1;
    font-weight: 650;
    min-width: 0;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }
  ol {
    list-style: none;
    margin: 0;
    padding: 0.35rem;
    border-top: 1px solid var(--line);
  }
  button {
    width: 100%;
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.55rem 0.5rem;
    border: 0;
    background: none;
    border-radius: var(--radius-sm);
    font-size: var(--t-sm);
    text-align: left;
    cursor: pointer;
  }
  button:disabled {
    color: #7d8894;
    cursor: default;
  }
  .current {
    background: var(--primary-tint);
    font-weight: 650;
  }
  .n {
    display: grid;
    place-items: center;
    width: 22px;
    height: 22px;
    border-radius: 999px;
    border: 1.5px solid var(--line-strong);
    font-size: 0.72rem;
    font-weight: 700;
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
    background: var(--primary);
    transition: width 250ms var(--ease);
  }
</style>
