<script>
  import { CircleCheck, Info, TriangleAlert, CircleX } from "@lucide/svelte";
  /** tone: info | success | warning | danger */
  let { tone = "info", title = "", lines = [], children, compact = false } = $props();
  const icons = { info: Info, success: CircleCheck, warning: TriangleAlert, danger: CircleX };
  const Icon = $derived(icons[tone]);
</script>

<div class="notice {tone}" class:compact role={tone === "danger" ? "alert" : "status"}>
  <Icon size={18} strokeWidth={2} aria-hidden="true" />
  <div class="body">
    {#if title}<p class="title">{title}</p>{/if}
    {#if children}<div class="content">{@render children()}</div>{/if}
    {#if lines?.length}
      <ul>
        {#each lines as l, i (i)}<li>{l}</li>{/each}
      </ul>
    {/if}
  </div>
</div>

<style>
  .notice {
    display: flex;
    gap: 0.65rem;
    padding: 0.8rem 0.95rem;
    border-radius: var(--radius);
    border: 1px solid;
    font-size: var(--t-sm);
    line-height: 1.5;
  }
  .compact {
    padding: 0.55rem 0.75rem;
  }
  .notice > :global(svg) {
    flex: none;
    margin-top: 1px;
  }
  .body {
    display: grid;
    gap: 0.25rem;
    min-width: 0;
  }
  .title {
    font-weight: 650;
  }
  ul {
    margin: 0;
    padding-left: 1.1rem;
    display: grid;
    gap: 0.15rem;
  }
  .info {
    background: var(--info-tint);
    border-color: var(--info-line);
    color: #163f86;
  }
  .info > :global(svg) {
    color: var(--info);
  }
  .success {
    background: var(--success-tint);
    border-color: #bfe5cf;
    color: #0b4f30;
  }
  .success > :global(svg) {
    color: var(--success);
  }
  .warning {
    background: var(--warning-tint);
    border-color: var(--warning-line);
    color: #6b4100;
  }
  .warning > :global(svg) {
    color: var(--warning);
  }
  .danger {
    background: var(--danger-tint);
    border-color: var(--danger-line);
    color: #8c1c15;
  }
  .danger > :global(svg) {
    color: var(--danger);
  }
</style>
