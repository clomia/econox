<script lang="ts">
  import { createEventDispatcher, onMount } from "svelte";
  import Excel from "../../../../assets/icon/Excel.svelte";
  import Csv from "../../../../assets/icon/Csv.svelte";
  import CloseButton from "../../../../components/CloseButton.svelte";
  import RippleLoader from "../../../../assets/animation/RippleLoader.svelte";
  import { Text } from "../../../../modules/state";
  import {
    UnivariateElementSelected,
    UnivariateFactorSelected,
  } from "../../../../modules/state";
  import { downloadFile } from "../functions";
  import type { ElementType, FactorType } from "../../../../modules/state";

  export let normalized: boolean;

  onMount(() => {
    document.body.style.overflow = "hidden";
  });

  const dispatch = createEventDispatcher();
  const close = () => {
    document.body.style.overflow = "";
    dispatch("close");
  };

  const current = {
    normalized,
    // 이 다운로드 컴포넌트가 실행되었으면 무조건 단변량이 선택되어 있음
    elementSection: ($UnivariateElementSelected as ElementType).section,
    elementCode: ($UnivariateElementSelected as ElementType).code,
    factorSection: ($UnivariateFactorSelected as FactorType).section.code,
    factorCode: ($UnivariateFactorSelected as FactorType).code,
  };
  let downloading = false;
  const downloadCsv = async () => {
    downloading = true;
    try {
      await downloadFile({ fileFormat: "csv", ...current });
    } finally {
      downloading = false;
    }
  };
  const downloadXlsx = async () => {
    downloading = true;
    try {
      await downloadFile({ fileFormat: "xlsx", ...current });
    } finally {
      downloading = false;
    }
  };
</script>

<div class="membrane">
  <main>
    <div class="title">{$Text.SelectFileFormat}</div>
    <div class="options">
      <button class="options__csv" on:click={downloadCsv}>
        <div><Csv size="6rem" /></div>
        <div class="option-title">.csv</div>
      </button>
      <button class="options__xlsx" on:click={downloadXlsx}>
        <div><Excel size="6rem" /></div>
        <div class="option-title">.xlsx</div>
      </button>
    </div>
    <button class="close" on:click={close}><CloseButton /></button>
    {#if downloading}
      <div class="loading"><RippleLoader /></div>
    {/if}
  </main>
</div>

<style>
  .membrane {
    position: fixed;
    width: 100vw;
    height: 100vh;
    top: 0;
    left: 0;
    z-index: 10;
    background-color: rgba(0, 0, 0, 0.4);
    display: flex;
    justify-content: center;
    align-items: center;
  }
  main {
    width: 30rem;
    height: 17rem;
    background: var(--widget-background);
    border: thin solid rgba(255, 255, 255, 0.15);
    border-radius: 0.2rem;
    position: relative;
  }
  .loading {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.4);
    display: flex;
    justify-content: center;
    align-items: center;
  }
  .title {
    font-size: 1.1rem;
    color: var(--white);
    margin: 1rem;
    margin-top: 2rem;
    text-align: center;
  }
  .options {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 5.5rem;
    margin-top: 2.7rem;
  }
  .options__csv,
  .options__xlsx {
    opacity: 0.5;
  }
  .options__csv:hover,
  .options__xlsx:hover {
    opacity: 0.9;
    cursor: pointer;
  }
  .option-title {
    color: white;
  }
  .close {
    position: absolute;
    top: 0.7rem;
    right: 0.7rem;
  }
</style>
