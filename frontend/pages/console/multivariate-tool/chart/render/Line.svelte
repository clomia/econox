<script lang="ts">
  import * as echarts from "echarts";
  import { onDestroy } from "svelte";
  import Toggle from "../../../../../components/Toggle.svelte";
  import { generateOption } from "../options/line";
  import {
    Text,
    FeatureGroupSelected,
    FgTsOrigin,
    FgTsScaled,
    FgStoreState,
  } from "../../../../../modules/state";
  import { wikiUrl } from "../../../../../modules/wiki";
  import { isSameArray } from "../../../../../modules/functions";

  let chart: echarts.ECharts | null = null;
  let chartContainer: HTMLElement;
  let chartOption = null;
  let scaled: boolean = false;

  onDestroy(() => chart?.dispose()); // 메모리 누수 방지

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
</script>

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
    로딩중!!
  {/if}
</main>

<style>
  main {
    position: relative;
  }
  .chart-background {
    height: 31rem;
  }
  .chart {
    position: absolute;
    width: 47rem;
    height: 28rem;
    left: -0.8rem;
    top: 0.5rem;
  }
  .toggle {
    position: absolute;
    left: 2.5rem;
    top: -1rem;
    z-index: 1;
  }
  .toggle-text {
    position: absolute;
    top: -1.7rem;
    left: 4.4rem;
    color: white;
    opacity: 0.4;
    font-size: 0.9rem;
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
</style>
