<script lang="ts">
  import { CountryCodeMap } from "../../../modules/state";
  import {
    UnivariateSelected,
    UnivariateElementSelected,
    UnivariateFactorSelected,
  } from "../../../modules/state";

  $: element = $UnivariateElementSelected?.name || "없음";
  $: factorSectionName = $UnivariateFactorSelected?.section?.name || "없음";
  $: factorName = $UnivariateFactorSelected?.name || "없음";

  const selected = { element: false, factorSection: false, factor: false };
  const selectElement = () => {
    selected.element = true;
    selected.factor = false;
    selected.factorSection = false;
  };
  const selectFactorSection = () => {
    selected.factorSection = true;
    selected.element = false;
    selected.factor = false;
  };
  const selectFactor = () => {
    selected.factor = true;
    selected.factorSection = false;
    selected.element = false;
  };
</script>

<main>
  <div class="header">
    {#if $UnivariateElementSelected}
      <button
        class="header__btn element-btn"
        on:click={selectElement}
        class:selected={selected.element}
      >
        {$UnivariateElementSelected.code}
      </button>
    {/if}
    {#if $UnivariateFactorSelected}
      <button
        class="header__btn factor-section-btn"
        on:click={selectFactorSection}
        class:selected={selected.factorSection}
      >
        {$UnivariateFactorSelected.section.name}
      </button>
      <button
        class="header__btn factor-btn"
        on:click={selectFactor}
        class:selected={selected.factor}
      >
        {$UnivariateFactorSelected.name}
      </button>
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
  .header {
    display: flex;
    align-items: stretch;
    padding: 1rem 1.5rem;
  }
  .header__btn {
    height: inherit;
    display: flex;
    align-items: center;
    justify-content: center;
    text-align: start;
    padding: 0.3rem 0.6rem;
    color: var(--white);
  }
  .element-btn {
    background-color: #41425e;
  }
  .factor-section-btn {
    background-color: #613a55;
  }
  .factor-btn {
    background-color: #40533e;
  }
  .header__btn:hover {
    background-color: rgba(255, 255, 255, 0.07);
    cursor: pointer;
  }
  /* .header__btn.selected {

  } */
</style>
