<script>
  import { FolderOpen, Download } from "@lucide/svelte";
  import Button from "../ui/Button.svelte";
  import { app, consented, saveClientFile, openClientFile } from "../lib/state.svelte.js";
  import { pickFile, readTextFile } from "../lib/files.js";

  let { inert = false } = $props();

  const company = $derived(app.session?.store?.profile?.company || "");
  const label = $derived(app.ctx?.label?.split(" · ").slice(0, 2).join(" · ") ?? "");

  async function open() {
    const file = await pickFile(".json,application/json");
    if (!file) return;
    if (app.dirty && !confirm("Open another client file? Changes you have not saved will be lost.")) return;
    try {
      await openClientFile(await readTextFile(file, app.meta.client_file.max_bytes));
    } catch (err) {
      app.notice = { tone: "danger", title: "Could not open that file", lines: [err.message] };
    }
  }
</script>

<header class="top" {inert}>
  <a class="brand" href="#/" aria-label="Klim, back to the calculator">
    <svg width="22" height="22" viewBox="0 0 22 22" aria-hidden="true">
      <rect x="1" y="1" width="20" height="20" rx="5" fill="var(--primary)" />
      <path d="M6.2 11.4l3.1 3.1 6.5-7" fill="none" stroke="#fff" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round" />
    </svg>
    <span>Klim</span>
  </a>
  {#if app.ready && app.view === "app"}
    <div class="client" title={app.ctx?.label}>
      <span class="name">{company || "New client"}</span>
      {#if label}<span class="chip">{label}</span>{/if}
      {#if app.dirty && consented()}<span class="unsaved">Unsaved</span>{/if}
    </div>
    <div class="actions">
      <Button size="sm" icon={FolderOpen} onclick={open}>Open<span class="long">&nbsp;client file</span></Button>
      <Button
        size="sm"
        variant={app.dirty && consented() ? "primary" : "secondary"}
        icon={Download}
        disabled={!consented()}
        title={consented() ? "Save this calculation to a file on your device" : "Agree to the privacy notice on Profile first"}
        onclick={saveClientFile}>Save<span class="long">&nbsp;client file</span></Button
      >
    </div>
  {/if}
</header>

<style>
  .top {
    position: sticky;
    top: 0;
    z-index: 20;
    height: var(--topbar-h);
    display: flex;
    align-items: center;
    gap: 1.25rem;
    padding: 0 1.25rem;
    background: var(--surface);
    border-bottom: 1px solid var(--line);
  }
  .brand {
    display: inline-flex;
    align-items: center;
    gap: 0.55rem;
    width: calc(var(--rail-w) - 1.25rem);
    flex: none;
    text-decoration: none;
    color: var(--ink);
    font-weight: 750;
    font-size: 1.0625rem;
    letter-spacing: -0.01em;
  }
  .brand:focus-visible {
    outline: none;
    box-shadow: var(--focus);
    border-radius: var(--radius-sm);
  }
  .client {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    min-width: 0;
    flex: 1;
  }
  .name {
    font-weight: 650;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 32ch;
  }
  .chip {
    flex: none;
    font-size: var(--t-xs);
    font-weight: 600;
    color: var(--ink-2);
    background: var(--rail);
    border: 1px solid var(--line);
    padding: 0.15rem 0.55rem;
    border-radius: 999px;
    white-space: nowrap;
  }
  .unsaved {
    flex: none;
    font-size: var(--t-xs);
    font-weight: 600;
    color: var(--warning);
  }
  .actions {
    display: flex;
    gap: 0.5rem;
    margin-left: auto;
  }
  @media (max-width: 900px) {
    .brand {
      width: auto;
    }
    .chip,
    .unsaved {
      display: none;
    }
    .long {
      display: none;
    }
  }
  @media (max-width: 520px) {
    .client {
      display: none;
    }
    .top {
      gap: 0.5rem;
      padding: 0 0.75rem;
    }
  }
</style>
