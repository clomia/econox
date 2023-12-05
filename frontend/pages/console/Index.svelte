<script>
  import { verify } from "../../modules/functions";
  import SearchBar from "./SearchBar.svelte";
  import UnivariateTool from "./univariate-tool/Index.svelte";

  verify({ conds: { billingOk: true }, failRedirect: "/account" });
</script>

<div class="search-bar"><SearchBar /></div>
<div class="tools">
  <div class="tool"><UnivariateTool /></div>
  <div class="tool"><div id="Tool2" /></div>
  <div class="tool"><div id="Tool3" /></div>
</div>

<style>
  .search-bar {
    margin-top: 2rem;
    display: flex;
    justify-content: center;
  }

  .tools {
    margin: 1rem 0;
    width: 100vw;
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  .tool {
    margin: 1rem;
  }

  #Tool2,
  #Tool3 {
    width: 44rem;
    height: 50rem;
    border: thin solid var(--border-white);
  }
</style>
