<script lang="ts">
  import {
    UnivariateSelected,
    UnivariateElementSelected,
    UnivariateFactorSelected,
    UnivariateNoteSelected,
    UnivariateNoteHovered,
  } from "../../../modules/state";
  import type { CurrentNoteTargetType } from "../../../modules/state";

  let elementBoxWidth = 0;
  let factorSectionBoxWidth = 0;
  let factorBoxWidth = 0;

  function resetState(store: any) {
    store.set({ element: false, factorSection: false, factor: false });
  }

  function select(target: keyof CurrentNoteTargetType) {
    resetState(UnivariateNoteSelected);
    if ($UnivariateNoteHovered[target]) {
      resetState(UnivariateNoteHovered);
    }
    UnivariateNoteSelected.update((s) => ({ ...s, [target]: true }));
  }

  function hover(target: keyof CurrentNoteTargetType) {
    resetState(UnivariateNoteHovered);
    if (!$UnivariateNoteSelected[target]) {
      UnivariateNoteHovered.update((h) => ({ ...h, [target]: true }));
    }
  }

  function hoverOut() {
    resetState(UnivariateNoteHovered);
  }
</script>

<main>
  <div class="header">
    <div class="header__box-row">
      {#if $UnivariateElementSelected}
        <button
          class="header__box-row__btn element-btn"
          on:click={() => select("element")}
          bind:clientWidth={elementBoxWidth}
          on:mouseover={() => hover("element")}
          on:mouseleave={hoverOut}
          on:focus={() => hover("element")}
        >
          {$UnivariateElementSelected.code}
        </button>
      {/if}
      {#if $UnivariateFactorSelected}
        <button
          class="header__box-row__btn factor-section-btn"
          on:click={() => select("factorSection")}
          bind:clientWidth={factorSectionBoxWidth}
          on:mouseover={() => hover("factorSection")}
          on:mouseleave={hoverOut}
          on:focus={() => hover("factorSection")}
        >
          {$UnivariateFactorSelected.section.name}
        </button>
        <button
          class="header__box-row__btn factor-btn"
          on:click={() => select("factor")}
          bind:clientWidth={factorBoxWidth}
          on:mouseover={() => hover("factor")}
          on:mouseleave={hoverOut}
          on:focus={() => hover("factor")}
        >
          {$UnivariateFactorSelected.name}
        </button>
      {/if}
    </div>
    <div class="header__line-row">
      {#if $UnivariateElementSelected}
        <button
          class="header__line-row__btn"
          on:click={() => select("element")}
          class:selected={$UnivariateNoteSelected.element}
          class:hovered={$UnivariateNoteHovered.element}
          style="width: {elementBoxWidth}px;"
        >
        </button>
      {/if}
      {#if $UnivariateFactorSelected}
        <button
          class="header__line-row__btn"
          on:click={() => select("factorSection")}
          class:selected={$UnivariateNoteSelected.factorSection}
          class:hovered={$UnivariateNoteHovered.factorSection}
          style="width: {factorSectionBoxWidth}px;"
        >
        </button>
        <button
          class="header__line-row__btn"
          on:click={() => select("factor")}
          class:selected={$UnivariateNoteSelected.factor}
          class:hovered={$UnivariateNoteHovered.factor}
          style="width: {factorBoxWidth}px;"
        >
        </button>
      {/if}
    </div>
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
    padding: 1rem 1.5rem;
  }
  .header__box-row {
    display: flex;
  }
  .header__box-row__btn {
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

  .header__line-row {
    display: flex;
  }
  .header__line-row__btn {
    display: flex;
    height: 0.7rem;
    border-bottom: 0.2rem solid rgba(255, 255, 255, 0.2);
  }
  .header__line-row__btn.selected {
    border-color: var(--white);
  }
  .header__line-row__btn.hovered {
    border-color: rgba(255, 255, 255, 0.45);
  }

  .header__box-row__btn:hover,
  .header__line-row__btn:hover {
    cursor: pointer;
  }
</style>
