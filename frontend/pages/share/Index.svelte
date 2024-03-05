<script lang="ts">
  import { onMount } from "svelte";
  import Swal from "sweetalert2";
  import WavingCubes from "../../assets/animation/WavingCubes.svelte";
  import CuteEmpty from "../../assets/icon/CuteEmpty.svelte";
  import { Text } from "../../modules/state";
  import { requestData } from "./function";
  import Chart from "./chart/Index.svelte";
  import Header from "./Header.svelte";
  import Features from "./Features.svelte";
  export let params: any;

  let responseReceived = false;
  const request = requestData(params.featureGroupId);
  onMount(async () => {
    await request;
    responseReceived = true;
  });
  setTimeout(() => {
    if (!responseReceived) {
      Swal.fire({
        width: "46rem",
        toast: true,
        showConfirmButton: false,
        timer: 7000,
        timerProgressBar: true,
        position: "bottom-end",
        color: "var(--white)",
        background: "var(--widget-background)",
        title: $Text.RequestTimeout,
      });
    }
  }, 10000);

  const failedMessages = {
    404: $Text.PublicFg404,
    423: $Text.PublicFg423,
  };
</script>

{#await request}
  <div class="loading">
    <WavingCubes />
    <div class="loading__text">{$Text.Loading}</div>
  </div>
{:then response}
  {#if typeof response === "number"}
    <div class="failed">
      <CuteEmpty size={300} />
      <div class="failed__text">
        {failedMessages[response]}
      </div>
    </div>
  {:else}
    <div class="content">
      <Header data={response} />
      <Features data={response} />
      <Chart data={response} />
    </div>
  {/if}
{/await}

<style>
  .loading {
    display: flex;
    flex-direction: column;
    align-items: center;
    padding-top: 20vh;
  }
  .loading__text {
    margin-top: 7rem;
    color: var(--white);
    padding-left: 1.5rem;
    font-size: 1.2rem;
  }
  .failed {
    margin-top: 7vh;
    display: flex;
    flex-direction: column;
    align-items: center;
  }
  .failed__text {
    margin-top: 4rem;
    color: var(--white);
    font-size: 1.2rem;
  }
  .content {
    display: flex;
    flex-direction: column;
    align-items: center;
  }
</style>
