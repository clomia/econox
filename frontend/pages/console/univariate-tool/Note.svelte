<script lang="ts">
  import {
    Text,
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

  $: if ($UnivariateElementSelected) {
    select("element"); // 요소가 변경되면 변경된 요소를 선택해준다.
  }
</script>

{#if $UnivariateElementSelected}
  <main>
    <div class="header">
      <div class="header__box-row">
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
        <button
          class="header__line-row__btn"
          class:selected={$UnivariateNoteSelected.element}
          class:hovered={$UnivariateNoteHovered.element}
          style="width: {elementBoxWidth}px;"
          on:click={() => select("element")}
          on:mouseover={() => hover("element")}
          on:mouseleave={hoverOut}
          on:focus={() => hover("element")}
        >
        </button>
        {#if $UnivariateFactorSelected}
          <button
            class="header__line-row__btn"
            class:selected={$UnivariateNoteSelected.factorSection}
            class:hovered={$UnivariateNoteHovered.factorSection}
            style="width: {factorSectionBoxWidth}px;"
            on:click={() => select("factorSection")}
            on:mouseover={() => hover("factorSection")}
            on:mouseleave={hoverOut}
            on:focus={() => hover("factorSection")}
          >
          </button>
          <button
            class="header__line-row__btn"
            class:selected={$UnivariateNoteSelected.factor}
            class:hovered={$UnivariateNoteHovered.factor}
            style="width: {factorBoxWidth}px;"
            on:click={() => select("factor")}
            on:mouseover={() => hover("factor")}
            on:mouseleave={hoverOut}
            on:focus={() => hover("factor")}
          >
          </button>
        {/if}
      </div>
    </div>

    <div class="content">
      {#if $UnivariateNoteSelected.element}
        <div class="content__name">{$UnivariateElementSelected.name}</div>
        <div class="content__note">{$UnivariateElementSelected.note}</div>
      {:else if $UnivariateFactorSelected && $UnivariateNoteSelected.factorSection}
        <div class="content__name">
          {$UnivariateFactorSelected.section.name}
        </div>
        <div class="content__note">
          {$UnivariateFactorSelected.section.note}
        </div>
      {:else if $UnivariateFactorSelected && $UnivariateNoteSelected.factor}
        <div class="content__name">{$UnivariateFactorSelected.name}</div>
        <div class="content__note">{$UnivariateFactorSelected.note}</div>
      {/if}
    </div>
  </main>
{/if}

<style>
  main {
    border-top: thin solid rgba(255, 255, 255, 0.2);
  }
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

  .content {
    padding-left: 1.5rem;
    padding-right: 1rem;
    margin-bottom: 1.5rem;
  }
  .content__name {
    font-size: 1.2rem;
    margin-bottom: 0.7rem;
  }
  .content__note {
    padding-right: 0.5rem;
    max-height: 16rem;
    overflow: auto;
  }
</style>
