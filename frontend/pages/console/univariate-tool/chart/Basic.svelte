<script lang="ts">
  import * as echarts from "echarts";
  import type { SourceType } from "../../../../modules/state";
  import { onMount } from "svelte";

  export let chartSource: SourceType;

  let chartContainer: HTMLElement;
  let chart: echarts.ECharts;
  onMount(() => {
    chart = echarts.init(chartContainer);
    console.log(chart, chartSource);
  });
</script>

<main>
  <div class="chart" bind:this={chartContainer}></div>
</main>

<style>
</style>
