<script>
    import { verify } from "../../modules/functions";
    import SearchBar from "./SearchBar.svelte";

    verify({ conds: { billingOk: true }, failRedirect: "/account" });
</script>

<div class="search-bar"><SearchBar /></div>

<style>
    .search-bar {
        margin-top: 2rem;
    }
</style>
