<script>
	import { Router, Link, Route } from "svelte-routing";
	import Home from "./routes/Home.svelte";
	import Signup from "./routes/Signup.svelte";
	import Head from "./components/Head.svelte";
	export let path = window.location.pathname;
</script>

<Head />
<Router {path}>
	<nav>
		<Link to="/">Home</Link>
		<Link to="/signup">Signup</Link>
	</nav>
	<div>
		<Route path="/signup" component={Signup} />
		<Route path="/" component={Home} />
	</div>
</Router>
