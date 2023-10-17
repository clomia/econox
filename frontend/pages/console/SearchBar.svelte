<script lang="ts">
    import { fade } from "svelte/transition";
    import SearchArrow from "../../assets/icon/SearchArrow.svelte";
    import Magnifier from "../../assets/icon/Magnifier.svelte";
    import DotLoader from "../../assets/animation/DotLoader.svelte";
    import { api } from "../../modules/request";
    import { Text, Lang } from "../../modules/state";

    let inputText = "";
    let loading = false;
    const search = async () => {
        loading = true;
        const resp = await api.member.get("/data/elements", { params: { query: inputText, lang: $Lang } });
        loading = false;
        console.log(resp.data);
    };
</script>

<main>
    <form class="search-form" class:shadow-pulse={loading} on:submit|preventDefault={search}>
        <div class="magnifier"><Magnifier /></div>
        <input
            class="search"
            type="text"
            name="search"
            autocomplete="off"
            spellcheck="false"
            disabled={loading}
            placeholder={$Text.SearchBar_Placeholder}
            bind:value={inputText}
        />

        {#if loading}
            <div in:fade class="search-loader"><DotLoader /></div>
        {:else}
            <button in:fade class="search-btn"><SearchArrow /></button>
        {/if}
    </form>
</main>

<style>
    .search-form {
        display: flex;
        align-items: center;
        width: 44rem;
        height: 2.6rem;
        border-radius: 1.5rem;
        border: thin solid var(--border-white);
        box-shadow: 0 0 2rem 0.1rem rgba(0, 0, 0, 0.2);
        transition: border-color 150ms ease-out;
    }
    .search {
        width: 100%;
        height: 100%;
        color: var(--white);
    }
    .magnifier {
        margin-left: 1.4rem;
        margin-top: 0.2rem;
        margin-right: 0.8rem;
    }
    .search-btn {
        width: 5rem;
        height: 100%;
        display: flex;
        align-items: center;
        margin-right: 0.5rem;
        opacity: 0.3;
        transition: opacity 100ms ease-out;
    }
    .search-btn:hover {
        opacity: 0.8;
        cursor: pointer;
    }
    .search-loader {
        display: flex;
        width: 10rem;
        height: 2rem;
        margin-right: 1rem;
        align-items: center;
    }
    .search-loader:hover,
    .search:disabled:hover {
        cursor: wait;
    }
    @keyframes shadowPulse {
        0%,
        100% {
            box-shadow: 0 0 0.5rem 0.1rem rgba(255, 255, 255, 0);
        }
        50% {
            box-shadow: 0 0 1rem 0.1rem rgba(255, 255, 255, 0.2);
        }
    }
    .shadow-pulse {
        border-color: rgba(255, 255, 255, 0.5);
        animation: shadowPulse 1400ms infinite;
    }
</style>
