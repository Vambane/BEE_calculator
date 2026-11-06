<script>
  import { onMount, untrack } from "svelte";
  import { app, start, refresh, steps, currentStep } from "./lib/state.svelte.js";
  import TopBar from "./shell/TopBar.svelte";
  import StepRail from "./shell/StepRail.svelte";
  import MobileSteps from "./shell/MobileSteps.svelte";
  import Loading from "./shell/Loading.svelte";
  import ProfileStep from "./steps/ProfileStep.svelte";
  import ElementStep from "./steps/ElementStep.svelte";
  import ResultsStep from "./steps/ResultsStep.svelte";
  import DocPage from "./pages/DocPage.svelte";
  import ReportView from "./report/ReportView.svelte";
  import Notice from "./ui/Notice.svelte";

  function route() {
    const h = location.hash.replace(/^#\/?/, "");
    app.view = ["howto", "privacy", "report"].includes(h) ? h : "app";
  }

  onMount(() => {
    route();
    window.addEventListener("hashchange", route);
    start();
    const warn = (e) => {
      if (app.dirty) {
        e.preventDefault();
        e.returnValue = "";
      }
    };
    window.addEventListener("beforeunload", warn);
    return () => {
      window.removeEventListener("hashchange", route);
      window.removeEventListener("beforeunload", warn);
    };
  });

  // Any change to the session re-derives steps and forms from the engine.
  let lastKey = "";
  $effect(() => {
    if (!app.ready || !app.session) return;
    const key = JSON.stringify(app.session);
    if (key === lastKey) return;
    const first = lastKey === "";
    lastKey = key;
    if (!first) {
      app.dirty = true;
      // Errors describe the figures at the last Continue; an edit makes them stale.
      untrack(() => {
        if (Object.keys(app.stepErrors).length) app.stepErrors = {};
      });
    }
    const t = setTimeout(refresh, 60);
    return () => clearTimeout(t);
  });

  const step = $derived(app.ctx ? currentStep() : null);
</script>

{#if app.view === "report" && app.ready}
  <ReportView />
{:else}
  <div class="shell">
    <TopBar />
    <div class="body">
      <aside class="rail" aria-label="Steps">
        <div class="rail-sticky"><StepRail /></div>
      </aside>
      <main id="main">
        {#if app.view === "howto" || app.view === "privacy"}
          <DocPage doc={app.view} />
        {:else if app.failed}
          <div class="wrap">
            <Notice tone="danger" title="The calculator could not start">
              <p>
                Your browser could not load the scoring engine ({app.failed}). Reload the page to try
                again. Klim needs a recent version of Chrome, Edge, Firefox or Safari.
              </p>
            </Notice>
          </div>
        {:else if !app.ready || !step}
          <Loading />
        {:else}
          <MobileSteps />
          {#if app.notice}
            <div class="wrap notice-wrap">
              <Notice tone={app.notice.tone} title={app.notice.title} lines={app.notice.lines} />
            </div>
          {/if}
          {#if app.session.draft}
            <div class="wrap notice-wrap">
              <Notice tone="warning" title="Draft rules on: not in force" compact>
                <p>
                  Draft Statement 400 / Draft QSE Code Series 600 of 2026 (GG 54032, 29 Jan 2026). The
                  Transformation Fund uses indicator sums only (ESD max 45 Fund / 40 ED+SD), not
                  scaled to 55.
                </p>
              </Notice>
            </div>
          {/if}
          {#key step.key}
            {#if step.key === "profile"}
              <ProfileStep />
            {:else if step.key === "results"}
              <ResultsStep />
            {:else}
              <ElementStep spec={app.ctx.elements[step.key]} />
            {/if}
          {/key}
        {/if}
      </main>
    </div>
  </div>
{/if}

<style>
  .shell {
    min-height: 100dvh;
    display: flex;
    flex-direction: column;
  }
  .body {
    flex: 1;
    display: grid;
    grid-template-columns: var(--rail-w) minmax(0, 1fr);
  }
  .rail {
    background: var(--rail);
    border-right: 1px solid var(--line);
  }
  .rail-sticky {
    position: sticky;
    top: var(--topbar-h);
    height: calc(100dvh - var(--topbar-h));
    overflow-y: auto;
  }
  main {
    min-width: 0;
    padding: 1.75rem 2rem 4rem;
  }
  .wrap {
    max-width: 880px;
    margin: 0 auto;
  }
  .notice-wrap {
    margin-bottom: 1rem;
  }
  @media (max-width: 900px) {
    .body {
      grid-template-columns: minmax(0, 1fr);
    }
    .rail {
      display: none;
    }
    main {
      padding: 1rem 1rem 3rem;
    }
  }
  @media print {
    .shell {
      display: none;
    }
  }
</style>
