import Account from "./Account.svelte";
import Landing from "./Landing.svelte";

interface Route {
    path: string;
    page: object;
}

export const routes: Route[] = [
    { path: "/", page: Landing },
    { path: "/account", page: Account },
];
