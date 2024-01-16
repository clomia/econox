<script lang="ts">
  import * as echarts from "echarts";
  import { onMount } from "svelte";
  import { option } from "./config";
  import type { SourceType } from "../../../../modules/state";

  export let chartSource: SourceType;

  let chartContainer: HTMLElement;
  let chart: echarts.ECharts;

  const initChart = () => {
    chart?.dispose();
    chart = echarts.init(chartContainer);
    chart.setOption({
      ...option,
      dataset: {
        source: chartSource.original,
      },
    });
    // 아무런 범례도 선택되지 않은 경우 restore 수행
    chart.on("legendselectchanged", (event: any) => {
      const selected = event.selected;
      if (Object.keys(selected).every((key) => !selected[key])) {
        chart.dispatchAction({ type: "restore" });
      }
    });
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
