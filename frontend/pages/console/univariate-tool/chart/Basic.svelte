<script lang="ts">
  import * as echarts from "echarts";
  import { onMount } from "svelte";
  import { option } from "./config";
  import { Text } from "../../../../modules/state";
  import { wikiUrl } from "../../../../modules/wiki";
  import Toggle from "../../../../components/Toggle.svelte";
  import DownloadIcon from "../../../../assets/icon/DownloadIcon.svelte";
  import FullScreenIcon from "../../../../assets/icon/FullScreenIcon.svelte";
  import Download from "./Download.svelte";
  import FullScreen from "./FullScreen.svelte";
  import type { SourceType } from "../../../../modules/state";

  export let chartSource: SourceType;

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

  let normalized = false;
  let isMounted = false;
  let currentData = chartSource.original;

  onMount(() => (isMounted = true));

  $: if (isMounted && chartSource && !normalized) {
    currentData = chartSource.original;
    initChart(currentData);
  } else if (isMounted && chartSource && normalized) {
    currentData = chartSource.normalized;
    initChart(currentData);
  }

  let downloadWidget: boolean;
  let fullScreen: boolean;
</script>

{#if downloadWidget}
  <Download {normalized} on:close={() => (downloadWidget = false)} />
{/if}

{#if fullScreen}
  <FullScreen data={currentData} on:close={() => (fullScreen = false)} />
{/if}

<main>
  <button class="toggle" on:click={() => (normalized = !normalized)}>
    <Toggle value={normalized} />
  </button>
  <a
    class="toggle-text"
    class:emphasis={normalized}
    href={wikiUrl.normalize()}
    target="_blank"
    rel="noopener noreferrer"
  >
    {$Text.Normalize}
  </a>
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
  .toggle {
    position: absolute;
    left: 3.5rem;
    top: 0.9rem;
    z-index: 1;
  }
  .toggle-text {
    position: absolute;
    top: 0.2rem;
    left: 5.4rem;
    color: white;
    opacity: 0.4;
    font-size: 0.95rem;
    z-index: 1;
    text-decoration: none;
  }
  .toggle-text:hover {
    border-bottom: thin solid white;
    cursor: pointer;
  }
  .full-screen {
    position: absolute;
    right: 2.65rem;
    top: 0.3rem;
    opacity: 0.4;
    z-index: 1;
  }
  .full-screen:hover {
    opacity: 0.8;
    cursor: pointer;
  }
  .emphasis {
    opacity: 0.8;
  }
  .download {
    position: absolute;
    right: 2.5rem;
    bottom: 0.5rem;
    z-index: 1;
    fill: rgba(255, 255, 255, 0.4);
  }
  .download:hover {
    fill: rgba(255, 255, 255, 0.8);
    cursor: pointer;
  }
</style>
