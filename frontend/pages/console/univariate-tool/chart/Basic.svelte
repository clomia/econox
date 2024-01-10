<script lang="ts">
  import * as echarts from "echarts";
  import type { SourceType } from "../../../../modules/state";
  import { onMount } from "svelte";

  export let chartSource: SourceType;

  const option: echarts.EChartsOption = {
    dataset: {
      source: chartSource.original,
    },
    xAxis: { type: "time" },
    yAxis: { splitLine: { show: false } },
    series: [{ type: "scatter", symbolSize: 3, color: "white" }],
    tooltip: {
      formatter: (params: any) => {
        return "X: " + params.value[0] + "<br>Y: " + params.value[1];
      },
    },
  };

  let chartContainer: HTMLElement;
  let chart: echarts.ECharts;
  onMount(() => {
    chart = echarts.init(chartContainer);
    chart.setOption(option);
  });
</script>

<main>
  <div class="chart" bind:this={chartContainer}></div>
</main>

<style>
  .chart {
    width: 41rem;
    height: 22rem;
  }
</style>
