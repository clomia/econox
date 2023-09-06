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

        const currentUrl = new URL(window.location.href);
        const { hostname } = currentUrl;
        const localHosts = ["localhost", "127.0.0.1"];

        if (!hostname.startsWith("www.") && !localHosts.includes(hostname)) {
            currentUrl.hostname = "www." + hostname;
            window.location.href = currentUrl.toString();
        }
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
