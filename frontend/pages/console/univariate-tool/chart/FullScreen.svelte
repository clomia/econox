<script lang="ts">
  import * as echarts from "echarts";
  import { createEventDispatcher, onMount } from "svelte";
  import CloseButton from "../../../../components/CloseButton.svelte";
  import { option } from "./config";

  export let data: [string, string | number][];

  let chartContainer: HTMLElement;
  let chart: echarts.ECharts;

  const initChart = (source: [string, string | number][]) => {
    chart?.dispose();
    chart = echarts.init(chartContainer);
    chart.setOption({
      ...option({ bar: false, scatter: false, line: true, area: false }),
      dataset: { source },
    });
    // 아무런 범례도 선택되지 않은 경우 restore 수행
    chart.on("legendselectchanged", (event: any) => {
      const selected = event.selected;
      if (Object.keys(selected).every((key) => !selected[key])) {
        chart.dispatchAction({ type: "restore" });
      }
    });
  };

  onMount(() => {
    initChart(data);
    window.onresize = chart.resize;
    document.body.style.overflow = "hidden";
  });

  const dispatch = createEventDispatcher();
  const close = () => {
    window.onresize = null;
    document.body.style.overflow = "";
    dispatch("close");
  };
</script>

<div class="membrane">
  <button class="close" on:click={close}><CloseButton /></button>
  <div class="chart" bind:this={chartContainer}></div>
</div>

<style>
  .membrane {
    position: fixed;
    width: 100vw;
    height: 100vh;
    top: 0;
    left: 0;
    z-index: 20;
    background: var(--background);
    display: flex;
    justify-content: center;
    align-items: center;
  }
  .close {
    position: absolute;
    top: 1.5rem;
    right: 2rem;
    z-index: 21;
  }
  .chart {
    width: 100%;
    height: 100%;
    padding-top: 2rem;
    padding-right: 2rem;
    padding-bottom: 2rem;
  }
</style>
