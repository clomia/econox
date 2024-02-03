<script lang="ts">
  import {
    Text,
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
    <button>{$Text.AddDataToGroup}</button>
  </main>
{/if}

<style>
  main {
    display: flex;
    align-items: center;
    justify-content: center;
    margin-top: 0.5rem;
    margin-bottom: 1.7em;
  }
  button {
    display: flex;
    width: 30rem;
    height: 3rem;
    align-items: center;
    justify-content: center;
    color: var(--white);
    border-radius: 0.2rem;
    border: thin solid rgba(255, 255, 255, 0.3);
    box-shadow: 0 0 2rem 0.1rem rgba(0, 0, 0, 0.2);
  }
  button:hover {
    cursor: pointer;
    box-shadow: inset 0 0 0.5rem 0.2rem rgba(0, 0, 0, 0.2);
    color: rgba(255, 255, 255, 0.8);
    border-color: rgba(255, 255, 255, 0.45);
  }
</style>
