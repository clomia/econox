<script lang="ts">
  import { onMount } from "svelte";
  import { currentLang, supportedLangs, changeLang } from "../modules/uiText";
  import LanguageIcon from "../assets/icon/LanguageIcon.svelte";

  export let url: string;

  let toggle = false;
  const apply = async (event: Event) => {
    await changeLang((event.target as HTMLSelectElement).value);
    location.reload(); // 레퍼런스 타는 변수들은 즉시 반영이 안돼서 reload하는게 가장 안전함
  };

  let lang = "";
  onMount(async () => {
    while (!lang) {
      lang = await currentLang();
      if (lang) break;
    } // App.svelte에서 언어 불러오는 시간 간극을 풀링으로 처리
  });

  $: isIntroPage = url === "/";
</script>

{#await supportedLangs() then langs}
  <section>
    <button
      on:click={() => (toggle = !toggle)}
      class:for-intro-page={isIntroPage}
    >
      <LanguageIcon />
    </button>
    {#if toggle}
      <select
        bind:value={lang}
        on:change={apply}
        class:for-intro-page={isIntroPage}
      >
        {#each Object.entries(langs) as [code, name]}
          <option value={code}>{name}</option>
        {/each}
      </select>
    {/if}
  </section>
{/await}

<style>
  section {
    display: flex;
    width: 17rem;
    height: 3rem;
    position: fixed;
    bottom: 2rem;
    left: 2rem;
    z-index: 10;
  }
  section button {
    display: flex;
    justify-content: center;
    align-items: center;
    width: 3rem;
    height: 3rem;
    border-radius: 0.5rem;
    border: thin solid var(--border-white);
    background-color: rgb(32, 49, 55);
    box-shadow: 0 0 2rem 0.1rem rgba(0, 0, 0, 0.3);
  }
  section button:hover {
    cursor: pointer;
    background-color: rgb(54, 63, 80);
  }
  select {
    border-radius: 0.5rem;
    border: thin solid var(--border-white);
    color: var(--white);
    margin: 0 0.5rem;
    padding: 0 1rem;
    width: 11rem;
    background-color: rgb(32, 49, 55);
    box-shadow: 0 0 2rem 0.1rem rgba(0, 0, 0, 0.3);
  }
  select:hover {
    cursor: pointer;
    background-color: rgb(54, 63, 80);
  }
  .for-intro-page {
    background-color: rgb(10, 10, 11);
  }
  .for-intro-page:hover {
    background-color: rgb(45, 45, 50);
  }
</style>
