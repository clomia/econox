<script lang="ts">
  import Swal from "sweetalert2";
  import { createEventDispatcher, onMount } from "svelte";
  import { defaultSwalStyle } from "../../../../modules/functions";
  import Excel from "../../../../assets/icon/Excel.svelte";
  import Csv from "../../../../assets/icon/Csv.svelte";
  import CloseButton from "../../../../components/CloseButton.svelte";
  import RippleLoader from "../../../../assets/animation/RippleLoader.svelte";
  import { Text } from "../../../../modules/state";
  import { downloadFile } from "../functions";

  export let elementSection: string;
  export let elementCode: string;
  export let factorSection: string;
  export let factorCode: string;

  onMount(() => {
    document.body.style.overflow = "hidden";
  });

  const dispatch = createEventDispatcher();
  const close = () => {
    document.body.style.overflow = "";
    dispatch("close");
  };

  let downloading = false;
  const completeMessage = async () => {
    await Swal.fire({
      ...defaultSwalStyle,
      width: "32rem",
      icon: "info",
      showDenyButton: false,
      title: $Text.DownloadComplete,
      confirmButtonText: $Text.Ok,
    });
  };
  const downloadCsv = async () => {
    downloading = true;
    try {
      await downloadFile({
        fileFormat: "csv",
        elementSection,
        elementCode,
        factorSection,
        factorCode,
      });
      await completeMessage();
      close();
    } finally {
      downloading = false;
    }
  };
  const downloadXlsx = async () => {
    downloading = true;
    try {
      await downloadFile({
        fileFormat: "xlsx",
        elementSection,
        elementCode,
        factorSection,
        factorCode,
      });
      await completeMessage();
      close();
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
