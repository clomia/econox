<script>
	import { Router, Link, Route } from "svelte-routing";
	import Head from "./components/Head.svelte";
	import Home from "./routes/Home.svelte";
	import Signup from "./routes/Signup.svelte";
	import Login from "./routes/Login.svelte";
	import Auth from "./routes/Auth.svelte";
	export let path = window.location.pathname;
</script>

<Head />
<Router {path}>
	<nav>
		<Link to="/">Home</Link>
		<Link to="/signup">Signup</Link>
		<Link to="/login">login</Link>
		<Link to="/auth">auth</Link>
	</nav>
	<div>
		<Route path="/" component={Home} />
		<Route path="/signup" component={Signup} />
		<Route path="/login" component={Login} />
		<Route path="/auth" component={Auth} />
	</div>
</Router>
