<script lang="ts">
  import { derived } from "svelte/store";

  import Magnifier from "../../../assets/icon/Magnifier.svelte";
  import MinusIcon from "../../../assets/icon/MinusIcon.svelte";
  import Check from "../../../assets/icon/Check.svelte";
  import { deleteElement, setFactors, attrQuerySort } from "./functions";
  import { Text, CountryCodeMap } from "../../../modules/state";
  import {
    UnivariateElements,
    UnivariateElementSelected,
    UnivariateNote,
    UnivariateFactorsProgress,
  } from "../../../modules/state";
  import type { ElementType } from "../../../modules/state";

  const select = async (ele: ElementType) => {
    $UnivariateElementSelected = ele;
    $UnivariateNote = ele.note;
    await setFactors(ele);
  };

  const Progress = derived(
    [UnivariateElements, UnivariateFactorsProgress],
    ([$UnivariateElements, $UnivariateFactorsProgress]) => {
      const progressObj: { [key: string]: number } = {};
      $UnivariateElements.forEach((ele) => {
        const key = `${ele.section}-${ele.code}`;
        progressObj[key] = $UnivariateFactorsProgress[key] || 0;
      });
      return progressObj;
    }
  );

  let query = "";
  let attr = "name";
  let view: any[] = [];

  $: if (query) {
    view = attrQuerySort($UnivariateElements, query, attr);
  } else {
    view = $UnivariateElements;
  }
  $: attrBtnText = attr === "name" ? $Text.Name : $Text.Code;

  const searchAttrChange = () => {
    if (attr === "name") {
      attr = "code";
    } else {
      attr = "name";
    }
  };
  const searchEventHandler = (event: any) => {
    const inputElement = event.target as HTMLInputElement;
    query = inputElement.value;
  };
</script>

<main>
  {#if $UnivariateElements.length}
    <div class="search">
      <Magnifier />
      <button class="search__attr-btn" on:click={searchAttrChange}
        >{attrBtnText}</button
      >
      <input class="search__input" type="text" on:input={searchEventHandler} />
    </div>
  {/if}
  <div class="list">
    {#each view as ele}
      {@const key = `${ele.section}-${ele.code}`}
      {@const progress = $Progress[key]}
      <button
        class="list__ele"
        on:click={() => select(ele)}
        class:selected={$UnivariateElementSelected === ele}
        class:list__ele_with_scroll={view.length >= 4}
      >
        <div class="list__ele__code">{ele.code}</div>
        <div class="list__ele__name">
          {ele.name}
          {#if ele.section === "country" && $CountryCodeMap}
            {@const code = $CountryCodeMap[ele.code].toLowerCase()}
            <img
              src={`https://flagcdn.com/w40/${code}.png`}
              alt={ele.name}
              width="30px"
            />
          {/if}
          <span class="progress">
            {#if 0 < progress && progress < 1}
              {Math.round(progress * 100)}%
            {:else if $UnivariateFactorsProgress[key] === 0}
              0%
            {:else if progress === 1}
              <Check />
            {/if}
          </span>
        </div>
        <button
          class="list__ele__del-btn"
          on:click={() => deleteElement(ele.code, ele.section)}
        >
          <MinusIcon size={1.2} />
        </button>
      </button>
    {:else}
      <div class="list-blank">{$Text.ElementsListBlank}</div>
    {/each}
  </div>
</main>

<style>
  main {
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
  .search__input {
    height: 100%;
    margin-left: 0.7rem;
    width: 83%;
    color: var(--white);
  }
  .search__attr-btn {
    margin-left: 0.7rem;
    padding: 0.2rem 0.5rem;
    border-radius: 0.2rem;
    background-color: rgba(255, 255, 255, 0.08);
    color: var(--white);
  }
  .search__attr-btn:hover {
    background-color: rgba(255, 255, 255, 0.18);
    cursor: pointer;
  }
  .list {
    margin: 1rem;
    /* 최소 4개 ~ 쵀대 6개 */
    min-height: 10.78rem;
    max-height: 16rem;
    overflow: auto;
  }
  .list__ele {
    width: 100%;
    display: flex;
    align-items: center;
    padding: 0.5rem 0;
    border: thin solid rgba(255, 255, 255, 0);
    position: relative;
  }
  .list__ele_with_scroll {
    width: 98%;
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
    border-radius: 0.15rem;
    margin: 0 0.5rem;
    color: var(--white);
    background-color: rgba(255, 255, 255, 0.2);
  }
  .list__ele__name {
    color: var(--white);
  }
  .progress {
    color: white;
    opacity: 0.3;
    margin-left: 0.2rem;
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
</style>
