<script lang="ts">
  import RippleLoader from "../../../assets/animation/RippleLoader.svelte";
  import Elements from "./Elements.svelte";
  import Factors from "./Factors.svelte";
  import Note from "./Note.svelte";
  import Chart from "./Chart.svelte";
  import { setElements } from "./functions";

  const setElementsPromise = setElements();
</script>

<main>
  {#await setElementsPromise}
    <div class="loading"><RippleLoader /></div>
  {:then}
    <div class="element-selector"><Elements /></div>
  {/await}
  <div class="factor-selector"><Factors /></div>
  <div class="note"><Note /></div>
  <div class="chart"><Chart /></div>
</main>

<style>
  main {
    width: 44rem;
    border: thin solid rgba(255, 255, 255, 0.2);
    border-radius: 0.5rem;
    box-shadow: 0 0 2rem 0.1rem rgba(0, 0, 0, 0.5);
  }
  .loading {
    height: 12.87rem;
    display: flex;
    align-items: center;
    justify-content: center;
    border-bottom: thin solid rgba(255, 255, 255, 0.2);
  }
  .element-selector,
  .factor-selector {
    border-bottom: thin solid rgba(255, 255, 255, 0.2);
  }
</style>
