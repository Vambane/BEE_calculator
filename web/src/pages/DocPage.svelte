<script>
  import { ArrowLeft } from "@lucide/svelte";
  import { marked } from "marked";

  let { doc } = $props();
  const files = { howto: "/docs/HOW_TO.md", privacy: "/docs/PRIVACY_WEB.md" };
  let html = $state("");
  let failed = $state(false);

  // The docs ship with the site (no user content), but strip raw HTML anyway.
  marked.use({ renderer: { html: () => "" } });

  $effect(() => {
    failed = false;
    fetch(files[doc])
      .then((r) => (r.ok ? r.text() : Promise.reject()))
      .then((md) => {
        // In-app links: "?page=privacy" in the shared docs becomes a hash route here.
        html = marked.parse(md.replaceAll("(?page=privacy)", "(#/privacy)").replaceAll("(?page=howto)", "(#/howto)"));
      })
      .catch(() => (failed = true));
  });
</script>

<article class="doc">
  <a class="back" href="#/"><ArrowLeft size={16} aria-hidden="true" />Back to the calculator</a>
  {#if failed}
    <p>This page could not be loaded. Check your connection and try again.</p>
  {:else}
    <div class="prose">{@html html}</div>
  {/if}
</article>

<style>
  .doc {
    max-width: 760px;
    margin: 0 auto;
    background: var(--surface);
    border: 1px solid var(--line);
    border-radius: var(--radius-lg);
    box-shadow: var(--shadow-1);
    padding: 1.5rem 2rem 2.25rem;
  }
  .back {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    font-size: var(--t-sm);
    font-weight: 600;
    text-decoration: none;
    margin-bottom: 1rem;
  }
  .prose {
    font-size: var(--t-md);
    color: var(--ink-2);
    line-height: 1.6;
  }
  .prose :global(h1) {
    font-size: var(--t-2xl);
    color: var(--ink);
    margin-bottom: 1rem;
    letter-spacing: -0.02em;
  }
  .prose :global(h2) {
    font-size: var(--t-lg);
    color: var(--ink);
    margin: 2rem 0 0.6rem;
  }
  .prose :global(h3) {
    font-size: var(--t-md);
    color: var(--ink);
    margin: 1.4rem 0 0.4rem;
  }
  .prose :global(p),
  .prose :global(ul),
  .prose :global(ol) {
    margin: 0 0 0.85rem;
    max-width: 70ch;
  }
  .prose :global(li) {
    margin-bottom: 0.3rem;
  }
  .prose :global(strong) {
    color: var(--ink);
  }
  .prose :global(hr) {
    border: 0;
    border-top: 1px solid var(--line);
    margin: 1.75rem 0;
  }
  .prose :global(blockquote) {
    margin: 0 0 1rem;
    padding: 0.75rem 1rem;
    background: var(--warning-tint);
    border: 1px solid var(--warning-line);
    border-radius: var(--radius);
    color: #713f12;
  }
  .prose :global(blockquote p) {
    margin: 0;
  }
  .prose :global(table) {
    width: 100%;
    border-collapse: collapse;
    font-size: var(--t-sm);
    margin: 0.5rem 0 1rem;
  }
  .prose :global(th),
  .prose :global(td) {
    text-align: left;
    padding: 0.5rem 0.6rem;
    border-bottom: 1px solid var(--line);
    vertical-align: top;
  }
  .prose :global(th) {
    background: var(--surface-2);
    color: var(--ink);
    font-size: var(--t-xs);
  }
  .prose :global(code) {
    font-size: 0.9em;
    background: var(--rail);
    padding: 0.05rem 0.3rem;
    border-radius: 4px;
  }
  @media (max-width: 640px) {
    .doc {
      padding: 1.1rem 1rem 1.5rem;
    }
  }
</style>
