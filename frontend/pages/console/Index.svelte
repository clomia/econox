<script>
  import { verify } from "../../modules/functions";
  import SearchBar from "./SearchBar.svelte";
  import UnivariateTool from "./univariate-tool/Index.svelte";
  import MultivariateTool from "./multivariate-tool/Index.svelte";

  const verifyPromise = verify({
    conds: { billingOk: true },
    failRedirect: "/account",
  });
</script>

{#await verifyPromise then}
  <div class="search-bar"><SearchBar /></div>
  <div class="tools">
    <div class="tool"><UnivariateTool /></div>
    <div class="tool"><MultivariateTool /></div>
  </div>
{/await}

<style>
  .search-bar {
    margin-top: 2rem;
    display: flex;
    justify-content: center;
  }

  .tools {
    margin: 1rem 0;
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  .tool {
    margin: 1rem;
    margin-bottom: 3rem;
  }
  .tools > .tool:last-child {
    margin-bottom: 0;
  }
</style>
