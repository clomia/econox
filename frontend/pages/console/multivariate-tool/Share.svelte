<script lang="ts">
  import Swal from "sweetalert2";
  import { onMount } from "svelte";
  import { createEventDispatcher } from "svelte";
  import CloseButton from "../../../components/CloseButton.svelte";
  import LinkIcon from "../../../assets/icon/LinkIcon.svelte";
  import RippleLoader from "../../../assets/animation/RippleLoader.svelte";
  import {
    Text,
    FeatureGroupSelected,
    FeatureGroups,
  } from "../../../modules/state";
  import { api } from "../../../modules/request";
  import { format } from "../../../modules/functions";

  $: chartName = {
    line: $Text.FgLineChart_Name,
    ratio: $Text.FgRatioChart_Name,
    granger: $Text.FgGrangerChart_Name,
    coint: $Text.FgCointChart_Name,
  }[$FeatureGroupSelected.chart_type];

  onMount(() => {
    document.body.style.overflow = "hidden";
  });

  const toPublic = (v: boolean) => {
    $FeatureGroupSelected.public = v;
    $FeatureGroups = $FeatureGroups.map((fg) => {
      if (fg.id === $FeatureGroupSelected.id) {
        return { ...fg, public: v };
      } else {
        return fg;
      }
    });
  };

  const apiRequest = async () => {
    if (!$FeatureGroupSelected.public) {
      // to public
      await api.member.patch("/feature/group", {
        group_id: $FeatureGroupSelected.id,
        public: true,
      });
      toPublic(true);
    }
  };
  const request = apiRequest();

  const dispatch = createEventDispatcher();
  const close = () => {
    document.body.style.overflow = "";
    dispatch("close");
  };

  const shareUrl =
    window.location.protocol +
    "//" +
    window.location.host +
    `/share/${$FeatureGroupSelected.id}`;
  const urlCopy = async () => {
    await navigator.clipboard.writeText(shareUrl);
    Swal.fire({
      width: "25rem",
      toast: true,
      showConfirmButton: false,
      timer: 2000,
      timerProgressBar: true,
      position: "top",
      color: "var(--white)",
      background: "var(--widget-background)",
      title: $Text.Copied,
      grow: "row",
    });
  };
  const unpublish = () => {
    api.member.patch("/feature/group", {
      group_id: $FeatureGroupSelected.id,
      public: false,
    });
    toPublic(false);
    close();
  };
</script>

<div class="bg">
  {#await request}
    <div class="loading">
      <RippleLoader size={1.5} />
    </div>
  {:then _}
    <main>
      <button class="close" on:click={close}><CloseButton /></button>
      <div class="title">{$Text.OnPublicTitle}</div>
      <div class="link">
        <LinkIcon size="16px" />
        <a href={shareUrl} target="_blank" rel="noopener noreferrer">
          {shareUrl}
        </a>
      </div>
      <div class="btn">
        <button class="btn__unpublish" on:click={unpublish}>
          {$Text.Unpublish}
        </button>
        <button class="btn__copy" on:click={urlCopy}>{$Text.CopyURL}</button>
      </div>
      <div class="desc">
        <div class="desc__1">{$Text.PublishGuide}</div>
        <div class="desc__2">
          {format($Text.f_NowDefaultChart, { chartName })}
        </div>
      </div>
    </main>
  {/await}
</div>

<style>
  .bg {
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
  .loading {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
  }
  main {
    width: 30rem;
    height: 15rem;
    background: var(--widget-background);
    border: thin solid rgba(255, 255, 255, 0.15);
    border-radius: 0.2rem;
    position: relative;
    display: flex;
    flex-direction: column;
    align-items: center;
  }
  .close {
    position: absolute;
    right: 0.5rem;
    top: 0.5rem;
  }
  .title {
    text-align: center;
    font-size: 1.2rem;
    margin-top: 1rem;
    color: var(--white);
  }
  .link {
    display: flex;
    align-items: center;
    justify-content: center;
    margin-top: 1rem;
  }
  .link a {
    margin-left: 0.4rem;
    text-decoration: none;
    color: white;
    opacity: 0.7;
  }
  .link a:hover {
    cursor: pointer;
    opacity: 0.9;
    text-decoration: underline;
  }
  .btn {
    display: flex;
    justify-content: space-evenly;
    width: 21rem;
  }
  .btn__copy,
  .btn__unpublish {
    color: var(--white);
    border: thin solid rgba(255, 255, 255, 0.5);
    margin: 1.3rem 0;
    padding: 0.5rem 1rem;
    border-radius: 0.2rem;
  }
  .btn__copy:hover,
  .btn__unpublish:hover {
    cursor: pointer;
    background-color: rgba(255, 255, 255, 0.15);
  }
  .desc {
    color: var(--white);
    padding: 1rem;
    padding-top: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
  }
</style>
