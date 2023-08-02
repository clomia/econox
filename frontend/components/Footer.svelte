<script lang="ts">
    import { onMount } from "svelte";
    import * as lang from "../modules/lang";
    import LanguageIcon from "../assets/LanguageIcon.svelte";
    import type { LangInfo } from "../modules/lang";

    // 비동기라서 먼저 초기값을 세팅해야지 undifined 에러가 안남
    let langInfo: LangInfo = { pin: "", base: "", langs: {}, contents: {} };
    onMount(async () => {
        langInfo = await lang.init();
    }); // 새로고침 시 서버의 데이터가 다시 반영되도록

    let langToggle = false;
    async function langChange(event: Event) {
        const targetLang = (event.target as HTMLSelectElement).value;
        await lang.update(targetLang);
        window.location.reload(); // 새로고침
    }
</script>

<footer>
    <section class="lang">
        <button on:click={() => (langToggle = !langToggle)}> <LanguageIcon /> </button>
        {#if langToggle}
            <select class="lang__menu" value={langInfo.pin} on:change={langChange}>
                {#each Object.entries(langInfo.langs) as [code, name]}
                    <option value={code}>{name}</option>
                {/each}
            </select>
        {/if}
    </section>
</footer>

<style>
    .lang {
        display: flex;
        width: 17rem;
        height: 3rem;
        position: fixed;
        bottom: 2rem;
        left: 2rem;
    }
    .lang button {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 3rem;
        height: 3rem;
        border-radius: 0.5rem;
        border: solid thin white;
        opacity: 0.6;
    }
    .lang button:hover {
        cursor: pointer;
        background-color: rgba(255, 255, 255, 0.16);
    }
    .lang__menu {
        background: none;
        opacity: 0.6;
        border-radius: 0.5rem;
        border: solid thin white;
        color: white;
        margin: 0 0.5rem;
        padding: 0 1rem;
        width: 11rem;
    }
    .lang__menu:hover {
        cursor: pointer;
        background-color: rgba(255, 255, 255, 0.16);
    }
</style>
