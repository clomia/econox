<script>
  import Basic from "./Basic.svelte";
  import FullScreen from "./FullScreen.svelte";
  import RippleLoader from "../../../../assets/animation/RippleLoader.svelte";
  import {
    UnivariateElementSelected,
    UnivariateFactorSelected,
    UnivariateChartFullScreen,
    UnivariateChartSource,
  } from "../../../../modules/state";

  let chartSource = null;
  $: if ($UnivariateElementSelected && $UnivariateFactorSelected) {
    const elementCode = $UnivariateElementSelected.code;
    const elementSection = $UnivariateElementSelected.section;
    const factorCode = $UnivariateFactorSelected.code;
    const factorSection = $UnivariateFactorSelected.section.code;
    const sourceKey = `${elementSection}-${elementCode}_${factorSection}-${factorCode}`;
    chartSource = $UnivariateChartSource[sourceKey];
  } else {
    chartSource = null;
  }

  $: console.log(chartSource);
</script>

{#if chartSource}
  {#if chartSource.original.length && chartSource.standardized.length}
    {#if $UnivariateChartFullScreen}
      <FullScreen />
    {:else}
      <main><Basic /></main>
    {/if}
  {:else}
    <main><RippleLoader /></main>
  {/if}
{/if}

<style>
  main {
    border-top: thin solid rgba(255, 255, 255, 0.2);
  }
</style>
