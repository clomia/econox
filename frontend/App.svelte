<script>
    import { onMount } from "svelte";
    import { Router, Route } from "svelte-routing";
    import { routes } from "./pages";
    import Navigator from "./components/Navigator.svelte";
    import LangBtn from "./components/LangBtn.svelte";
    import { loadUiText } from "./modules/uiText";
    import * as state from "./modules/state";

    onMount(async () => {
        const { text } = await loadUiText();
        state.uiText.text.set(text);
    });
</script>

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
