<script lang="ts">
  import WavingCubes from "../../assets/animation/WavingCubes.svelte";
  import CuteEmpty from "../../assets/icon/CuteEmpty.svelte";
  import { Text } from "../../modules/state";
  import { requestData } from "./function";
  import Chart from "./chart/Index.svelte";
  import Header from "./Header.svelte";
  export let params: any;

  const request = requestData(params.featureGroupId);
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
    <Header data={response} />
    <Chart data={response} />
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
</style>
