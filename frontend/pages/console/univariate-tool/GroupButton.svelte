<script lang="ts">
  import {
    Text,
    UnivariateElementSelected,
    UnivariateFactorSelected,
    UnivariateChartSource,
    FeatureGroups,
  } from "../../../modules/state";
  import { swal } from "../../../modules/functions";
  import GroupSelector from "./GroupSelector.svelte";

  // 장황해 보이지만 그룹에 추가할 수 있는지 여부를 확인할 수 있는 가장 간결한 방법이다..
  let chartSource: null | [string, string | number][] = null;
  let elementCode: any;
  let elementSection: any;
  let factorCode: any;
  let factorSection: any;
  let targetFeature: any;
  let buttonAvaliable: boolean = false;
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
  $: if (chartSource?.length) {
    buttonAvaliable = true;
    targetFeature = {
      element: {
        section: $UnivariateElementSelected.section,
        code: $UnivariateElementSelected.code,
      },
      factor: {
        section: $UnivariateFactorSelected.section.code,
        code: $UnivariateFactorSelected.code,
      },
    };
  } else {
    buttonAvaliable = false;
  }

  let selector = false;
  const selectorOff = () => {
    selector = false;
  };
  const selectorOn = async () => {
    if ($FeatureGroups.filter((g) => !g.confirm).length) {
      // 모든 그룹이 confirm되지 않은 경우 변경할 수 없음
      await swal(
        "삭제 처리중인 데이터 그룹이 있습니다. 잠시 후 다시 시도해주세요"
      );
    } else {
      selector = true;
    }
  };
</script>

{#if buttonAvaliable}
  <main>
    <button on:click={selectorOn}>{$Text.AddDataToGroup}</button>
  </main>
{/if}
{#if selector}
  <GroupSelector {targetFeature} on:close={selectorOff} />
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
