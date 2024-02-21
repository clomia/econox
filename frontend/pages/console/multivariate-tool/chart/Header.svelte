<script lang="ts">
  import { Text } from "../../../../modules/state";
  import SpinLoader from "../../../../assets/animation/SpinLoader.svelte";
  import FullScreenIcon from "../../../../assets/icon/FullScreenIcon.svelte";
  import LinkIcon from "../../../../assets/icon/LinkIcon.svelte";
  import {
    FeatureGroupSelected,
    FgStoreState,
  } from "../../../../modules/state";

  $: group = $FeatureGroupSelected; // shortcut

  let ready: boolean = false;
  const getReady = () => {
    switch (group.chart_type) {
      case "line":
      case "ratio":
        return $FgStoreState[group.id].FgTsOrigin === "after";
      case "granger":
        return $FgStoreState[group.id].FgGranger === "after";
      case "coint":
        return $FgStoreState[group.id].FgCoint === "after";
    }
  };
  $: if (group && $FgStoreState[group.id]) {
    ready = getReady();
  }
</script>

<main>
  <div class="layout-div"></div>
  {#if ready}
    <button class="share">
      <LinkIcon size="1rem" />
      <div class="share__text">{$Text.ShareDataGroup}</div>
    </button>
  {:else if group.confirm}
    <div class="updating">
      <SpinLoader size={0.4} />
      <div class="updating__text">Loading...</div>
    </div>
  {:else}
    <div class="updating">
      <SpinLoader size={0.4} />
      <div class="updating__text">{$Text.ReflectingToDelete}</div>
    </div>
  {/if}
  <button class="fullscreen"><FullScreenIcon /></button>
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
    margin-left: 0.5rem;
  }
  .layout-div {
    width: 26px;
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
