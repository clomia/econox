<script>
    import { onMount } from "svelte";
    import { Router, Route } from "svelte-routing";
    import { routes } from "./pages";
    import Navigator from "./components/Navigator.svelte";
    import LangBtn from "./components/LangBtn.svelte";
    import { loadUiText } from "./modules/uiText";
    import { isLoggedIn } from "./modules/functions";
    import { api } from "./modules/request";
    import { Text, UserInfo } from "./modules/state";

    const userSetup = async () => {
        if (await isLoggedIn()) {
            return await api.private.get("/user"); // 유저정보 가져오는 동안 로딩잠깐 띄우기?
        }
    };

    onMount(async () => {
        const currentUrl = new URL(window.location.href);
        const { hostname } = currentUrl;
        const localHosts = ["localhost", "127.0.0.1"];

        if (!hostname.startsWith("www.") && !localHosts.includes(hostname)) {
            currentUrl.hostname = "www." + hostname;
            window.location.href = currentUrl.toString();
        }
        // ==================================================================
        const [{ text }, userInfo] = await Promise.all([loadUiText(), userSetup()]);
        $Text = text;
        $UserInfo = userInfo;
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
