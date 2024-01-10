<script lang="ts">
  import BouncingCubeLoader from "../../../assets/animation/BouncingCubeLoader.svelte";
  import Elements from "./Elements.svelte";
  import Factors from "./Factors.svelte";
  import Note from "./Note.svelte";
  import Chart from "./chart/Index.svelte";
  import { setElements } from "./functions";
  import { Text } from "../../../modules/state";

  const setElementsPromise = setElements();
</script>

<main>
  {#await setElementsPromise}
    <div class="loading">
      <BouncingCubeLoader backgroundColor="#41425e" borderColor="#fb7cf7" />
      <div class="load-info">{$Text.ElementLoadingInfo}</div>
    </div>
  {:then}
    <div class="element-selector"><Elements /></div>
    <div class="factor-selector"><Factors /></div>
  {/await}
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
    height: 20rem;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
    padding-top: 4rem;
  }
  .load-info {
    position: absolute;
    display: flex;
    width: 100%;
    height: 100%;
    align-items: center;
    justify-content: center;
    bottom: 0;
    left: 0;
    padding-bottom: 16rem;
    color: rgba(255, 255, 255, 0.6);
  }
</style>
