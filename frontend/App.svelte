<script>
  import { Router, Route } from "svelte-routing";
  import { routes } from "./pages";
  import Navigator from "./components/Navigator.svelte";
  import CircleLoader from "./assets/animation/CircleLoader.svelte";
  import LangBtn from "./components/LangBtn.svelte";
  import { init } from "./modules/functions";

  const initPromise = init();
</script>

{#await initPromise}
  <div class="loading">
    <div><CircleLoader /></div>
  </div>
{:then}
  <Router>
    {#each routes as route}
      <Route path={route.path} let:params>
        <header>
          <Navigator url={route.path} />
        </header>
        <main>
          <svelte:component this={route.page} {params} />
        </main>
        <aside>
          <LangBtn url={route.path} />
        </aside>
      </Route>
    {/each}
  </Router>
{/await}

<style>
  .loading {
    position: fixed;
    width: 100vw;
    height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding-bottom: 25vh;
    background: var(--background);
    z-index: 1;
  }
</style>
