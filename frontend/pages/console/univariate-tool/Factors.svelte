<script lang="ts">
  import Magnifier from "../../../assets/icon/Magnifier.svelte";
  import { Text } from "../../../modules/state";
  import {
    UnivariateNote,
    UnivariateFactors,
    UnivariateElementSelected,
    UnivariateFactorSelected,
  } from "../../../modules/state";
  import type { ElementType, FactorType } from "../../../modules/state";

  const select = (fac: FactorType) => {
    $UnivariateFactorSelected = fac;
    $UnivariateNote = fac.note;
  };

  let scrolled = false;
  const scrollHandler = () => {
    scrolled = true;
  };

  $: ele = $UnivariateElementSelected;
  $: factors = ele ? $UnivariateFactors[`${ele.section}-${ele.code}`] || [] : [];
</script>

<main>
  {#if factors.length}
    <div class="search"><Magnifier /><input type="text" /></div>
  {/if}
  <div class="list" on:scroll={scrollHandler}>
    {#each factors as fac}
      <button
        class="list__ele"
        on:click={() => select(fac)}
        class:selected={$UnivariateFactorSelected === fac}
      >
        <div class="list__ele__code">{fac.code}</div>
        <div class="list__ele__name">{fac.name}</div>
      </button>
    {:else}
      <div class="list-blank">{$Text.ElementsListBlank}</div>
    {/each}
  </div>
  {#if !scrolled && factors.length > 4}
    <div class="scroll-guide">스크롤하여 더보기</div>
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
  .scroll-guide {
    position: absolute;
    bottom: 0;
    display: flex;
    width: 100%;
    justify-content: center;
    align-items: start;
    color: var(--white);
    background-color: rgba(0, 0, 0, 0.2);
    padding: 0.15rem 0;
  }
</style>
