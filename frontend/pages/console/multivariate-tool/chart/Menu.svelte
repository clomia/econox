<script lang="ts">
  import PinIcon from "../../../../assets/icon/PinIcon.svelte";
  import LineChartIcon from "../../../../assets/icon/LineChartIcon.svelte";
  import PieChartIcon from "../../../../assets/icon/PieChartIcon.svelte";
  import GrangerChartIcon from "../../../../assets/icon/GrangerChartIcon.svelte";
  import CointChartIcon from "../../../../assets/icon/CointChartIcon.svelte";
  import { chartSelectedHandler } from "../functions";
  import {
    FeatureGroups,
    FeatureGroupSelected,
    FgDefaultChartType,
  } from "../../../../modules/state";

  $: group = $FeatureGroupSelected; // shortcut

  const changeChartType = async (chartType: string) => {
    const _group = { ...group };
    if (_group.chart_type === chartType) {
      return; // 변경사항이 없으면 패스
    }
    const idx = $FeatureGroups.findIndex((g) => g.id === _group.id);
    _group.chart_type = chartType;
    $FeatureGroups[idx] = _group;
    $FeatureGroupSelected = _group;
    await chartSelectedHandler(_group);
  };
</script>

<main>
  <div class="chart-type">
    <div class="chart-type__pin" class:selected={group.chart_type === "line"}>
      {#if $FgDefaultChartType[group.id] === "line"}
        <PinIcon />
      {/if}
    </div>
    <button
      class:selected={group.chart_type === "line"}
      on:click={() => changeChartType("line")}
    >
      <LineChartIcon size="2.3rem" />
    </button>
  </div>
  <div class="chart-type">
    <div class="chart-type__pin" class:selected={group.chart_type === "ratio"}>
      {#if $FgDefaultChartType[group.id] === "ratio"}
        <PinIcon />
      {/if}
    </div>
    <button
      class:selected={group.chart_type === "ratio"}
      on:click={() => changeChartType("ratio")}
    >
      <PieChartIcon size="2.3rem" />
    </button>
  </div>
  <div class="chart-type">
    <div
      class="chart-type__pin"
      class:selected={group.chart_type === "granger"}
    >
      {#if $FgDefaultChartType[group.id] === "granger"}
        <PinIcon />
      {/if}
    </div>
    <button
      class:selected={group.chart_type === "granger"}
      on:click={() => changeChartType("granger")}
    >
      <GrangerChartIcon size="2.3rem" />
    </button>
  </div>
  <div class="chart-type">
    <div class="chart-type__pin" class:selected={group.chart_type === "coint"}>
      {#if $FgDefaultChartType[group.id] === "coint"}
        <PinIcon />
      {/if}
    </div>
    <button
      class:selected={group.chart_type === "coint"}
      on:click={() => changeChartType("coint")}
    >
      <CointChartIcon size="2.6rem" />
    </button>
  </div>
</main>

<style>
  main {
    border-top: thin solid rgba(255, 255, 255, 0.4);
    height: 5rem;
    display: flex;
    align-items: center;
    padding: 0 0.5rem;
  }
  .chart-type {
    display: flex;
    flex-direction: column;
    align-items: center;
    position: relative;
  }
  .chart-type__pin {
    width: 3rem;
    height: 1rem;
    display: flex;
    justify-content: flex-end;
    opacity: 0.2;
    position: absolute;
    top: -0.3rem;
    left: 1.5rem;
  }
  button {
    width: 3rem;
    height: 3rem;
    color: white;
    opacity: 0.2;
    margin: 0 1rem;
  }
  button:hover {
    cursor: pointer;
  }
  .selected {
    opacity: 1;
  }
  .selected:hover {
    cursor: default;
  }
</style>
