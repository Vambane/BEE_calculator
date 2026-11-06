<script>
  /** The step's main surface. Header (title + optional actions), body, optional footer. */
  let { title = "", description = "", children, footer, actions, pad = true } = $props();
</script>

<section class="card">
  {#if title || actions}
    <header>
      <div>
        {#if title}<h2>{title}</h2>{/if}
        {#if description}<p>{description}</p>{/if}
      </div>
      {#if actions}<div class="actions">{@render actions()}</div>{/if}
    </header>
  {/if}
  <div class="body" class:pad>{@render children()}</div>
  {#if footer}<footer>{@render footer()}</footer>{/if}
</section>

<style>
  .card {
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: calc(var(--radius) + 2px);
    box-shadow: var(--shadow-1);
  }
  header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 1rem;
    padding: 1.1rem 1.25rem 0;
  }
  h2 {
    font-size: var(--t-lg);
  }
  header p {
    margin-top: 0.2rem;
    color: var(--ink-3);
    font-size: var(--t-sm);
    max-width: 62ch;
  }
  .actions {
    flex: none;
    display: flex;
    gap: 0.5rem;
  }
  .body {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    gap: 1.15rem;
  }
  .pad {
    padding: 1.1rem 1.25rem 1.25rem;
  }
  footer {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 0.75rem;
    padding: 0.9rem 1.25rem;
    border-top: 1px solid var(--line);
    background: var(--surface-2);
    border-radius: 0 0 calc(var(--radius) + 2px) calc(var(--radius) + 2px);
  }
</style>
