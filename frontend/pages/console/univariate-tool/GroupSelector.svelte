<!-- 단변량을 추가할 그룹을 선택해 추가하거나 생성해주는 컴포넌트 -->
<script lang="ts">
  import { createEventDispatcher, onMount } from "svelte";
  import Magnifier from "../../../assets/icon/Magnifier.svelte";
  import ClosedFolder from "../../../assets/icon/ClosedFolder.svelte";
  import PlusIcon from "../../../assets/icon/PlusIcon.svelte";
  import CloseButton from "../../../components/CloseButton.svelte";
  import CircleLoader from "../../../assets/animation/CircleLoader.svelte";
  import { api } from "../../../modules/request";
  import { FeatureGroups, Text } from "../../../modules/state";
  import { attrQuerySort, strip } from "../../../modules/functions";
  import {
    loadGroups,
    selectGroup,
    featureAddDeleteHandler,
  } from "../multivariate-tool/functions";
  import { isSame, swal, format } from "../../../modules/functions";
  import type { FeatureGroupType } from "../../../modules/state";
  export let targetFeature: {
    element: {
      section: string;
      code: string;
    };
    factor: {
      section: string;
      code: string;
    };
  };

  onMount(() => {
    document.body.style.overflow = "hidden";
  });

  const dispatch = createEventDispatcher();

  const filter = (groups: FeatureGroupType[]) => {
    // 이미 targetFeature가 포함된 그룹은 표시되지 않도록 합니다.
    return groups.filter((group) => {
      if (group.features.length >= 6) {
        // 그룹의 피쳐 갯수는 6개를 초과할 수 없다. 6개 넘으면 계산 시간 너무 김
        return false;
      }
      return (
        group.features.length === 0 || // 텅 빈 그룹이거나
        group.features.filter(
          (feature) =>
            isSame(feature.element, targetFeature.element) &&
            isSame(feature.factor, targetFeature.factor)
        ).length === 0
      ); // targetFeature와 동일한 피쳐가 하나도 없는 경우 통과
    });
  };

  let searchQuery = "";
  $: groups = filter(attrQuerySort($FeatureGroups, searchQuery, "name"));
  let isLoading = false;
  let newGroupName = "";
  $: if (newGroupName.length >= 58) {
    newGroupName = newGroupName.slice(0, 58);
  }

  const close = () => {
    document.body.style.overflow = "";
    dispatch("close");
  };

  const select = async (group: FeatureGroupType) => {
    if (isLoading) {
      return; // 중복 동작 방지
    }
    isLoading = true;
    // 서버가 피쳐 색상을 지정해 줘야 UI를 만들 수 있어서 낙관적 업데이트를 할 수 없음
    await api.member.post("/feature/group/feature", {
      group_id: group.id,
      ...targetFeature,
    }); // 서버에 반영
    await loadGroups(true); // 상태 업데이트
    selectGroup(group.id);
    featureAddDeleteHandler(group.id);
    isLoading = false;
    close();
    await swal(format($Text.f_DataAddedToGroup, { groupName: group.name }));
    const updatedDom = document.getElementById("multivariate-tool__features");
    if (updatedDom) {
      updatedDom.scrollIntoView({ behavior: "instant", block: "start" });
      // behavior: smooth로 설정하면 스크롤 동작이 쬐끔 되더니 마는 문제가 있어서 instant로 함
    }
  };
  const create = async () => {
    if (isLoading) {
      return; // 중복 동작 방지
    }
    const name = strip(newGroupName);
    if (!name) {
      return; // 빈 값은 허용되지 않음
    }
    isLoading = true;
    await api.member.post("/feature/group", { name: newGroupName });
    await loadGroups(true); // 상태 업데이트
    newGroupName = "";
    isLoading = false;
  };

  const enterToCreate = async (event: KeyboardEvent) => {
    // input에 대해 엔터키 누르면 create 되도록
    if (event.key === "Enter") await create();
  };
</script>

{#if isLoading}
  <div class="loader"><CircleLoader /></div>
{/if}
<div class="membrane">
  <main>
    <button class="close" on:click={close}><CloseButton /></button>
    <div class="title">{$Text.AddDataToGroupTitle}</div>
    <div class="search">
      <Magnifier />
      <input
        bind:value={searchQuery}
        type="text"
        placeholder={$Text.FindGroup}
      />
    </div>
    <div class="list">
      <div class="list__add">
        <div class="list__add__icon"><ClosedFolder /></div>
        <input
          bind:value={newGroupName}
          on:keydown={enterToCreate}
          type="text"
          placeholder={$Text.CreateGroup}
        />
        <button on:click={create}><PlusIcon /></button>
      </div>
      {#each groups as group}
        <button class="list__exist" on:click={() => select(group)}>
          <div class="list__exist__icon"><ClosedFolder /></div>
          <div class="list__exist__name">
            {group.name}
            <div class="list__exist__name__feature-count">
              {group.features.length}
            </div>
          </div>
        </button>
      {/each}
    </div>
    <div class="description">{$Text.AddDataToGroupDescription}</div>
  </main>
</div>

<style>
  .membrane,
  .loader {
    position: fixed;
    z-index: 11;
    top: 0;
    left: 0;
    width: 100vw;
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: rgba(0, 0, 0, 0.4);
  }
  .loader {
    z-index: 12;
  }
  main {
    width: 40rem;
    height: 34.5rem;
    background: var(--widget-background);
    padding: 1rem;
    padding-top: 1.5rem;
    position: relative;
  }
  .close {
    position: absolute;
    top: 0.5rem;
    right: 0.5rem;
    transform: scale(0.8);
  }
  .title {
    text-align: center;
    font-size: 1.1rem;
    color: var(--white);
  }
  .search {
    margin-top: 1rem;
    margin-bottom: 0.5rem;
    padding-left: 0.7rem;
    height: 2.6rem;
    display: flex;
    align-items: center;
    border: thin solid rgba(255, 255, 255, 0.2);
    border-radius: 0.2rem;
  }
  .search input {
    width: 34rem;
    height: 2rem;
    margin-left: 0.7rem;
    color: var(--white);
  }
  .list {
    height: 18rem;
    overflow: auto;
  }
  .list__add,
  .list__exist {
    display: flex;
    align-items: center;
    color: var(--white);
    width: 98%;
  }
  .list__exist {
    padding: 0.6rem 0;
  }
  .list__add__icon,
  .list__exist__icon {
    margin-left: 0.6rem;
    margin-right: 0.5rem;
    display: flex;
    align-items: center;
  }
  .list__exist__name {
    width: 94%;
    text-align: start;
    display: flex;
    align-items: center;
    justify-content: space-between;
  }
  .list__exist__name__feature-count {
    color: white;
    margin-left: 0.5rem;
    margin-right: 0.83rem;
    opacity: 0.2;
  }
  .list__add input {
    color: var(--white);
    width: 33rem;
  }
  .list__add input:hover,
  .list__add input:focus {
    padding-bottom: 0.2rem;
    border-bottom: thin solid rgba(255, 255, 255, 0.5);
  }
  .list__add button {
    width: 2.2rem;
    height: 2.2rem;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-left: 1rem;
    opacity: 0.7;
  }
  .list__exist:hover,
  .list__add button:hover {
    background-color: rgba(255, 255, 255, 0.2);
    cursor: pointer;
    opacity: 1;
  }
  .description {
    display: flex;
    justify-content: center;
    color: var(--white);
    height: 8.1rem;
    border-top: thin solid rgba(255, 255, 255, 0.3);
    padding: 1rem 0.5rem;
  }
</style>
