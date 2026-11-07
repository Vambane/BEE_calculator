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

  let narrow = $state(false);
  let stepsOpen = $state(false);

  function route() {
    const h = location.hash.replace(/^#\/?/, "");
    app.view = ["howto", "privacy", "report"].includes(h) ? h : "app";
  }

  function closeSteps() {
    stepsOpen = false;
    requestAnimationFrame(() => document.getElementById("steps-toggle")?.focus());
  }

  onMount(() => {
    route();
    const onHash = () => {
      route();
      if (stepsOpen) closeSteps();
    };
    window.addEventListener("hashchange", onHash);
    start();
    const warn = (e) => {
      if (app.dirty) {
        e.preventDefault();
        e.returnValue = "";
      }
    };
    window.addEventListener("beforeunload", warn);
    const mq = window.matchMedia("(max-width: 900px)");
    const apply = () => {
      narrow = mq.matches;
      if (!mq.matches) stepsOpen = false;
    };
    apply();
    mq.addEventListener("change", apply);
    const onKey = (e) => {
      if (e.key === "Escape" && stepsOpen) {
        e.preventDefault();
        closeSteps();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => {
      window.removeEventListener("hashchange", onHash);
      window.removeEventListener("beforeunload", warn);
      window.removeEventListener("keydown", onKey);
      mq.removeEventListener("change", apply);
    };
  });

  $effect(() => {
    if (!stepsOpen) return;
    requestAnimationFrame(() => {
      const rail = document.getElementById("step-rail");
      const target = rail?.querySelector(".step.current") || rail?.querySelector(".rail-close");
      if (target instanceof HTMLElement) target.focus();
    });
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
    <TopBar inert={narrow && stepsOpen} />
    {#if narrow && stepsOpen}
      <div class="scrim" aria-hidden="true" onclick={closeSteps}></div>
    {/if}
    <div class="body">
      <aside
        id="step-rail"
        class="rail"
        class:open={stepsOpen}
        aria-label="Steps"
        role={narrow && stepsOpen ? "dialog" : undefined}
        aria-modal={narrow && stepsOpen ? "true" : undefined}
        inert={narrow && !stepsOpen}
      >
        <button type="button" class="rail-close" onclick={closeSteps}>Close steps</button>
        <div class="rail-sticky"><StepRail onpicked={() => narrow && closeSteps()} /></div>
      </aside>
      <main id="main" inert={narrow && stepsOpen}>
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
          <MobileSteps bind:open={stepsOpen} />
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
  .rail-close {
    display: none;
  }
  .rail-sticky {
    position: sticky;
    top: var(--topbar-h);
    height: calc(100dvh - var(--topbar-h));
    overflow-y: auto;
  }
  .scrim {
    position: fixed;
    inset: 0;
    z-index: 30;
    background: rgb(9 9 11 / 0.4);
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
    .rail.open {
      display: flex;
      flex-direction: column;
      position: fixed;
      z-index: 40;
      top: 0;
      bottom: 0;
      left: 0;
      width: min(19.5rem, calc(100vw - 2.75rem));
      max-width: 100%;
      background: var(--rail);
      border-right: 1px solid var(--line);
      box-shadow: var(--shadow-pop);
    }
    .rail-close {
      display: flex;
      align-items: center;
      flex: none;
      width: calc(100% - 1.5rem);
      margin: 0.75rem 0.75rem 0;
      min-height: 44px;
      padding: 0 0.85rem;
      border: 1px solid var(--line-strong);
      border-radius: var(--radius-sm);
      background: var(--surface);
      color: var(--ink);
      font-weight: 650;
      font-size: var(--t-sm);
      cursor: pointer;
    }
    .rail-close:focus-visible {
      outline: none;
      box-shadow: var(--focus);
    }
    .rail-sticky {
      position: relative;
      top: auto;
      height: auto;
      flex: 1;
      min-height: 0;
    }
    main {
      padding: 1rem 1rem 3rem;
    }
  }
  @media (max-width: 430px) {
    main {
      padding: 0.75rem 0.75rem 2.5rem;
    }
  }
  @media print {
    .shell {
      display: none;
    }
  }
</style>
