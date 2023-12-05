<script lang="ts">
  import CircleDotLoader from "../../../assets/animation/CircleDotLoader.svelte";
  import Elements from "./Elements.svelte";
  import Factors from "./Factors.svelte";
  import { setElements } from "./functions";

  const setElementsPromise = setElements();
</script>

<main>
  {#await setElementsPromise}
    <div class="loading">
      <div><CircleDotLoader /></div>
    </div>
  {:then}
    <div class="element-selector"><Elements /></div>
    <div class="factor-selector"><Factors /></div>
  {/await}
</main>

<style>
  main {
    width: 44rem;
    border: thin solid rgba(255, 255, 255, 0.2);
    border-radius: 0.5rem;
    box-shadow: 0 0 2rem 0.1rem rgba(0, 0, 0, 0.5);
  }
  .loading {
    width: 100%;
    height: 10rem;
    display: flex;
    align-items: center;
    justify-content: center;
  }
</style>
