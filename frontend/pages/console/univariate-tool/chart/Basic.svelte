<script lang="ts">
  import * as echarts from "echarts";
  import { onMount } from "svelte";
  import type { SourceType } from "../../../../modules/state";

  export let chartSource: SourceType;

  let chartContainer: HTMLElement;
  let chart: echarts.ECharts;

  const initChart = () => {
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
    chart?.dispose();
    chart = echarts.init(chartContainer);
    chart.setOption(option);
  };

  let isMounted = false;
  onMount(() => {
    isMounted = true;
    initChart();
  });
  $: if (isMounted && chartSource) {
    initChart();
  }
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
