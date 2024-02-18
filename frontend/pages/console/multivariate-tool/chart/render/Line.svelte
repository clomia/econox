<script lang="ts">
  import * as echarts from "echarts";
  import { onMount, onDestroy } from "svelte";
  import { getSrc } from "../../functions";
  import { generateOption } from "../options/line";
  import { FeatureGroupSelected } from "../../../../../modules/state";

  let chartContainer: HTMLElement;
  let src = null;
  let chart: echarts.ECharts | null = null;
  let chartOption = null;
  let srcGroupId: number;

  const updateChart = async () => {
    if ($FeatureGroupSelected.id !== srcGroupId) {
      // 그룹 변경
      src = null;
      const groupId = $FeatureGroupSelected.id;
      src = await getSrc(groupId, "original");
      srcGroupId = groupId;
    }
    chartOption = generateOption(src, $FeatureGroupSelected.id);
  };

  onMount(updateChart);
  onDestroy(() => chart?.dispose()); // 메모리 누수 방지

  $: if (chartContainer) {
    chart = echarts.init(chartContainer); // DOM이 생기면 차트 인스턴스 생성
    updateChart(); // 차트 인스턴스 생기면 차트 옵션 생성
  }
  $: if (chart && $FeatureGroupSelected) {
    // 기존 옵션이 있는 상태에서 특정 피쳐의 색상이 업데이트되면 옵션 객체도 업데이트
    // 혹은 피쳐 그룹 변경 시 변경된 그룹의 시계열 데이터를 로드해서 업데이트
    updateChart();
  }
  $: if (chart && chartOption) {
    // 옵션 변경사항을 차트에 반영
    chart.setOption(chartOption);
  }
</script>

<main>
  {#if src}
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
</style>
