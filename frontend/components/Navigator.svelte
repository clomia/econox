<script lang="ts">
    import Auth from "./auth/Index.svelte";
    import * as state from "../modules/state";

    let text = state.uiText.text;
    let authToggle = false;
</script>

<section>
    <button>Econox</button>
    <button>{$text.Console}</button>
    <button>{$text.FeatureHub}</button>
    <button on:click={() => (authToggle = !authToggle)}>{$text.SignInOut}</button>
</section>

{#if authToggle}
    <Auth />
{/if}

<style>
    section {
        display: flex;
        justify-content: center;
        padding: 3rem 0;
        white-space: nowrap;
    }

    section button {
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

    section button:hover {
        background-color: rgba(255, 255, 255, 0.16);
        cursor: pointer;
    }
</style>
