<script lang="ts">
    import { onMount } from "svelte";
    import { currentLang, supportedLangs, changeLang } from "../modules/uiText";
    import LanguageIcon from "../assets/icon/LanguageIcon.svelte";

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
</script>

{#await supportedLangs() then langs}
    <section>
        <button on:click={() => (toggle = !toggle)}> <LanguageIcon /> </button>
        {#if toggle}
            <select bind:value={lang} on:change={apply}>
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
        border: thin solid var(--white);
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
        border: thin solid var(--white);
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
