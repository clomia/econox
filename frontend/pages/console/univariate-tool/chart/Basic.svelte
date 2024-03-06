<script lang="ts">
  import * as echarts from "echarts";
  import { onMount } from "svelte";
  import { option } from "./config";
  import DownloadIcon from "../../../../assets/icon/DownloadIcon.svelte";
  import FullScreenIcon from "../../../../assets/icon/FullScreenIcon.svelte";
  import Download from "./Download.svelte";
  import FullScreen from "./FullScreen.svelte";
  import {
    UnivariateElementSelected,
    UnivariateFactorSelected,
  } from "../../../../modules/state";

  export let chartSource: [string, string | number][];

  let chartContainer: HTMLElement;
  let chart: echarts.ECharts;

  const initChart = (source: [string, string | number][]) => {
    chart?.dispose();
    chart = echarts.init(chartContainer);
    chart.setOption({
      ...option({ bar: false, scatter: false, line: true, area: false }),
      dataset: { source },
    });
  };

  let isMount = false;
  onMount(() => (isMount = true));
  $: if (isMount && chartSource) {
    // 차트 소스가 바뀌면 다시 렌더링해줘야 함
    initChart(chartSource);
  }

  let downloadWidget: boolean;
  let fullScreen: boolean;
</script>

{#if downloadWidget}
  <Download
    elementSection={$UnivariateElementSelected.section}
    elementCode={$UnivariateElementSelected.code}
    factorSection={$UnivariateFactorSelected.section.code}
    factorCode={$UnivariateFactorSelected.code}
    on:close={() => (downloadWidget = false)}
  />
{/if}

{#if fullScreen}
  <FullScreen data={chartSource} on:close={() => (fullScreen = false)} />
{/if}

<main>
  <button class="download" on:click={() => (downloadWidget = true)}>
    <DownloadIcon />
  </button>
  <button class="full-screen" on:click={() => (fullScreen = true)}>
    <FullScreenIcon />
  </button>
  <div class="chart" bind:this={chartContainer}></div>
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
  .full-screen {
    position: absolute;
    right: 2.65rem;
    top: 0.3rem;
    opacity: 0.4;
    z-index: 11;
  }
  .full-screen:hover {
    opacity: 0.8;
    cursor: pointer;
  }
  .download {
    position: absolute;
    right: 2.5rem;
    bottom: 0.5rem;
    z-index: 11;
    fill: rgba(255, 255, 255, 0.4);
  }
  .download:hover {
    fill: rgba(255, 255, 255, 0.8);
    cursor: pointer;
  }
</style>
