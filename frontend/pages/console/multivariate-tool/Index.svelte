<script lang="ts">
  import { loadGroups } from "./functions";
  import { Text, FeatureGroupSelected } from "../../../modules/state";
  import Groups from "./Groups.svelte";
  import Note from "./Note.svelte";
  import Features from "./Features.svelte";
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
    <div class="section"><Groups /></div>
    {#if $FeatureGroupSelected}
      <div class="section"><Note /></div>
      <div class="section"><Features /></div>
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
    position: absolute;
    display: flex;
    width: 100%;
    height: 100%;
    align-items: center;
    justify-content: center;
    bottom: 0;
    left: 0;
    padding-bottom: 15.5rem;
    color: rgba(255, 255, 255, 0.6);
  }
  .section {
    border-bottom: thin solid rgba(255, 255, 255, 0.2);
  }
  .section:last-of-type {
    border: none;
  }
</style>
