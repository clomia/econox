<script lang="ts">
  import { loadGroups } from "./functions";
  import Groups from "./Groups.svelte";

  const loadGroupsPromise = loadGroups();
</script>

<main>
  {#await loadGroupsPromise}
    로딩중 데쓰데
  {:then}
    <Groups />
  {/await}
</main>

<style>
  main {
    width: 44rem;
    border: thin solid rgba(255, 255, 255, 0.2);
    border-radius: 0.5rem;
    box-shadow: 0 0 2rem 0.1rem rgba(0, 0, 0, 0.5);
  }
</style>
