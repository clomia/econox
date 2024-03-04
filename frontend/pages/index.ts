import Auth from "./auth/Index.svelte";
import Account from "./account/Index.svelte";
import Console from "./console/Index.svelte";
import Public from "./public/Index.svelte";
import Intro from "./intro/Index.svelte";
import PageNotFound from "./NotFound404.svelte";

interface Route {
  path: string;
  page: object;
}

export const routes: Route[] = [
  { path: "/", page: Intro },
  { path: "/auth", page: Auth },
  { path: "/account", page: Account },
  { path: "/console", page: Console },
  { path: "/public/:featureGroupId", page: Public },
  { path: "*", page: PageNotFound }, // 주의: 가장 밑에 있어야 함
];
