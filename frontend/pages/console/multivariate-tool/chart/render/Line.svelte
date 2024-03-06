<script lang="ts">
  import * as echarts from "echarts";
  import { onDestroy } from "svelte";
  import Toggle from "../../../../../components/Toggle.svelte";
  import BouncingCubeLoader from "../../../../../assets/animation/BouncingCubeLoader.svelte";
  import CloseButton from "../../../../../components/CloseButton.svelte";
  import { generateOption } from "../options/line";
  import {
    FeatureGroupSelected,
    FgTsOrigin,
    FgTsScaled,
    FgStoreState,
    FgChartFullScreen,
  } from "../../../../../modules/state";
  import { wikiUrl } from "../../../../../modules/wiki";
  import { isSameArray } from "../../../../../modules/functions";

  let chartOption = null;

  let chart: echarts.ECharts | null = null;
  let chartContainer: HTMLElement;
  let fullScreenChart: echarts.ECharts | null = null;
  let fullScreenChartContainer: HTMLElement;

  let scaled: boolean = false;

  onDestroy(() => {
    chart?.dispose();
    fullScreenChart?.dispose();
  }); // 메모리 누수 방지

  $: group = $FeatureGroupSelected; // shortcut
  $: ready = $FgStoreState[group.id].FgTsOrigin === "after";
  $: columns = $FgTsOrigin[group.id] ? $FgTsOrigin[group.id][0] : [];

  $: if (group && ready && scaled === true) {
    chartOption = generateOption($FgTsScaled[group.id], group.id);
  } else if (group && ready && scaled === false) {
    chartOption = generateOption($FgTsOrigin[group.id], group.id);
  }
  $: if (chartContainer) {
    chart = echarts.init(chartContainer); // chartContainer 바운드 되면 차트 인스턴스 생성
  }

  let beforeColumns: string[];
  $: if (chart && chartOption) {
    let afterColumns = [...columns];
    if (!beforeColumns) {
      // 첫 실행, 초기화
      beforeColumns = [...afterColumns];
    }
    if (isSameArray(beforeColumns, afterColumns)) {
      // 차트 구성만 변경된 경우 변경 사항만 병합
      chart.setOption(chartOption);
    } else {
      // 데이터셋이 변경된 경우 전체 옵션 재할당
      chart.setOption(chartOption, true);
    }
    beforeColumns = [...afterColumns];
  }

  $: if (fullScreenChartContainer && chartOption) {
    document.body.style.overflow = "hidden";
    // 전체화면을 켜서 컨테이너가 바인드되면 차트 인스턴스 생성
    fullScreenChart = echarts.init(fullScreenChartContainer);
    fullScreenChart.setOption(chartOption);
    window.onresize = fullScreenChart.resize;
  }
  $: if (!$FgChartFullScreen) {
    window.onresize = null;
    document.body.style.overflow = "";
    // 전체화면을 끄면 차트 인스턴스 삭제
    fullScreenChart?.dispose();
  }
</script>

{#if chartOption && $FgChartFullScreen}
  <div class="full-screen">
    <button
      class="full-screen__close"
      on:click={() => ($FgChartFullScreen = false)}
    >
      <CloseButton />
    </button>
    <div class="full-screen__toggle">
      <button
        class="full-screen__toggle__btn"
        on:click={() => (scaled = !scaled)}
      >
        <Toggle value={scaled} />
      </button>
      <a
        class="full-screen__toggle__text"
        class:emphasis={scaled}
        href={wikiUrl.scaling()}
        target="_blank"
        rel="noopener noreferrer"
      >
        Min-Max Scaling
      </a>
    </div>
    <div class="full-screen__chart" bind:this={fullScreenChartContainer}></div>
  </div>
{/if}

<main>
  {#if chartOption}
    <button class="toggle" on:click={() => (scaled = !scaled)}>
      <Toggle value={scaled} />
    </button>
    <a
      class="toggle-text"
      class:emphasis={scaled}
      href={wikiUrl.scaling()}
      target="_blank"
      rel="noopener noreferrer"
    >
      Min-Max Scaling
    </a>
    <div class="chart-background" />
    <div class="chart" bind:this={chartContainer}></div>
  {:else}
    <div class="loading">
      <BouncingCubeLoader backgroundColor="#ff8181" borderColor="#5e4141" />
    </div>
  {/if}
</main>

<style>
  main {
    position: relative;
  }
  .loading {
    height: 17rem;
    padding-top: 2rem;
  }
  .chart-background {
    height: 31rem;
  }
  .chart {
    position: absolute;
    width: 47rem;
    height: 28rem;
    left: -0.8rem;
    top: 1rem;
  }
  .toggle {
    position: absolute;
    left: 2.5rem;
    top: -1rem;
    z-index: 11;
  }
  .toggle-text {
    position: absolute;
    top: -1.7rem;
    left: 4.4rem;
    color: white;
    opacity: 0.4;
    font-size: 0.9rem;
    z-index: 11;
    text-decoration: none;
  }
  .toggle-text:hover {
    border-bottom: thin solid white;
    cursor: pointer;
  }
  .emphasis {
    opacity: 0.8;
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
    padding: 2rem 0;
  }
  .full-screen__toggle {
    position: absolute;
    top: 2.2rem;
    right: 6.5rem;
    z-index: 21;
  }
  .full-screen__toggle__text {
    color: white;
    opacity: 0.4;
    font-size: 0.9rem;
    text-decoration: none;
    margin-left: 10.3rem;
  }
  .full-screen__toggle__text:hover {
    border-bottom: thin solid white;
    cursor: pointer;
  }
</style>
