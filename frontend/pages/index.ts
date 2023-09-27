import Account from "./account/index.svelte";
import Landing from "./Landing.svelte";
import PageNotFound from "./NotFound404.svelte";

interface Route {
    path: string;
    page: object;
}

export const routes: Route[] = [
    { path: "/", page: Landing },
    { path: "/account", page: Account },
    { path: "*", page: PageNotFound }, // 주의: 가장 밑에 있어야 함
];
