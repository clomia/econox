<script lang="ts">
  import * as echarts from "echarts";
  import { onDestroy } from "svelte";
  import BouncingCubeLoader from "../../../../../assets/animation/BouncingCubeLoader.svelte";
  import { generateOption } from "../options/granger";
  import {
    FeatureGroupSelected,
    FgTsRatio,
    FgStoreState,
  } from "../../../../../modules/state";
  import { isSameArray } from "../../../../../modules/functions";

  let chart: echarts.ECharts | null = null;
  let chartContainer: HTMLElement;
  let chartOption = null;

  onDestroy(() => chart?.dispose()); // 메모리 누수 방지

  $: group = $FeatureGroupSelected; // shortcut
  $: ready = $FgStoreState[group.id].FgTsRatio === "after";
  $: columns = $FgTsRatio[group.id] ? $FgTsRatio[group.id][0] : [];

  $: if (group && ready) {
    chartOption = generateOption([], [], []);
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
</style>
