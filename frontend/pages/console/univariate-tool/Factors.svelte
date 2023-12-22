<script lang="ts">
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
  import { attrQuerySort } from "./functions";
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

  let query = "";
  let attr = "name";
  let view: any[] = [];

  $: if (query) {
    view = attrQuerySort(factors, query, attr);
  } else {
    view = factors;
  }
  $: attrBtnText = attr === "name" ? $Text.Name : $Text.Section;

  const searchAttrChange = () => {
    if (attr === "name") {
      attr = "section";
    } else {
      attr = "name";
    }
  };
  const searchEventHandler = (event: any) => {
    const inputElement = event.target as HTMLInputElement;
    query = inputElement.value;
  };
</script>

<main>
  {#if factors.length}
    <div class="search">
      <Magnifier />
      <button class="search__attr-btn" on:click={searchAttrChange}
        >{attrBtnText}</button
      >
      <input class="search__input" type="text" on:input={searchEventHandler} />
    </div>
  {/if}
  <div class="list">
    {#each factors as fac}
      <button
        class="list__fac"
        on:click={() => select(fac)}
        class:selected={$UnivariateFactorSelected === fac}
      >
        <div class="list__fac__section">{fac.section.name}</div>
        <div class="list__fac__name">{fac.name}</div>
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
    <div class="list-blank">{$Text.FactorsListBlank}</div>
  {/if}
</main>

<style>
  main {
    position: relative;
  }
  .list-blank {
    position: absolute;
    bottom: 0;
    left: 0;
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
  .search__input {
    height: 100%;
    margin-left: 0.7rem;
    width: 83%;
    color: var(--white);
  }
  .search__attr-btn {
    margin-left: 0.7rem;
    padding: 0.2rem 0.5rem;
    border-radius: 0.2rem;
    background-color: rgba(255, 255, 255, 0.08);
    color: var(--white);
  }
  .search__attr-btn:hover {
    background-color: rgba(255, 255, 255, 0.18);
    cursor: pointer;
  }
  .list {
    margin: 1rem;
    height: 10.78rem;
    overflow: auto;
  }
  .list__fac {
    width: 100%;
    display: flex;
    align-items: center;
    padding: 0.5rem 0;
    border-radius: 0.35rem;
    border: thin solid rgba(255, 255, 255, 0);
    position: relative;
  }
  .list__fac.selected {
    border-color: rgba(255, 255, 255, 0.2);
  }
  .list__fac:hover {
    background-color: rgba(255, 255, 255, 0.07);
    cursor: pointer;
  }
  .list__fac__section {
    padding: 0.2rem 0.4rem;
    border-radius: 0.2rem;
    margin: 0 0.5rem;
    color: var(--white);
    background-color: rgba(255, 255, 255, 0.2);
  }
  .list__fac__name {
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
