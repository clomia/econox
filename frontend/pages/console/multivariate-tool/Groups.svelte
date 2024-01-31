<script lang="ts">
  import { FeatureGroups, FeatureGroupSelected } from "../../../modules/state";
  import ClosedFolder from "../../../assets/icon/ClosedFolder.svelte";
  import Folder from "../../../assets/icon/Folder.svelte";
  import Magnifier from "../../../assets/icon/Magnifier.svelte";
  import MinusIcon from "../../../assets/icon/MinusIcon.svelte";
  import EditIcon from "../../../assets/icon/EditIcon.svelte";
  import { attrQuerySort } from "../../../modules/functions";
  import type { FeatureGroupType } from "../../../modules/state";

  let searchQuery = "";
  $: groups = attrQuerySort($FeatureGroups, searchQuery, "name");

  let groupHovered: FeatureGroupType | null = null;
  const selectGroup = async (group: FeatureGroupType) => {
    $FeatureGroupSelected = group;
  };
  const deleteGroup = async (group: FeatureGroupType) => {
    console.log(group, "삭제해야대~");
  };
</script>

<main>
  <div class="search">
    <Magnifier />
    <input class="search__input" type="text" bind:value={searchQuery} />
  </div>
  <div class="list">
    {#each groups as group}
      {@const selected = $FeatureGroupSelected === group}
      {@const hovered = groupHovered === group}
      <div class="list__group" class:selected class:shrink={groups.length >= 6}>
        <button
          class="list__group__main"
          class:shrink={groups.length >= 6}
          on:click={() => selectGroup(group)}
          on:mouseenter={() => (groupHovered = group)}
          on:mouseleave={() => (groupHovered = null)}
        >
          <div class="list__group__main__icon">
            {#if selected || hovered}
              <Folder />
            {:else}
              <ClosedFolder />
            {/if}
          </div>
          {group.name}
        </button>
        <button class="list__group__edit"> <EditIcon /> </button>
        <button class="list__group__delete" on:click={() => deleteGroup(group)}>
          <MinusIcon size={1.2} />
        </button>
      </div>
    {/each}
  </div>
</main>

<style>
  main {
    position: relative;
  }
  .search {
    display: flex;
    align-items: center;
    padding-left: 0.8rem;
    height: 2.6rem;
    border-bottom: thin solid rgba(255, 255, 255, 0.2);
  }
  .search__input {
    margin-left: 0.7rem;
    color: var(--white);
    width: 40rem;
  }
  .list {
    margin: 1rem;
    min-height: 11.9rem;
    max-height: 17.5rem;
    overflow: auto;
  }
  .list__group {
    display: flex;
    width: 100%;
    align-items: center;
    min-height: 2.8rem;
    border: thin solid rgba(255, 255, 255, 0);
  }
  .list__group.shrink {
    width: 98%;
  }
  .list__group__main {
    display: flex;
    align-items: center;
    color: var(--white);
    width: 36.6rem;
    height: 100%;
  }
  .list__group__main.shrink {
    width: 35.35rem;
  }
  .list__group__main:hover {
    cursor: pointer;
    color: white;
  }
  .list__group__main__icon {
    width: 3rem;
    opacity: 0.9;
  }
  .list__group__edit,
  .list__group__delete {
    height: 2.6rem;
    width: 2.6rem;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  .list__group__edit,
  .list__group__delete {
    opacity: 0.7;
  }
  .list__group__edit:hover,
  .list__group__delete:hover {
    background-color: rgba(255, 255, 255, 0.2);
    cursor: pointer;
    opacity: 1;
  }
  .list__group.selected {
    border-color: rgba(255, 255, 255, 0.2);
  }
</style>
