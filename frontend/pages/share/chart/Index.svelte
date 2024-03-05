<script lang="ts">
  import { onMount } from "svelte";
  import * as echarts from "echarts";
  import { Text } from "../../../modules/state";
  import Toggle from "../../../components/Toggle.svelte";
  import CloseButton from "../../../components/CloseButton.svelte";
  import FullScreenIcon from "../../../assets/icon/FullScreenIcon.svelte";
  import { wikiUrl } from "../../../modules/wiki";
  import { generateOption as cointChart } from "./options/coint";
  import { generateOption as grangerChart } from "./options/granger";
  import { generateOption as ratioChart } from "./options/ratio";
  import { original, scaled } from "./options/line";
  import type { PublicFgRespType } from "../function";

  export let data: PublicFgRespType;

  let option: string;
  let chart: echarts.ECharts;
  let chartContainer: HTMLElement;

  let fullScreenChart: echarts.ECharts | null = null;
  let fullScreenChartContainer: HTMLElement;

  let chartName: string;
  let chartDescription: string;

  let fullScreen = false;

  const optionGeneraterMap = {
    lineOrigin: original,
    lineScaled: scaled,
    ratio: ratioChart,
    granger: grangerChart,
    coint: cointChart,
  };

  if (data.feature_group.chart_type === "line") {
    option = "lineOrigin";
  } else {
    option = data.feature_group.chart_type;
  }

  switch (data.feature_group.chart_type) {
    case "line":
      chartName = $Text.FgLineChart_Name;
      chartDescription = $Text.FgLineChart_Description;
      break;
    case "ratio":
      chartName = $Text.FgRatioChart_Name;
      chartDescription = $Text.FgRatioChart_Description;
      break;
    case "granger":
      chartName = $Text.FgGrangerChart_Name;
      chartDescription = $Text.FgGrangerChart_Description;
      break;
    case "coint":
      chartName = $Text.FgCointChart_Name;
      chartDescription = $Text.FgCointChart_Description;
      break;
  }

  const lineScaleToggle = () => {
    if (option === "lineOrigin") {
      option = "lineScaled";
    } else if (option === "lineScaled") {
      option = "lineOrigin";
    }
  };

  onMount(() => {
    chart = echarts.init(chartContainer);
  });

  $: if (chart && option) {
    chart.setOption(optionGeneraterMap[option](data), true);
  }

  $: if (fullScreenChartContainer) {
    fullScreenChart = echarts.init(fullScreenChartContainer);
    fullScreenChart.setOption(optionGeneraterMap[option](data), true);
    window.onresize = fullScreenChart.resize;
    document.body.style.overflow = "hidden";
  } else if (fullScreenChart) {
    window.onresize = null;
    document.body.style.overflow = "";
    fullScreenChart.dispose();
  }
</script>

<section class="note">
  <button on:click={() => (fullScreen = true)} class="fullscreen-btn">
    <FullScreenIcon />
  </button>
  <div class="note__chart-name">{chartName}</div>
  <div class="note__chart-desc">{chartDescription}</div>
</section>

<main>
  {#if data.feature_group.chart_type === "line"}
    <button class="toggle" on:click={lineScaleToggle}>
      <Toggle value={option === "lineScaled"} />
    </button>
    <a
      class="toggle-text"
      class:emphasis={option === "lineScaled"}
      href={wikiUrl.scaling()}
      target="_blank"
      rel="noopener noreferrer"
    >
      Min-Max Scaling
    </a>
  {/if}
  <div class="chart" bind:this={chartContainer} />
</main>

{#if fullScreen}
  <div class="full-screen">
    <button class="full-screen__close" on:click={() => (fullScreen = false)}>
      <CloseButton />
    </button>
    {#if data.feature_group.chart_type === "line"}
      <button class="full-screen__toggle" on:click={lineScaleToggle}>
        <Toggle value={option === "lineScaled"} />
      </button>
      <a
        class="full-screen__toggle-text"
        class:emphasis={option === "lineScaled"}
        href={wikiUrl.scaling()}
        target="_blank"
        rel="noopener noreferrer"
      >
        Min-Max Scaling
      </a>
    {/if}
    <div class="full-screen__chart" bind:this={fullScreenChartContainer}></div>
  </div>
{/if}

<style>
  .note {
    width: 44rem;
    color: var(--white);
    padding: 1rem;
    position: relative;
  }
  .note__chart-name {
    text-align: center;
    font-size: 1.2rem;
    margin-bottom: 1.3rem;
  }
  .note__chart-desc {
    text-align: start;
  }

  main {
    position: relative;
    padding-bottom: 1rem;
    border-bottom: thin solid rgba(255, 255, 255, 0.35);
  }
  .toggle {
    position: absolute;
    left: 3rem;
    top: 1.2rem;
    z-index: 1;
  }
  .toggle-text {
    position: absolute;
    top: 0.5rem;
    left: 5rem;
    color: white;
    opacity: 0.4;
    font-size: 0.9rem;
    z-index: 1;
    text-decoration: none;
  }
  .toggle-text:hover,
  .full-screen__toggle-text:hover {
    border-bottom: thin solid white;
    cursor: pointer;
  }
  .full-screen__toggle {
    position: absolute;
    left: 8rem;
    top: 3.1rem;
    z-index: 1;
  }
  .full-screen__toggle-text {
    position: absolute;
    top: 2.4rem;
    left: 10rem;
    color: white;
    opacity: 0.4;
    font-size: 0.9rem;
    z-index: 1;
    text-decoration: none;
  }

  .emphasis {
    opacity: 0.8;
  }
  .chart {
    width: 44rem;
    height: 28rem;
  }

  .fullscreen-btn {
    position: absolute;
    top: 1rem;
    right: 0.2rem;
    opacity: 0.5;
  }
  .fullscreen-btn:hover {
    cursor: pointer;
    opacity: 1;
  }

  .full-screen {
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
  .full-screen__close {
    position: absolute;
    top: 1.5rem;
    right: 2rem;
    z-index: 21;
  }
  .full-screen__chart {
    width: 100%;
    height: 100%;
    padding: 2rem;
  }
</style>
