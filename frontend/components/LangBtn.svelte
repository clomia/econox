<script lang="ts">
    import { onMount } from "svelte";

    import LanguageIcon from "../assets/LanguageIcon.svelte";
    import * as state from "../modules/state";
    import { loadUiText, supportedLangs, changeLang } from "../modules/uiText";

    let lang = "";
    onMount(async () => {
        lang = (await loadUiText()).lang;
    });

    let toggle = false;
    const apply = async (event: Event) => {
        lang = (event.target as HTMLSelectElement).value;
        const { text } = await changeLang(lang);
        state.uiText.text.set(text);
        toggle = !toggle;
    };
</script>

{#await supportedLangs() then langs}
    <section>
        <button on:click={() => (toggle = !toggle)}> <LanguageIcon /> </button>
        {#if toggle}
            <select value={lang} on:change={apply}>
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
    }
    section button {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 3rem;
        height: 3rem;
        border-radius: 0.5rem;
        border: solid thin white;
        opacity: 0.6;
    }
    section button:hover {
        cursor: pointer;
        background-color: rgba(255, 255, 255, 0.16);
    }
    select {
        background: none;
        opacity: 0.6;
        border-radius: 0.5rem;
        border: solid thin white;
        color: white;
        margin: 0 0.5rem;
        padding: 0 1rem;
        width: 11rem;
    }
    select:hover {
        cursor: pointer;
        background-color: rgba(255, 255, 255, 0.16);
    }
</style>
