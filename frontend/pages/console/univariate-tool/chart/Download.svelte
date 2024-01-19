<script lang="ts">
  import { createEventDispatcher, onMount } from "svelte";
  import Excel from "../../../../assets/icon/Excel.svelte";
  import Csv from "../../../../assets/icon/Csv.svelte";
  import {
    UnivariateElementSelected,
    UnivariateFactorSelected,
  } from "../../../../modules/state";
  export let normalized: boolean;

  const dispatch = createEventDispatcher();
  onMount(() => {
    document.body.style.overflow = "hidden";
  });

  const close = () => {
    document.body.style.overflow = "";
    dispatch("close");
  };
</script>

<div class="membrane">
  <main>
    <Excel size="5rem" />
    <Csv size="5rem" />
    <div>파일 포멧 선택!</div>
    <div>{normalized}</div>

    <button on:click={close}>Close</button>
  </main>
</div>

<style>
  .membrane {
    position: fixed;
    width: 100vw;
    height: 100vh;
    top: 0;
    left: 0;
    z-index: 10;
    background-color: rgba(0, 0, 0, 0.4);
    display: flex;
    justify-content: center;
    align-items: center;
  }
  main {
    width: 30rem;
    height: 15rem;
    background: var(--widget-background);
    color: white;
  }
</style>
