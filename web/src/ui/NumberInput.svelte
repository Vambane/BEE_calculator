<script>
  import { groupThousands, parseNumber } from "../lib/format.js";

  /**
   * Number entry that accepts what people paste from spreadsheets ("1 250 000", "R1,250,000").
   * Shows grouped thousands when not focused. `value` is a number or null.
   */
  let {
    id,
    value = $bindable(null),
    prefix = "",
    suffix = "",
    decimals = 0,
    disabled = false,
    placeholder = "",
    invalid = false,
    describedby,
    onchange,
    allowNull = false,
    min,
    max,
  } = $props();

  let focused = $state(false);
  let draft = $state("");

  const shown = $derived(
    focused ? draft : value === null || value === undefined ? "" : groupThousands(value, decimals),
  );

  function onfocus() {
    draft = value === null || value === undefined ? "" : String(value);
    focused = true;
  }
  function oninput(e) {
    draft = e.currentTarget.value;
    const n = parseNumber(draft);
    if (n === null && !allowNull && draft.trim() === "") value = 0;
    else value = n;
  }
  function onblur() {
    focused = false;
    let n = parseNumber(draft);
    if (n !== null) {
      if (min !== undefined && n < min) n = min;
      if (max !== undefined && n > max) n = max;
    }
    value = n === null ? (allowNull ? null : 0) : n;
    onchange?.(value);
  }
</script>

<div class="num" class:disabled class:invalid>
  {#if prefix}<span class="affix pre" aria-hidden="true">{prefix}</span>{/if}
  <input
    {id}
    type="text"
    inputmode="decimal"
    autocomplete="off"
    spellcheck="false"
    {disabled}
    {placeholder}
    value={shown}
    aria-invalid={invalid}
    aria-describedby={describedby}
    {onfocus}
    {oninput}
    {onblur}
  />
  {#if suffix}<span class="affix post" aria-hidden="true">{suffix}</span>{/if}
</div>

<style>
  .num {
    display: flex;
    align-items: center;
    height: 48px;
    background: var(--glass);
    border: 1px solid var(--line);
    border-radius: var(--radius);
    transition:
      border-color 150ms var(--ease),
      background-color 150ms var(--ease),
      box-shadow 150ms var(--ease);
  }
  .num:hover:not(.disabled) {
    border-color: #a1a1aa;
  }
  .num:focus-within {
    border-color: var(--accent);
    background: var(--glass-focus);
    box-shadow: var(--focus);
  }
  .invalid {
    border-color: var(--danger);
  }
  .invalid:focus-within {
    box-shadow: 0 0 0 3px rgb(185 28 28 / 0.2);
  }
  .disabled {
    background: var(--rail);
    border-color: var(--line);
    color: var(--ink-3);
    box-shadow: none;
  }
  .disabled input {
    color: var(--ink-3);
  }
  input {
    flex: 1;
    min-width: 0;
    height: 100%;
    border: 0;
    background: transparent;
    padding: 0 1rem;
    font-size: var(--t-md);
    font-variant-numeric: tabular-nums;
    text-align: right;
    outline: none;
  }
  input:disabled {
    cursor: not-allowed;
  }
  input::placeholder {
    color: var(--ink-3);
  }
  .affix {
    color: var(--ink-3);
    font-size: var(--t-sm);
    font-weight: 550;
    user-select: none;
  }
  .pre {
    padding-left: 0.75rem;
  }
  .pre + input {
    padding-left: 0.4rem;
  }
  .post {
    padding-right: 0.75rem;
    white-space: nowrap;
  }
  input:has(+ .post) {
    padding-right: 0.4rem;
  }
</style>
