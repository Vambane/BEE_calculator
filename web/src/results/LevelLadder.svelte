<script>
  import { g } from "../lib/format.js";
  /** The level table as a scale, with the scorecard's position on it. */
  let { levels, points, level, discounted = false } = $props();

  const top = $derived(Math.max(110, Math.ceil((points ?? 0) / 10) * 10 + 5));
  const pos = (x) => `${(Math.min(Math.max(x, 0), top) / top) * 100}%`;
  // Bands from low to high: NC (0..40), L8 (40..55) ... L1 (100..top)
  const bands = $derived.by(() => {
    const asc = [...levels].sort((a, b) => a.min - b.min);
    const out = [{ from: 0, to: asc[0].min, level: 9, label: "NC" }];
    asc.forEach((l, i) => out.push({ from: l.min, to: asc[i + 1]?.min ?? top, level: l.level, label: `L${l.level}` }));
    return out;
  });
</script>

<figure class="ladder">
  <figcaption class="visually-hidden">
    Points for the level table: {g(points)}. Level thresholds: {levels.map((l) => `Level ${l.level} from ${l.min}`).join(", ")}.
  </figcaption>
  <div class="track" aria-hidden="true">
    {#each bands as b (b.label)}
      <div
        class="band"
        class:here={b.level === level && !discounted}
        class:nc={b.level === 9}
        style:left={pos(b.from)}
        style:width="calc({pos(b.to)} - {pos(b.from)})"
      >
        <span>{b.label}</span>
      </div>
    {/each}
    <div class="fill" style:width={pos(points ?? 0)}></div>
    <div class="marker" style:left={pos(points ?? 0)}>
      <span class="val">{g(Math.round((points ?? 0) * 10) / 10)} pts</span>
    </div>
  </div>
  <div class="ticks" aria-hidden="true">
    {#each [...levels].sort((a, b) => a.min - b.min) as l (l.level)}
      <span class:minor={![40, 55, 70, 80, 100].includes(l.min)} style:left={pos(l.min)}>{l.min}</span>
    {/each}
  </div>
</figure>

<style>
  .ladder {
    container: ladder / inline-size;
    margin: 0;
    padding: 2.1rem 1.35rem 0.25rem;
  }
  .track {
    position: relative;
    height: 34px;
    border-radius: var(--radius-sm);
    background: var(--surface-2);
    border: 1px solid var(--line);
    overflow: visible;
  }
  .band {
    position: absolute;
    top: 0;
    bottom: 0;
    display: grid;
    place-items: center;
    border-right: 1px solid var(--line-strong);
    font-size: 0.72rem;
    font-weight: 700;
    color: var(--ink-3);
    z-index: 1;
  }
  .band:last-child {
    border-right: 0;
  }
  .band.here {
    color: var(--primary-active);
  }
  .fill {
    position: absolute;
    left: 0;
    top: 0;
    bottom: 0;
    background: var(--primary-tint-2);
    border-radius: var(--radius-sm) 0 0 var(--radius-sm);
    transition: width 500ms var(--ease);
  }
  .marker {
    position: absolute;
    top: -6px;
    bottom: -6px;
    width: 3px;
    margin-left: -1.5px;
    background: var(--primary);
    border-radius: 2px;
    z-index: 2;
    transition: left 500ms var(--ease);
  }
  .val {
    position: absolute;
    bottom: calc(100% + 4px);
    left: 50%;
    transform: translateX(-50%);
    white-space: nowrap;
    font-size: var(--t-xs);
    font-weight: 700;
    color: var(--primary-active);
    background: var(--surface);
    padding: 0 0.3rem;
  }
  .ticks {
    position: relative;
    height: 1.2rem;
    margin-top: 0.3rem;
  }
  .ticks span {
    position: absolute;
    transform: translateX(-50%);
    font-size: 0.7rem;
    color: var(--ink-3);
  }
  @container ladder (max-width: 480px) {
    .ticks span.minor {
      display: none;
    }
  }
</style>
