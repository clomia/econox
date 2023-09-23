<script>
    import { onMount } from "svelte";
    import { Router, Route } from "svelte-routing";
    import { routes } from "./pages";
    import Navigator from "./components/Navigator.svelte";
    import CircleLoader from "./assets/animation/CircleLoader.svelte";
    import LangBtn from "./components/LangBtn.svelte";
    import { init } from "./modules/functions";

    let initPromise = init();
</script>

{#await initPromise}
    <div class="loading">
        <div><CircleLoader /></div>
    </div>
{:then}
    <header>
        <Navigator />
    </header>

    <main>
        <Router>
            {#each routes as route}
                <Route path={route.path}>
                    <svelte:component this={route.page} />
                </Route>
            {/each}
        </Router>
    </main>

    <aside>
        <LangBtn />
    </aside>
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
        background: -webkit-linear-gradient(to bottom, #202123, #1f3036);
        background: linear-gradient(to bottom, #202123, #1f3036);
        z-index: 1;
    }
</style>
