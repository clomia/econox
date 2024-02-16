<script lang="ts">
  import * as echarts from "echarts";
  import { onMount } from "svelte";
  import { getSrc } from "../../functions";
  import { generateOption } from "../options/line";
  import { FeatureGroupSelected } from "../../../../../modules/state";

  let chartContainer: HTMLElement;
  let src = null;
  let chart: echarts.ECharts | null = null;
  let chartOption = null;

  onMount(
    // 데이터를 불러와서 src로 할당
    async () => (src = await getSrc($FeatureGroupSelected.id, "original"))
  );
  $: if (chartContainer) {
    // DOM이 생기면 차트 인스턴스 생성
    chart = echarts.init(chartContainer);
  }
  $: if (chart) {
    // 차트 인스턴스 생기면 차트 옵션 생성
    chartOption = generateOption(src, $FeatureGroupSelected.id);
  }
  $: if (chartOption && $FeatureGroupSelected) {
    // 기존 옵션이 있는 상태에서 특정 피쳐의 색상이 업데이트되면 옵션 객체도 업데이트
    const option = generateOption(src, $FeatureGroupSelected.id);
    chart.setOption(option);
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
