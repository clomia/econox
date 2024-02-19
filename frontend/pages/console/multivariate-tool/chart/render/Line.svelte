<script lang="ts">
  import * as echarts from "echarts";
  import { onMount, onDestroy } from "svelte";
  import Toggle from "../../../../../components/Toggle.svelte";
  import { generateOption } from "../options/line";
  import {
    FeatureGroupSelected,
    FgTsOrigin,
    FgTsScaled,
    FgStoreState,
  } from "../../../../../modules/state";

  let chart: echarts.ECharts | null = null;
  let chartContainer: HTMLElement;
  let chartOption = null;
  let scaled: boolean = false;

  onMount(() => (chart = echarts.init(chartContainer)));
  onDestroy(() => chart?.dispose()); // 메모리 누수 방지

  $: group = $FeatureGroupSelected; // shortcut
  $: ready = $FgStoreState[group.id].FgTsOrigin === "after";
  $: if (group && ready && scaled === true) {
    chartOption = generateOption($FgTsScaled[group.id], group.id);
  } else if (group && ready && scaled === false) {
    chartOption = generateOption($FgTsOrigin[group.id], group.id);
  }
  $: if (chart && chartOption) {
    chart.setOption(chartOption);
  }
</script>

<main>
  {#if chartOption}
    {#if !ready}
      <div style="color: white;">최신 데이터로 업데이트중입니다...</div>
    {/if}
    <button class="toggle" on:click={() => (scaled = !scaled)}>
      <Toggle value={scaled} />
    </button>
    <div class="chart" bind:this={chartContainer}></div>
  {:else}
    로딩중!!
  {/if}
</main>

<style>
  main {
    position: relative;
  }
  .chart {
    width: 46rem;
    height: 23rem;
    padding-right: 2rem;
  }
  .toggle {
    position: absolute;
    left: 3.5rem;
    top: 0.9rem;
    z-index: 1;
  }
</style>
