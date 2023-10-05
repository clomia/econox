<script lang="ts">
    import { auth } from "../../modules/state";
    import Login from "./Login.svelte";
    import Signup from "./signup/Index.svelte";
    import LoginSignupToggle from "./LoginSignupToggle.svelte";

    const Toggle = auth.Toggle;
</script>

<div class="ground">
    <div class="ground__window">
        <LoginSignupToggle />
        <section>
            {#if $Toggle.login}
                <Login />
            {:else}
                <Signup />
            {/if}
        </section>
    </div>
</div>

<style>
    .ground {
        display: flex;
        justify-content: center;
        align-items: start;
        position: absolute;
        top: 10rem;
        left: 0;
        right: 0;
        bottom: 0;
    }
    .ground__window {
        width: 34rem;
        padding: 3rem 4rem;
        border-radius: 0.6rem;
        border: thin solid rgba(255, 255, 255, 0.2);
        background: var(--widget-background);
    }
</style>
