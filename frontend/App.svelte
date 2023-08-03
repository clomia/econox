<script>
	import { Router, Route } from "svelte-routing";
	import { loadText } from "./modules/lang";
	import { routes } from "./pages";
	import Header from "./components/Header.svelte";
	import Footer from "./components/Footer.svelte";
</script>

{#await loadText() then text}
	<Header {text} />
	<Router>
		{#each routes as route}
			<Route path={route.path}>
				<svelte:component this={route.page} {text} />
			</Route>
		{/each}
	</Router>
	<Footer {text} />
{/await}
