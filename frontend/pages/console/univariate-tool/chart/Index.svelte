<script lang="ts">
  import Basic from "./Basic.svelte";
  import FullScreen from "./FullScreen.svelte";
  import BouncingCubeLoader from "../../../../assets/animation/BouncingCubeLoader.svelte";
  import { Text } from "../../../../modules/state";
  import {
    UnivariateElementSelected,
    UnivariateFactorSelected,
    UnivariateChartFullScreen,
    UnivariateChartSource,
  } from "../../../../modules/state";
  import { format } from "../../../../modules/functions";
  import type { SourceType } from "../../../../modules/state";

  let chartSource: null | SourceType = null;
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
</script>

{#if chartSource}
  {#if chartSource.original.length && chartSource.standardized.length}
    {#if $UnivariateChartFullScreen}
      <FullScreen />
    {:else}
      <main><Basic {chartSource} /></main>
    {/if}
  {:else}
    <main>
      <BouncingCubeLoader />
      <div class="load-info">
        {format($Text.f_ChartLoadingInfo, {
          element: $UnivariateElementSelected?.code,
          factor: `${$UnivariateFactorSelected?.section.name}(${$UnivariateFactorSelected?.name})`,
        })}
      </div>
    </main>
  {/if}
{/if}

<style>
  main {
    border-top: thin solid rgba(255, 255, 255, 0.2);
    height: 25rem;
    display: flex;
    align-items: center;
    justify-content: center;
    position: relative;
  }
  .load-info {
    position: absolute;
    display: flex;
    width: 100%;
    height: 100%;
    align-items: center;
    justify-content: center;
    bottom: 0;
    left: 0;
    padding-bottom: 21.5rem;
    color: rgba(255, 255, 255, 0.6);
  }
</style>
