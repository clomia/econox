<script lang="ts">
    import * as lang from "../modules/lang";
    import Auth from "./auth/Index.svelte";

    let authToggle = false;

    const text = lang.setup();
</script>

<header class="header">
    <button>ECONOX</button>
    <button>{$text.console}</button>
    <button>{$text.featureHub}</button>
    <button on:click={() => (authToggle = !authToggle)}>{$text.signInOut}</button>
</header>

{#if authToggle}
    <Auth />
{/if}

<style>
    .header {
        display: flex;
        justify-content: center;
        padding: 3rem 0;
        white-space: nowrap;
    }

    .header button {
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 0 0.7rem;
        width: 10rem;
        height: 2.4rem;
        color: white;
        border: solid white thin;
        border-radius: 2rem;
    }

    .header button:hover {
        background-color: rgba(255, 255, 255, 0.16);
        cursor: pointer;
    }
</style>
