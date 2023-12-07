<script lang="ts">
  import Magnifier from "../../../assets/icon/Magnifier.svelte";
  import MinusIcon from "../../../assets/icon/MinusIcon.svelte";
  import { Text, UnivariateElements, UnivariateNote, CountryCodeMap } from "../../../modules/state";
  import { deleteElement } from "./functions";
  import type { ElementType } from "../../../modules/state";

  let selected: ElementType;
  const select = (ele: ElementType) => {
    selected = ele;
    $UnivariateNote = ele.note;
  };

  let scrolled = false;
  const scrollHandler = () => {
    scrolled = true;
  };
</script>

<main>
  {#if $UnivariateElements.length}
    <div class="search"><Magnifier /> <input type="text" /></div>
  {/if}
  <div class="list" on:scroll={scrollHandler}>
    {#each $UnivariateElements as ele}
      <button class="list__ele" on:click={() => select(ele)} class:selected={selected === ele}>
        <div class="list__ele__code">{ele.code}</div>
        <div class="list__ele__name">
          {ele.name}
          {#if ele.section === "country" && $CountryCodeMap}
            {@const code = $CountryCodeMap[ele.code].toLowerCase()}
            <img src={`https://flagcdn.com/w40/${code}.png`} alt={ele.name} width="30px" />
          {/if}
        </div>
        <button class="list__ele__del-btn" on:click={() => deleteElement(ele.code, ele.section)}>
          <MinusIcon size={1.2} />
        </button>
      </button>
    {:else}
      <div class="list-blank">{$Text.ElementsListBlank}</div>
    {/each}
  </div>
  {#if !scrolled && $UnivariateElements.length > 4}
    <div class="scroll-guide">스크롤하여 더보기</div>
  {/if}
</main>

<style>
  main {
    border-bottom: thin solid rgba(255, 255, 255, 0.2);
    position: relative;
  }
  .list-blank {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: rgba(255, 255, 255, 0.5);
  }
  .search {
    display: flex;
    align-items: center;
    padding-left: 0.8rem;
    height: 2.6rem;
    border-bottom: thin solid rgba(255, 255, 255, 0.2);
  }
  .search input {
    height: 100%;
    margin-left: 0.7rem;
    width: 90%;
    color: var(--white);
  }
  .list {
    margin: 1rem;
    height: 10.78rem;
    overflow: scroll;
  }
  .list__ele {
    width: 100%;
    display: flex;
    align-items: center;
    padding: 0.5rem 0;
    border-radius: 0.35rem;
    border: thin solid rgba(255, 255, 255, 0);
    position: relative;
  }
  .list__ele.selected {
    border-color: rgba(255, 255, 255, 0.2);
  }
  .list__ele:hover {
    background-color: rgba(255, 255, 255, 0.07);
    cursor: pointer;
  }
  .list__ele__code {
    padding: 0.2rem 0.4rem;
    border-radius: 0.2rem;
    margin: 0 0.5rem;
    color: var(--white);
    background-color: rgba(255, 255, 255, 0.2);
  }
  .list__ele__name {
    color: var(--white);
  }
  .list__ele__del-btn {
    width: 2rem;
    height: 2rem;
    position: absolute;
    right: 0.5rem;
    border-radius: 0.3rem;
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0.7;
  }
  .list__ele__del-btn:hover {
    background-color: rgba(255, 255, 255, 0.1);
    cursor: pointer;
    opacity: 1;
  }
  .scroll-guide {
    position: absolute;
    bottom: 0;
    display: flex;
    width: 100%;
    justify-content: center;
    align-items: start;
    color: var(--white);
    background-color: rgba(0, 0, 0, 0.2);
    padding: 0.15rem 0;
  }
</style>
