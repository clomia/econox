<script lang="ts">
  import Magnifier from "../../../assets/icon/Magnifier.svelte";
  import ProgressBar from "../../../components/ProgressBar.svelte";
  import RippleLoader from "../../../assets/animation/RippleLoader.svelte";
  import { Text } from "../../../modules/state";
  import {
    UnivariateElementSelected,
    UnivariateFactorSelected,
    UnivariateFactors,
    UnivariateFactorsProgress,
  } from "../../../modules/state";
  import { format } from "../../../modules/functions";
  import { setChartSource } from "./functions";
  import { attrQuerySort } from "../../../modules/functions";
  import type { FactorType } from "../../../modules/state";

  const select = async (fac: FactorType) => {
    $UnivariateFactorSelected = fac;
    if (
      // for typescript
      $UnivariateElementSelected?.code &&
      $UnivariateElementSelected?.section
    ) {
      await setChartSource(
        $UnivariateElementSelected.code,
        $UnivariateElementSelected.section,
        fac.code,
        fac.section.code
      );
    }
  };

  $: ele = $UnivariateElementSelected;
  $: factors = ele
    ? $UnivariateFactors[`${ele.section}-${ele.code}`] || []
    : [];
  $: progress = ele
    ? $UnivariateFactorsProgress[`${ele.section}-${ele.code}`] || 0
    : 0;

  let query = "";
  let attr: string | string[] = "name";
  let view: any[] = [];

  $: if (query) {
    view = attrQuerySort(factors, query, attr);
  } else {
    view = factors;
  }
  $: attrBtnText = attr === "name" ? $Text.Name : $Text.Section;

  const searchAttrChange = () => {
    if (attr === "name") {
      attr = ["section", "name"];
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
    {#each view as fac}
      <button
        class="list__fac"
        on:click={() => select(fac)}
        class:selected={$UnivariateFactorSelected === fac}
        class:list__ele_with_scroll={view.length >= 6}
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
    border-top: thin solid rgba(255, 255, 255, 0.2);
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
    min-height: 10.78rem;
    max-height: 16rem;
    overflow: auto;
  }
  .list__fac {
    width: 100%;
    display: flex;
    align-items: center;
    text-align: start;
    border: thin solid rgba(255, 255, 255, 0);
    position: relative;
  }
  .list__ele_with_scroll {
    width: 98%;
  }
  .list__fac.selected {
    border-color: rgba(255, 255, 255, 0.2);
  }
  .list__fac:hover {
    background-color: rgba(255, 255, 255, 0.07);
    cursor: pointer;
  }
  .list__fac__section {
    margin: 0.5rem;
    padding: 0.2rem 0.4rem;
    border-radius: 0.15rem;
    color: var(--white);
    background-color: #613a55;
  }
  .list__fac__name {
    margin: 0.5rem;
    padding: 0.2rem 0.4rem;
    border-radius: 0.15rem;
    color: var(--white);
    background-color: #40533e;
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
    padding-bottom: 8.5rem;
    color: rgba(255, 255, 255, 0.6);
  }
</style>
