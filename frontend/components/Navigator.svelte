<script lang="ts">
    import Auth from "./auth/Index.svelte";
    import { UserInfo, Text } from "../modules/state";

    let authToggle = false;
</script>

<section>
    <button>{$Text.Econox}</button>
    <button>{$Text.Console}</button>
    <button>{$Text.FeatureHub}</button>
    {#if $UserInfo}
        <button>{$UserInfo["name"]}</button>
    {:else}
        <button on:click={() => (authToggle = !authToggle)}>{$Text.SignInOut}</button>
    {/if}
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
