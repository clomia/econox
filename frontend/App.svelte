<script>
	import { Router, Link, Route } from "svelte-routing";
	import Home from "./routes/Home.svelte";
	import SignIn from "./routes/SignIn.svelte";
	import Head from "./components/Head.svelte";

	export let url = "/";
</script>

<Head />
<Router {url}>
	<nav>
		<Link to="/">Home</Link>
		<Link to="/sign-in">SignIn</Link>
	</nav>
	<div>
		<Route path="/sign-in" component={SignIn} />
		<Route path="/" component={Home} />
	</div>
</Router>
