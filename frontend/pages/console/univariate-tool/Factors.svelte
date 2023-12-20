<script lang="ts">
  import { get } from "svelte/store";
  import Magnifier from "../../../assets/icon/Magnifier.svelte";
  import ProgressBar from "../../../components/ProgressBar.svelte";
  import RippleLoader from "../../../assets/animation/RippleLoader.svelte";
  import { Text } from "../../../modules/state";
  import {
    UnivariateNote,
    UnivariateElementSelected,
    UnivariateFactorSelected,
    UnivariateFactors,
    UnivariateFactorsProgress,
  } from "../../../modules/state";
  import { format } from "../../../modules/functions";
  import type { FactorType } from "../../../modules/state";

  const select = (fac: FactorType) => {
    $UnivariateFactorSelected = fac;
    $UnivariateNote = fac.note;
  };

  $: ele = $UnivariateElementSelected;
  $: factors = ele
    ? $UnivariateFactors[`${ele.section}-${ele.code}`] || []
    : [];
  $: progress = ele
    ? $UnivariateFactorsProgress[`${ele.section}-${ele.code}`] || 0
    : 0;
</script>

<main>
  {#if factors.length}
    <div class="search"><Magnifier /><input type="text" /></div>
  {/if}
  <div class="list">
    {#each factors as fac}
      <button
        class="list__ele"
        on:click={() => select(fac)}
        class:selected={$UnivariateFactorSelected === fac}
      >
        <div class="list__ele__code">{fac.code}</div>
        <div class="list__ele__name">{fac.name}</div>
      </button>
    {/each}
  </div>
  {#if 0 < progress && progress < 1}
    <div class="progress">
      <div class="progress__bar"><ProgressBar {progress} /></div>
    </div>
  {:else if progress === 0 && ele}
    <div class="loader"><RippleLoader /></div>
    <div class="load-info">
      {format($Text.f_FactorLoadingInfo, { element: ele.code })}
    </div>
  {:else if progress === 0 && !ele}
    <div class="list-blank">{$Text.ElementsListBlank}</div>
  {/if}
</main>

<style>
  main {
    border-bottom: thin solid rgba(255, 255, 255, 0.2);
    position: relative;
  }
  .list-blank {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: rgba(255, 255, 255, 0.5);
  }
  .search {
    display: flex;
    align-items: center;
    padding-left: 0.8rem;
    height: 2.6rem;
    border-bottom: thin solid rgba(255, 255, 255, 0.2);
  }
  .search input {
    height: 100%;
    margin-left: 0.7rem;
    width: 90%;
    color: var(--white);
  }
  .list {
    margin: 1rem;
    height: 10.78rem;
    overflow: auto;
  }
  .list__ele {
    width: 100%;
    display: flex;
    align-items: center;
    padding: 0.5rem 0;
    border-radius: 0.35rem;
    border: thin solid rgba(255, 255, 255, 0);
    position: relative;
  }
  .list__ele.selected {
    border-color: rgba(255, 255, 255, 0.2);
  }
  .list__ele:hover {
    background-color: rgba(255, 255, 255, 0.07);
    cursor: pointer;
  }
  .list__ele__code {
    padding: 0.2rem 0.4rem;
    border-radius: 0.2rem;
    margin: 0 0.5rem;
    color: var(--white);
    background-color: rgba(255, 255, 255, 0.2);
  }
  .list__ele__name {
    color: var(--white);
  }
  .progress {
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .progress__bar {
    width: 93%;
    padding-bottom: 1rem;
  }
  .loader {
    position: absolute;
    display: flex;
    width: 100%;
    height: 100%;
    align-items: center;
    justify-content: center;
    bottom: 0;
    left: 0;
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
    padding-bottom: 9rem;
    color: var(--white);
  }
</style>
