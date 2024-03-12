import Auth from "./auth/Index.svelte";
import Account from "./account/Index.svelte";
import Console from "./console/Index.svelte";
import Share from "./share/Index.svelte";
import Intro from "./intro/Index.svelte";
import E404 from "./E404.svelte";

interface Route {
  path: string;
  page: object;
}

export const routes: Route[] = [
  { path: "/", page: Intro },
  { path: "/auth", page: Auth },
  { path: "/account", page: Account },
  { path: "/console", page: Console },
  { path: "/share/:featureGroupId", page: Share },
  { path: "*", page: E404 }, // 주의: 가장 밑에 있어야 함
];
