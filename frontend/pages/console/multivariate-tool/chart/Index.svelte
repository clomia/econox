<script lang="ts">
  import {
    FeatureGroups,
    FeatureGroupSelected,
  } from "../../../../modules/state";
  import Header from "./Header.svelte";
  import Menu from "./Menu.svelte";
  import Note from "./Note.svelte";
  import LineChart from "./render/Line.svelte";
  import RatioChart from "./render/Ratio.svelte";

  const chartMap = { line: LineChart, ratio: RatioChart };
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
