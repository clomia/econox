<script lang="ts">
  import { loadGroups } from "./functions";
  import {
    Text,
    FeatureGroupSelected,
    FeatureGroups,
  } from "../../../modules/state";
  import Groups from "./Groups.svelte";
  import Note from "./Note.svelte";
  import Features from "./Features.svelte";
  import Chart from "./chart/Index.svelte";
  import BouncingCubeLoader from "../../../assets/animation/BouncingCubeLoader.svelte";

  const loadGroupsPromise = loadGroups();
</script>

<main>
  {#await loadGroupsPromise}
    <div class="loading">
      <BouncingCubeLoader backgroundColor="#5e4141" borderColor="#ff8181" />
      <div class="load-info">{$Text.GroupLoadingInfo}</div>
    </div>
  {:then}
    {#if $FeatureGroups.length === 0}
      <div class="empty">{$Text.GroupsListBlank}</div>
    {:else}
      <div class="section"><Groups /></div>
      {#if $FeatureGroupSelected}
        <div class="section"><Note /></div>
        <div class="section" id="multivariate-tool__features"><Features /></div>
        {#if $FeatureGroupSelected.features.length}
          <div class="section"><Chart /></div>
        {/if}
      {/if}
    {/if}
  {/await}
</main>

<style>
  main {
    width: 44rem;
    border: thin solid rgba(255, 255, 255, 0.2);
    border-radius: 0.5rem;
    box-shadow: 0 0 2rem 0.1rem rgba(0, 0, 0, 0.5);
    position: relative;
  }
  .loading {
    height: 20rem;
    padding-top: 4.5rem;
  }
  .load-info {
    width: 100%;
    height: 100%;
    position: absolute;
    display: flex;
    align-items: center;
    justify-content: center;
    bottom: 0;
    left: 0;
    padding-bottom: 15.5rem;
    color: rgba(255, 255, 255, 0.6);
  }
  .empty {
    display: flex;
    height: 10rem;
    text-align: start;
    align-items: center;
    justify-content: center;
    padding: 2rem 3rem;
    color: rgba(255, 255, 255, 0.5);
  }
  .section {
    border-bottom: thin solid rgba(255, 255, 255, 0.2);
  }
  .section:last-of-type {
    border: none;
  }
</style>
