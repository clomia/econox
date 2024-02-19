<script lang="ts">
  import { get } from "svelte/store";
  import {
    FeatureGroups,
    FeatureGroupSelected,
    FgStoreState,
  } from "../../../../modules/state";
  import { fgDataStateTracker, fgDataStateSynchronizer } from "../functions";
  import Header from "./Header.svelte";
  import Menu from "./Menu.svelte";
  import Note from "./Note.svelte";
  import LineChart from "./render/Line.svelte";
  import RatioChart from "./render/Ratio.svelte";

  const chartMap = { line: LineChart, ratio: RatioChart };

  let before = get(FeatureGroups);
  $: if ($FeatureGroups) {
    fgDataStateTracker(before, $FeatureGroups);
    before = $FeatureGroups;
  }

  $: if ($FeatureGroupSelected) {
    fgDataStateSynchronizer($FeatureGroupSelected);
  }
</script>

<main>
  <div class="header"><Header /></div>
  <svelte:component this={chartMap[$FeatureGroupSelected.chart_type]} />
  <div class="menu"><Menu /></div>
  <div class="note"><Note /></div>
</main>

<style>
  main {
    border-top: thin solid rgba(255, 255, 255, 0.2);
    position: relative;
    min-height: 5rem;
    color: white;
  }
</style>
