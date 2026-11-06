<script>
  import { ArrowLeft, ArrowRight } from "@lucide/svelte";
  import Button from "../ui/Button.svelte";
  import Notice from "../ui/Notice.svelte";
  import { app, steps, continueStep, back } from "../lib/state.svelte.js";

  let { title, intro = "", children, wide = false, aside } = $props();
  let busy = $state(false);

  const list = $derived(steps());
  const key = $derived(list[app.step]?.key);
  const errors = $derived(app.stepErrors[key] ?? []);
  const nextName = $derived(list[app.step + 1]?.name);

  async function next() {
    busy = true;
    try {
      await continueStep();
    } finally {
      busy = false;
    }
  }
</script>

<div class="frame" class:wide>
  <header class="head">
    <div>
      <h1>{title}</h1>
      {#if intro}<p class="intro">{intro}</p>{/if}
    </div>
    {#if aside}<div class="aside">{@render aside()}</div>{/if}
  </header>

  <div class="content">{@render children()}</div>

  {#if errors.length}
    <div class="errors">
      <Notice tone="danger" title="Fix these to continue" lines={errors} />
    </div>
  {/if}

  <nav class="foot" aria-label="Step navigation">
    {#if app.step > 0}
      <Button variant="ghost" icon={ArrowLeft} onclick={back}>Back</Button>
    {:else}
      <span></span>
    {/if}
    {#if nextName}
      <Button variant="primary" loading={busy} onclick={next}>
        <span class="lbl">Continue<span class="to">&nbsp;to {nextName}</span></span><ArrowRight size={17} aria-hidden="true" />
      </Button>
    {/if}
  </nav>
</div>

<style>
  .frame {
    max-width: 880px;
    margin: 0 auto;
  }
  /* Staggered entrance, as on the sign-in theme: title, intro, each card, then the footer. */
  .head h1,
  .intro,
  .content > :global(*),
  .foot {
    animation: fadeSlideIn 0.6s var(--ease) both;
  }
  .head h1 {
    animation-delay: 0.05s;
  }
  .intro {
    animation-delay: 0.12s;
  }
  .content > :global(:nth-child(1)) {
    animation-delay: 0.2s;
  }
  .content > :global(:nth-child(2)) {
    animation-delay: 0.28s;
  }
  .content > :global(:nth-child(3)) {
    animation-delay: 0.36s;
  }
  .content > :global(:nth-child(n + 4)) {
    animation-delay: 0.44s;
  }
  .foot {
    animation-delay: 0.5s;
  }
  .wide {
    max-width: 1040px;
  }
  .head {
    display: flex;
    align-items: flex-end;
    justify-content: space-between;
    gap: 1rem;
    margin-bottom: 1.35rem;
  }
  h1 {
    font-size: var(--t-2xl);
    font-weight: 600;
    letter-spacing: -0.035em;
  }
  .intro {
    margin-top: 0.4rem;
    color: var(--ink-2);
    max-width: 68ch;
  }
  .aside {
    flex: none;
  }
  .content {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
    gap: 1rem;
  }
  .errors {
    margin-top: 1rem;
  }
  .foot {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: 1.5rem;
    padding-top: 1.25rem;
    border-top: 1px solid var(--line);
  }
  .foot :global(.btn.primary span) {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
  }
  .foot :global(.btn.primary .lbl),
  .foot :global(.btn.primary .lbl .to) {
    display: inline;
  }
  @media (max-width: 640px) {
    .foot :global(.btn.primary .lbl .to) {
      display: none;
    }
    h1 {
      font-size: var(--t-xl);
    }
    .head {
      flex-direction: column;
      align-items: flex-start;
    }
  }
</style>
