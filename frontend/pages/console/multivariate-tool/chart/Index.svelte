<script lang="ts">
  import {
    FeatureGroups,
    FeatureGroupSelected,
    FgTsOrigin,
  } from "../../../../modules/state";
  import { fgDataStateTracker, fgDataStateSynchronizer } from "../functions";
  import Header from "./Header.svelte";
  import Menu from "./Menu.svelte";
  import Note from "./Note.svelte";
  import LineChart from "./render/Line.svelte";
  import RatioChart from "./render/Ratio.svelte";
  import GrangerChart from "./render/Granger.svelte";
  import CointChart from "./render/Coint.svelte";

  const chartMap = {
    line: LineChart,
    ratio: RatioChart,
    granger: GrangerChart,
    coint: CointChart,
  };

  let beforeGroups = [...$FeatureGroups];
  $: if ($FeatureGroups) {
    fgDataStateTracker(beforeGroups, $FeatureGroups);
    beforeGroups = [...$FeatureGroups];
  }

  $: if ($FeatureGroupSelected) fgDataStateSynchronizer($FeatureGroupSelected);

  $: if ($FeatureGroupSelected && $FgTsOrigin) {
    console.log($FeatureGroupSelected);
    console.log($FgTsOrigin);
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
