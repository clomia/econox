<script lang="ts">
  import { onMount } from "svelte";
  import mermaid from "mermaid";
  import {
    UnivariateSelected,
    UnivariateElementSelected,
    UnivariateFactorSelected,
  } from "../../../modules/state";
  import { Text } from "../../../modules/state";

  let element = "";
  let factorSectionName = "";
  let factorName = "";
  $: diagram = `
    stateDiagram-v2
      direction LR
      state ${$Text.Element} {
          Meta
      }
      state Factor {
        direction LR
        주가데이터 --> 조정종가
      }
      Meta --> 주가데이터
    `;

  let svgDiagram: any = "";
  $: renderDiagram = async () => {
    try {
      const { svg, bindFunctions } = await mermaid.render("mermaid", diagram);
      svgDiagram = svg;
    } catch (err) {
      console.error("Mermaid diagram rendering failed:", err);
    }
  };

  onMount(() => {
    mermaid.initialize({ startOnLoad: false });
    renderDiagram();
  });

  $: diagram && renderDiagram();
</script>

<main>
  {@html svgDiagram}
  <div class="header">
    {#if $UnivariateElementSelected}
      {$UnivariateElementSelected.name}
    {/if}
    {#if $UnivariateFactorSelected}
      {$UnivariateFactorSelected.name}
    {/if}
  </div>
  {#if typeof $UnivariateSelected?.section === "string"}
    <!-- 선택된 단변량이 Element인 경우 -->
    <div class="element">
      <div class="element__header">
        <div class="element__header__code">{$UnivariateSelected.code}</div>
        <div class="element__header__name">{$UnivariateSelected.name}</div>
      </div>
      <div class="element__note">{$UnivariateSelected.note}</div>
    </div>
  {:else if typeof $UnivariateSelected?.section === "object"}
    <!-- 선택된 단변량이 Factor인 경우 -->
    <div class="factor">
      <div class="factor__section">
        <div class="factor__section__name">
          {$UnivariateSelected.section.name}
        </div>
        <div class="factor__section__note">
          {$UnivariateSelected.section.note}
        </div>
      </div>
      <div class="factor__factor">
        <div class="factor__factor__name">{$UnivariateSelected.name}</div>
        <div class="factor__factor__note">{$UnivariateSelected.note}</div>
      </div>
    </div>
  {:else}
    <!-- 선택된 단변량이 없는 경우 -->
    <div class="null">선택 안해서 보여줄거 없음</div>
  {/if}
</main>

<div>{$UnivariateSelected}</div>

<style>
  div {
    color: var(--white);
  }
</style>
