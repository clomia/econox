<script lang="ts">
  import { createEventDispatcher, onMount } from "svelte";
  import { swal } from "../../../modules/functions";
  import Excel from "../../../assets/icon/Excel.svelte";
  import Csv from "../../../assets/icon/Csv.svelte";
  import Toggle from "../../../components/Toggle.svelte";
  import CloseButton from "../../../components/CloseButton.svelte";
  import RippleLoader from "../../../assets/animation/RippleLoader.svelte";
  import { wikiUrl } from "../../../modules/wiki";
  import { Text, Lang } from "../../../modules/state";
  import { downloadFile } from "./functions";
  import { FeatureGroupSelected } from "../../../modules/state";

  onMount(() => {
    document.body.style.overflow = "hidden";
  });

  let scaled: boolean = false;

  const dispatch = createEventDispatcher();
  const close = () => {
    document.body.style.overflow = "";
    dispatch("close");
  };

  let downloading = false;
  const completeMessage = async () => {
    await swal($Text.DownloadComplete, "32rem");
  };
  const downloadCsv = async () => {
    downloading = true;
    try {
      await downloadFile($FeatureGroupSelected.name, {
        fileFormat: "csv",
        groupId: $FeatureGroupSelected.id,
        lang: $Lang,
        minmaxScaling: scaled,
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
      await downloadFile($FeatureGroupSelected.name, {
        fileFormat: "xlsx",
        groupId: $FeatureGroupSelected.id,
        lang: $Lang,
        minmaxScaling: scaled,
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
    <div class="scaling-toggle">
      <button class="scaling-toggle__btn" on:click={() => (scaled = !scaled)}>
        <Toggle value={scaled} />
      </button>
      <a
        class="scaling-toggle__text"
        class:emphasis={scaled}
        href={wikiUrl.scaling()}
        target="_blank"
        rel="noopener noreferrer"
      >
        Min-Max Scaling
      </a>
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
    z-index: 11;
    background-color: rgba(0, 0, 0, 0.4);
    display: flex;
    justify-content: center;
    align-items: center;
  }
  main {
    width: 30rem;
    height: 18rem;
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
  .scaling-toggle {
    display: flex;
    align-items: center;
    padding-left: 11rem;
    padding-top: 1.4rem;
  }
  .scaling-toggle__btn {
    position: relative;
  }
  .scaling-toggle__text {
    color: white;
    opacity: 0.4;
    font-size: 0.9rem;
    text-decoration: none;
    margin-left: 2rem;
  }
  .scaling-toggle__text:hover {
    border-bottom: thin solid white;
    cursor: pointer;
  }
</style>
