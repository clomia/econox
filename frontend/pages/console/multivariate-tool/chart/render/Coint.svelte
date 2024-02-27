<script lang="ts">
  import * as echarts from "echarts";
  import { onDestroy } from "svelte";
  import BouncingCubeLoader from "../../../../../assets/animation/BouncingCubeLoader.svelte";
  import { generateOption } from "../options/coint";
  import {
    FeatureGroupSelected,
    FgCoint,
    FgStoreState,
  } from "../../../../../modules/state";

  let chart: echarts.ECharts | null = null;
  let chartContainer: HTMLElement;
  let chartOption = null;

  onDestroy(() => chart?.dispose()); // 메모리 누수 방지

  $: group = $FeatureGroupSelected; // shortcut
  $: ready = $FgStoreState[group.id].FgCoint === "after";

  $: if (group && ready) {
    chartOption = generateOption($FgCoint[group.id], group.id);
  }
  $: if (chartContainer) {
    chart = echarts.init(chartContainer); // chartContainer 바운드 되면 차트 인스턴스 생성
  }

  $: if (chart && chartOption) {
    chart.setOption(chartOption);
  }
</script>

<main>
  {#if chartOption}
    <div class="chart-background" />
    <div class="chart" bind:this={chartContainer}></div>
  {:else}
    <div class="loading">
      <BouncingCubeLoader backgroundColor="#ff8181" borderColor="#5e4141" />
    </div>
  {/if}
</main>

<style>
  main {
    position: relative;
  }
  .loading {
    height: 17rem;
    padding-top: 2rem;
  }
  .chart-background {
    height: 31rem;
  }
  .chart {
    position: absolute;
    width: 40rem;
    height: 28rem;
    left: 2rem;
    top: 1rem;
  }
</style>
