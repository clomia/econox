<script>
	import { Router, Route } from "svelte-routing";
	import { routes } from "./pages";
	import Header from "./components/Header.svelte";
	import Footer from "./components/Footer.svelte";
</script>

<Header />
<Router>
	{#each routes as route}
		<Route path={route.path}>
			<svelte:component this={route.page} />
		</Route>
	{/each}
</Router>
<Footer />
