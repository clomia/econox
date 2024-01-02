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
</script>

<main>
  <div class="header">
    {#if $UnivariateElementSelected}
      <button
        class="header__btn"
        on:click={selectElement}
        class:selected={selected.element}
      >
        <div class="header__btn__element-code">
          {$UnivariateElementSelected.code}
        </div>
        <div class="header__btn__element-name">
          {$UnivariateElementSelected.name}
          {#if $UnivariateElementSelected.section === "country" && $CountryCodeMap}
            {@const code =
              $CountryCodeMap[$UnivariateElementSelected.code].toLowerCase()}
            <img
              src={`https://flagcdn.com/w40/${code}.png`}
              alt={$UnivariateElementSelected.name}
              width="30px"
            />
          {/if}
        </div></button
      >
    {/if}
    {#if $UnivariateFactorSelected}
      <button
        class="header__btn"
        on:click={selectFactorSection}
        class:selected={selected.factorSection}
      >
        <div class="header__btn__factor-section">
          {$UnivariateFactorSelected.section.name}
        </div>
      </button>
      <button
        class="header__btn"
        on:click={selectFactorSection}
        class:selected={selected.factor}
      >
        <div class="header__btn__factor">
          {$UnivariateFactorSelected.name}
        </div>
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
    flex-wrap: wrap;
  }
  .header__btn {
    display: flex;
    align-items: center;
    padding: 0.5rem;
    border: thin solid rgba(255, 255, 255, 0);
    position: relative;
  }
  .header__btn.selected {
    border-color: rgba(255, 255, 255, 0.2);
  }
  .header__btn:hover {
    background-color: rgba(255, 255, 255, 0.07);
    cursor: pointer;
  }
  .header__btn__element-code {
    padding: 0.2rem 0.4rem;
    border-radius: 0.15rem;
    margin-right: 0.5rem;
    color: var(--white);
    background-color: rgba(255, 255, 255, 0.2);
  }
  .header__btn__element-name {
    color: var(--white);
  }
  .header__btn__factor-section {
    padding: 0.2rem 0.4rem;
    border-radius: 0.15rem;
    color: var(--white);
    background-color: #613a55;
  }
  .header__btn__factor {
    padding: 0.2rem 0.4rem;
    border-radius: 0.15rem;
    color: var(--white);
    background-color: #40533e;
  }
</style>
