<script lang="ts">
    import { navigate } from "svelte-routing";
    import { UserInfo, Text } from "../modules/state";
    import Auth from "./auth/Index.svelte";
    import type { UserDetail } from "../modules/state";

    let userDetail = $UserInfo as UserDetail;
    let authToggle = false;
</script>

<section>
    <button>{$Text.Econox}</button>
    <button>{$Text.Console}</button>
    <button>{$Text.FeatureHub}</button>
    {#if $UserInfo}
        <button on:click={() => navigate("/account")}>
            <img src="static/img/profile.png" alt="profile" />
            <div class="username">{userDetail["name"]}</div>
        </button>
    {:else}
        <button on:click={() => (authToggle = !authToggle)}>{$Text.SignInOut}</button>
    {/if}
</section>

{#if authToggle}
    <Auth />
{/if}

<style>
    img {
        width: 1.6rem;
        height: 1.6rem;
        position: absolute;
        left: 0.4rem;
    }
    .username {
        margin-left: 1rem;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
        width: 6rem;
    }
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
        color: var(--white);
        border: solid var(--white) thin;
        border-radius: 2rem;
        position: relative;
    }

    section button:hover {
        background-color: rgba(255, 255, 255, 0.16);
        cursor: pointer;
    }
</style>
