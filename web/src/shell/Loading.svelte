<script>
  import { onMount } from "svelte";
  let slow = $state(false);
  onMount(() => {
    const t = setTimeout(() => (slow = true), 2500);
    return () => clearTimeout(t);
  });
</script>

<div class="wrap" aria-busy="true" aria-live="polite">
  <div class="sk title"></div>
  <div class="sk line"></div>
  <div class="card">
    <div class="sk row"></div>
    <div class="sk row short"></div>
    <div class="grid">
      <div class="sk field"></div>
      <div class="sk field"></div>
    </div>
    <div class="sk row"></div>
  </div>
  <p class="msg">
    Loading the calculator engine{#if slow}. The first visit downloads it once (about 10 MB);
      after that it opens from your browser's cache{/if}.
  </p>
</div>

<style>
  .wrap {
    max-width: 880px;
    margin: 0 auto;
    display: grid;
    gap: 0.75rem;
  }
  .card {
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: var(--radius-lg);
    padding: 1.25rem;
    display: grid;
    gap: 1rem;
    margin-top: 0.75rem;
  }
  .grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
  }
  .sk {
    border-radius: 6px;
    background: linear-gradient(90deg, #f4f4f5 0%, #fafafa 50%, #f4f4f5 100%);
    background-size: 200% 100%;
    animation: shimmer 1.4s linear infinite;
  }
  .title {
    width: 46%;
    height: 30px;
  }
  .line {
    width: 70%;
    height: 14px;
  }
  .row {
    height: 14px;
  }
  .short {
    width: 60%;
  }
  .field {
    height: 64px;
  }
  .msg {
    margin-top: 0.5rem;
    font-size: var(--t-sm);
    color: var(--ink-3);
  }
  @keyframes shimmer {
    from {
      background-position: 100% 0;
    }
    to {
      background-position: -100% 0;
    }
  }
</style>
