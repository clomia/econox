<script lang="ts">
  import SpinLoader from "../../../../assets/animation/SpinLoader.svelte";
  import FullScreenIcon from "../../../../assets/icon/FullScreenIcon.svelte";
  import LinkIcon from "../../../../assets/icon/LinkIcon.svelte";
  import WifiIcon from "../../../../assets/icon/WifiIcon.svelte";
  import {
    Text,
    FeatureGroupSelected,
    FgDataState,
    FgChartFullScreen,
  } from "../../../../modules/state";
  import { chartDataMap } from "../functions";
  import Share from "../Share.svelte";

  $: group = $FeatureGroupSelected; // shortcut

  let ready: boolean = false;
  const getReady = () => {
    return $FgDataState[group.id][chartDataMap[group.chart_type]] === "after";
  };
  $: if (group && $FgDataState) {
    ready = getReady();
  }

  let shareWidget = false;
</script>

{#if shareWidget}
  <Share on:close={() => (shareWidget = false)} />
{/if}

<main>
  <div class="layout-div"></div>
  {#if ready}
    <button class="share" on:click={() => (shareWidget = true)}>
      {#if group.public}
        <WifiIcon size="1rem" />
        <div class="share__text">{$Text.OnPublicTitle}</div>
      {:else}
        <LinkIcon size="1rem" />
        <div class="share__text">{$Text.ShareDataGroup}</div>
      {/if}
    </button>
    <button on:click={() => ($FgChartFullScreen = true)} class="fullscreen">
      <FullScreenIcon />
    </button>
  {:else}
    <div class="updating">
      <SpinLoader size={0.4} />
      <div class="updating__text">{$Text.Loading}</div>
    </div>
    <div class="layout-div"></div>
  {/if}
</main>

<style>
  main {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .updating {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 0;
    color: var(--white);
  }
  .updating__text {
    padding-bottom: 0.2rem;
  }
  .share {
    margin-right: 1rem;
    display: flex;
    align-items: center;
  }
  .share__text {
    color: white;
    margin-left: 0.4rem;
  }
  .layout-div {
    width: 26px;
    height: 26px;
  }
  button {
    opacity: 0.5;
  }
  button:hover {
    cursor: pointer;
    opacity: 1;
  }
  main {
    padding: 1rem;
    padding-bottom: 0;
  }
</style>
