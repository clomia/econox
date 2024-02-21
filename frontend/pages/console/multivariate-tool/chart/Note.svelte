<script lang="ts">
  import { api } from "../../../../modules/request";
  import PinIcon from "../../../../assets/icon/PinIcon.svelte";
  import {
    Text,
    FeatureGroupSelected,
    FgDefaultChartType,
  } from "../../../../modules/state";

  $: group = $FeatureGroupSelected; // shortcut

  let name = "";
  let description = "";
  $: if (group) {
    switch (group.chart_type) {
      case "line":
        name = $Text.FgLineChart_Name;
        description = $Text.FgLineChart_Description;
        break;
      case "ratio":
        name = $Text.FgRatioChart_Name;
        description = $Text.FgRatioChart_Description;
        break;
      case "granger":
        name = $Text.FgGrangerChart_Name;
        description = $Text.FgGrangerChart_Description;
        break;
      case "coint":
        name = $Text.FgCointChart_Name;
        description = $Text.FgCointChart_Description;
        break;
    }
  }

  $: pined = group.chart_type === $FgDefaultChartType[group.id];

  const pin = async () => {
    if (pined) {
      return;
    } else {
      $FgDefaultChartType[group.id] = group.chart_type;
      await api.member.patch("/feature/group", {
        group_id: group.id,
        chart_type: group.chart_type,
      });
    }
  };
</script>

<main>
  <button on:click={pin} class="pin-btn" class:pined>
    <PinIcon size="1.2rem" />
  </button>
  <div class="name">{name}</div>
  <div class="description">{description}</div>
</main>

<style>
  main {
    border-top: thin solid rgba(255, 255, 255, 0.4);
    padding: 1rem;
    position: relative;
  }
  .pin-btn {
    position: absolute;
    right: 1rem;
    top: 1rem;
    width: 2.5rem;
    height: 2.5rem;
    border: thin solid rgba(255, 255, 255, 0.5);
    border-radius: 0.35rem;
    opacity: 0.6;
  }
  .pin-btn:hover {
    opacity: 0.9;
    cursor: pointer;
  }
  .pined {
    opacity: 0.9;
    background-color: rgba(255, 255, 255, 0.15);
    border-color: rgba(255, 255, 255, 0.5);
  }
  .pined:hover {
    cursor: default;
  }
  .name {
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: start;
    color: var(--white);
    font-size: 1.1rem;
  }
  .description {
    display: flex;
    text-align: start;
    min-height: 7rem;
    overflow: auto;
    padding: 1rem;
    color: var(--white);
  }
</style>
