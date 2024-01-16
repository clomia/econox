<script lang="ts">
  import * as echarts from "echarts";
  import { onMount } from "svelte";
  import { option } from "./config";
  import Toggle from "../../../../components/Toggle.svelte";
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

  let value = false;
  $: value, console.log(value);
</script>

<main>
  <button class="toggle" on:click={() => (value = !value)}>
    <Toggle {value} />
  </button>
  <div class="chart" bind:this={chartContainer}></div>
</main>

<style>
  main {
    position: relative;
  }
  .chart {
    width: 41rem;
    height: 22rem;
  }
  .toggle {
    position: absolute;
    left: 1rem;
    top: 0.5rem;
  }
</style>
