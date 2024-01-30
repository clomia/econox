<!-- 다변량 툴 개발을 위해서 임시로 만들어놓는 버튼, 다변량 툴 개발 후 이쁘게 재작성 할 예정 -->
<script lang="ts">
  /**
   * 버튼 기능: 펙터를 추가할 그룹 선택
   *   - 기존 그룹 리스트와 그룹 추가 버튼 제공
   *     - 그룹 리스트는 검색 툴도 있고 크고 좋아야 함
   *     - 그룹 추가 기능도 크고 좋아야 함
   */

  import {
    UnivariateElementSelected,
    UnivariateFactorSelected,
    UnivariateChartSource,
  } from "../../../modules/state";
  import { api } from "../../../modules/request";
  import type { SourceType } from "../../../modules/state";

  let chartSource: null | SourceType = null;
  let elementCode: any;
  let elementSection: any;
  let factorCode: any;
  let factorSection: any;
  $: if ($UnivariateElementSelected && $UnivariateFactorSelected) {
    elementCode = $UnivariateElementSelected.code;
    elementSection = $UnivariateElementSelected.section;
    factorCode = $UnivariateFactorSelected.code;
    factorSection = $UnivariateFactorSelected.section.code;
    const sourceKey = `${elementSection}-${elementCode}_${factorSection}-${factorCode}`;
    chartSource = $UnivariateChartSource[sourceKey];
  } else {
    chartSource = null;
  }
  $: buttonAvaliable =
    chartSource && chartSource.original.length && chartSource.normalized.length;

  let groupId: number;
  let groupName: string;
  let groupDescription: string = "";
  const proc = async () => {
    if (groupName) {
      // 그룹 생성 & 추가
      const resp = await api.member.post("/feature/group", {
        name: groupName,
        description: groupDescription,
      });
      groupId = resp.data["group_id"];
    }
    // 이미 있는 그룹에 추가
    const resp = await api.member.post("/feature/group/feature", {
      group_id: groupId,
      element: { section: elementSection, code: elementCode },
      factor: { section: factorSection, code: factorCode },
    });
    console.log(resp.data);
  };
</script>

{#if buttonAvaliable}
  <main>
    <input type="number" placeholder="Select ID" bind:value={groupId} />
    <input type="text" placeholder="Create Name" bind:value={groupName} />
    <input
      type="text"
      placeholder="Create Description"
      bind:value={groupDescription}
    />
    <button on:click={proc}>그룹에 추가</button>
  </main>
{/if}

<style>
  main {
    border-top: thin solid white;
  }
  button {
    padding: 2rem;
    color: white;
    background-color: blue;
  }
  button:hover {
    cursor: pointer;
    background-color: red;
  }
  input {
    min-width: 10rem;
    height: 3rem;
    background-color: rgba(255, 255, 255, 0.5);
    color: black;
  }
</style>
