<script lang="ts">
  import * as echarts from "echarts";
  import { onDestroy } from "svelte";
  import Toggle from "../../../../../components/Toggle.svelte";
  import { generateOption } from "../options/line";
  import {
    FeatureGroupSelected,
    FgTsOrigin,
    FgTsScaled,
    FgStoreState,
  } from "../../../../../modules/state";
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
    {#if !ready}
      <div style="color: white;">최신 데이터로 업데이트중입니다...</div>
    {/if}
    <button class="toggle" on:click={() => (scaled = !scaled)}>
      <Toggle value={scaled} />
    </button>
    <div class="chart" bind:this={chartContainer}></div>
  {:else}
    로딩중!!
  {/if}
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
</style>
