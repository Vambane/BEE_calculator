<script>
  /** @type {{variant?: 'primary'|'secondary'|'ghost'|'danger', size?: 'md'|'sm', type?: string, disabled?: boolean, loading?: boolean, full?: boolean, onclick?: (e: MouseEvent) => void, children: any, icon?: any, title?: string, ariaLabel?: string}} */
  let {
    variant = "secondary",
    size = "md",
    type = "button",
    disabled = false,
    loading = false,
    full = false,
    onclick,
    children,
    icon: Icon,
    title,
    ariaLabel,
  } = $props();
</script>

<button
  class="btn {variant} {size}"
  class:full
  class:loading
  {type}
  disabled={disabled || loading}
  aria-busy={loading}
  aria-label={ariaLabel}
  {title}
  {onclick}
>
  {#if Icon}<Icon size={size === "sm" ? 15 : 17} strokeWidth={2} aria-hidden="true" />{/if}
  <span>{@render children()}</span>
</button>

<style>
  .btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.45rem;
    height: 44px;
    padding: 0 1.15rem;
    border-radius: var(--radius);
    border: 1px solid transparent;
    font-weight: 600;
    font-size: var(--t-sm);
    letter-spacing: 0.005em;
    white-space: nowrap;
    cursor: pointer;
    transition:
      background-color 160ms var(--ease),
      border-color 160ms var(--ease),
      box-shadow 160ms var(--ease),
      color 160ms var(--ease);
  }
  .sm {
    height: 36px;
    padding: 0 0.7rem;
    font-size: var(--t-xs);
  }
  .full {
    width: 100%;
  }
  .primary {
    background: var(--primary);
    color: var(--ink-inverse);
    box-shadow: 0 1px 2px rgb(9 9 11 / 0.12);
  }
  .primary:hover:not(:disabled) {
    background: var(--primary-hover);
  }
  .primary:active:not(:disabled) {
    background: var(--primary-active);
  }
  .secondary {
    background: var(--surface);
    border-color: var(--line-strong);
    color: var(--ink);
    box-shadow: 0 1px 2px rgb(9 9 11 / 0.05);
  }
  .secondary:hover:not(:disabled) {
    background: var(--surface-2);
    border-color: #a1a1aa;
  }
  .secondary:active:not(:disabled) {
    background: var(--rail);
  }
  .ghost {
    background: transparent;
    color: var(--ink-2);
  }
  .ghost:hover:not(:disabled) {
    background: rgb(9 9 11 / 0.06);
    color: var(--ink);
  }
  .danger {
    background: var(--surface);
    border-color: var(--danger-line);
    color: var(--danger);
  }
  .danger:hover:not(:disabled) {
    background: var(--danger-tint);
  }
  .btn:focus-visible {
    outline: none;
    box-shadow: var(--focus);
  }
  .btn:disabled {
    cursor: not-allowed;
    opacity: 0.55;
  }
  .loading span {
    opacity: 0.7;
  }
</style>
