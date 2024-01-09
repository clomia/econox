<script>
  import Basic from "./Basic.svelte";
  import FullScreen from "./FullScreen.svelte";
  import { UnivariateChartFullScreen } from "../../../../modules/state";
</script>

{#if $UnivariateChartFullScreen}
  <FullScreen />
{:else}
  <Basic />
{/if}
