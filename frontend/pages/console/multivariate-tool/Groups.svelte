<script lang="ts">
  import { api } from "../../../modules/request";
  import { FeatureGroups, FeatureGroupSelected } from "../../../modules/state";
  import ClosedFolder from "../../../assets/icon/ClosedFolder.svelte";
  import Folder from "../../../assets/icon/Folder.svelte";
  import Magnifier from "../../../assets/icon/Magnifier.svelte";
  import MinusIcon from "../../../assets/icon/MinusIcon.svelte";
  import EditIcon from "../../../assets/icon/EditIcon.svelte";
  import Check from "../../../assets/icon/Check.svelte";
  import CancelIcon from "../../../assets/icon/CancelIcon.svelte";
  import { attrQuerySort, strip } from "../../../modules/functions";
  import type { FeatureGroupType } from "../../../modules/state";

  let searchQuery = "";
  $: groups = attrQuerySort($FeatureGroups, searchQuery, "name");

  let groupHovered: FeatureGroupType | null = null;
  let groupEditingTarget: FeatureGroupType | null = null;
  let groupEditingInput: HTMLInputElement | null = null;

  const selectGroup = (group: FeatureGroupType) => {
    $FeatureGroupSelected = group;
  };
  const deleteGroup = async (group: FeatureGroupType) => {
    $FeatureGroupSelected = null;
    $FeatureGroups = $FeatureGroups.filter((g) => g.id !== group.id);
    await api.member.delete("feature/group", {
      params: { group_id: group.id },
    });
  };
  const editGroup = (group: FeatureGroupType) => {
    groupEditingTarget = group;
  };

  const editGroupDone = () => {
    groupEditingTarget = null;
    groupEditingInput = null;
  };
  const editHandler = () => {
    if (!groupEditingInput) {
      return; // for typescript
    }
    // 58글자 초과 입력하지 못하도록 제한
    groupEditingInput.value = groupEditingInput.value.slice(0, 58);
  };
  const editGroupConform = async (group: FeatureGroupType) => {
    if (!groupEditingInput || !$FeatureGroups) {
      return; // for typescript
    }
    const newName = strip(groupEditingInput.value);
    const target = $FeatureGroups.find((g) => g.id === group.id);
    editGroupDone();
    if (!target) {
      return; // for typescript
    }
    if (!newName || target.name === newName) {
      return;
    }
    if (target === $FeatureGroupSelected) {
      $FeatureGroupSelected.name = newName;
    }
    target.name = newName;
    await api.member.patch("/feature/group", {
      group_id: group.id,
      name: newName,
    });
  };
  const editGroupConformKeyHandler = async (
    event: KeyboardEvent,
    group: FeatureGroupType
  ) => {
    // input에 대해 엔터키 눌러도 confirm되도록 구현
    if (event.key === "Enter") {
      await editGroupConform(group);
    }
  };
  $: if (groupEditingInput) {
    // 편집 버튼 누르면 해당 input에 자동으로 포커싱 해주기 구현
    groupEditingInput.focus();
  }
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
      <div class="list__group" class:selected class:shrink={groups.length >= 7}>
        <button
          class="list__group__main"
          class:shrink={groups.length >= 7}
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
          {#if groupEditingTarget === group}
            <input
              class="list__group__main__edit"
              type="text"
              value={group.name}
              bind:this={groupEditingInput}
              placeholder={group.name}
              on:keydown={(event) => editGroupConformKeyHandler(event, group)}
              on:input={editHandler}
            />
          {:else}
            <div class="list__group__main__name">
              {group.name}
              <div class="list__group__main__name__feature-count">
                {group.features.length}
              </div>
            </div>
          {/if}
        </button>
        {#if groupEditingTarget === group}
          <button
            class="list__group__edit-confirm"
            on:click={() => editGroupConform(group)}
          >
            <Check />
          </button>
          <button class="list__group__edit-cancel" on:click={editGroupDone}>
            <CancelIcon />
          </button>
        {:else}
          <button class="list__group__edit" on:click={() => editGroup(group)}>
            <EditIcon />
          </button>
          <button
            class="list__group__delete"
            on:click={() => deleteGroup(group)}
          >
            <MinusIcon size={1.2} />
          </button>
        {/if}
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
    text-align: start;
  }
  .list__group__main.shrink {
    width: 35.35rem;
  }
  .list__group__main:hover {
    cursor: pointer;
    color: white;
  }
  .list__group__main__edit {
    color: var(--white);
    width: 90%;
    border-bottom: thin solid rgba(255, 255, 255, 0.4);
    padding-bottom: 0.3rem;
    margin-left: 0.64rem;
  }
  .list__group__main__name {
    margin-left: 1rem;
    width: 40rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .list__group__main__name__feature-count {
    color: white;
    margin-left: 0.5rem;
    opacity: 0.2;
  }
  .list__group__main__icon {
    width: 2rem;
    opacity: 0.9;
    margin-left: 0.5rem;
  }
  .list__group__edit,
  .list__group__delete,
  .list__group__edit-confirm,
  .list__group__edit-cancel {
    height: 2.6rem;
    width: 2.6rem;
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0.7;
  }
  .list__group__edit:hover,
  .list__group__delete:hover,
  .list__group__edit-confirm:hover,
  .list__group__edit-cancel:hover {
    background-color: rgba(255, 255, 255, 0.2);
    cursor: pointer;
    opacity: 1;
  }
  .list__group.selected {
    border-color: rgba(255, 255, 255, 0.2);
  }
</style>
