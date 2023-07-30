<script>
	import { Router, Route } from "svelte-routing";
	import * as page from "./pages";
	import Header from "./components/Header.svelte";
	import Footer from "./components/Footer.svelte";

	const routes = [
		{ path: "/", component: page.Landing },
		{ path: "/account", component: page.Account },
	];
</script>

<Header />
<Router>
	{#each routes as route}
		<Route path={route.path}>
			<svelte:component this={route.component} />
		</Route>
	{/each}
</Router>
<Footer />
