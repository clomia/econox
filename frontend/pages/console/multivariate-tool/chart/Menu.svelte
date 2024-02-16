<script lang="ts">
  import {
    FeatureGroups,
    FeatureGroupSelected,
  } from "../../../../modules/state";

  const changeChartType = (chartType: string) => {
    const group = $FeatureGroupSelected;
    if (group.chart_type === chartType) {
      return; // 변경사항이 없으면 패스
    }
    const idx = $FeatureGroups.findIndex(
      (group) => group.id === $FeatureGroupSelected.id
    );
    group.chart_type = chartType;
    $FeatureGroups[idx] = group;
    $FeatureGroupSelected = group;
  };
</script>

<main>
  <button on:click={() => changeChartType("line")}>라인차트</button>
  <button on:click={() => changeChartType("ratio")}>비율차트</button>

  <div class="test-monitor">
    <div>이것은 메뉴입니다</div>
    <div style="color: white;">
      현재 선택된 차트 타입: {$FeatureGroupSelected.chart_type}
    </div>
  </div>
</main>

<style>
  main {
    border-top: thin solid rgba(255, 255, 255, 0.4);
  }
  button {
    width: 10rem;
    height: 3rem;
    color: white;
    background-color: brown;
  }
  button:hover {
    cursor: pointer;
    background-color: black;
  }
  .test-monitor {
    display: flex;
    width: 100%;
    justify-content: space-around;
  }
</style>
