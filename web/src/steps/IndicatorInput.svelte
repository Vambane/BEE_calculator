<script>
  import NumberInput from "../ui/NumberInput.svelte";
  import Checkbox from "../ui/Checkbox.svelte";

  /** One indicator. `ind` is the engine's spec; `vals` is the element's value bucket. */
  let { ind, label, vals } = $props();

  const id = $derived(`ind-${ind.clause.replaceAll(/[^a-z0-9]/gi, "-")}`);
  const value = {
    get v() {
      const x = vals[ind.clause];
      return typeof x === "number" ? x : 0;
    },
    set v(n) {
      vals[ind.clause] = n ?? 0;
    },
  };
</script>

{#if ind.kind === "bool"}
  <div class="bool">
    <Checkbox {id} checked={vals[ind.clause] === true} onchange={(e) => (vals[ind.clause] = e.currentTarget.checked)} help={ind.help}>
      {label}{#if ind.tag}<span class="tag">{ind.tag}</span>{/if}
    </Checkbox>
  </div>
{:else}
  <div class="ind">
    <label for={id}>
      <span class="name">{label}{#if ind.tag}<span class="tag">{ind.tag}</span>{/if}</span>
    </label>
    <NumberInput
      {id}
      bind:value={value.v}
      prefix={ind.unit === "R" ? "R" : ""}
      suffix={ind.unit && ind.unit !== "R" ? (ind.unit === "count" ? "people" : ind.unit) : ""}
      decimals={ind.rand ? 0 : 2}
      describedby="{id}-meta"
    />
    <p class="meta" id="{id}-meta">
      Target <strong>{ind.target_text}</strong> · {ind.points_text} · cl. {ind.clause}
    </p>
  </div>
{/if}

<style>
  .ind {
    display: grid;
    gap: 0.35rem;
    min-width: 0;
  }
  label {
    font-size: var(--t-sm);
    font-weight: 600;
    line-height: 1.35;
  }
  .tag {
    margin-left: 0.4rem;
    font-size: 0.7rem;
    font-weight: 700;
    letter-spacing: 0.02em;
    text-transform: uppercase;
    color: var(--warning);
    background: var(--warning-tint);
    padding: 0.05rem 0.35rem;
    border-radius: 4px;
    vertical-align: 1px;
  }
  .meta {
    font-size: var(--t-xs);
    color: var(--ink-3);
  }
  .meta strong {
    color: var(--ink-2);
    font-weight: 650;
  }
  .bool {
    padding: 0.2rem 0;
  }
</style>
