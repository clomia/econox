<script lang="ts">
  import * as echarts from "echarts";
  import { onMount } from "svelte";
  import { option } from "./config";
  import { Text } from "../../../../modules/state";
  import { wikiUrl } from "../../../../modules/wiki";
  import Toggle from "../../../../components/Toggle.svelte";
  import Download from "../../../../assets/icon/Download.svelte";
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

  onMount(() => (isMounted = true));

  $: if (isMounted && chartSource && !normalized) {
    initChart(chartSource.original);
  } else if (isMounted && chartSource && normalized) {
    initChart(chartSource.normalized);
  }
</script>

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
  <button class="download">
    <Download />
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
    z-index: 1;
  }
  .toggle-text {
    position: absolute;
    left: 2.8rem;
    top: -0.17rem;
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
  .emphasis {
    opacity: 0.8;
  }
  .download {
    position: absolute;
    right: 0.5rem;
    bottom: 0.5rem;
    z-index: 1;
    fill: rgba(255, 255, 255, 0.4);
  }
  .download:hover {
    fill: rgba(255, 255, 255, 0.8);
    cursor: pointer;
  }
</style>
