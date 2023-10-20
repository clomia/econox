<script lang="ts">
    import { verify } from "../../modules/functions";
    import { auth } from "../../modules/state";
    import Login from "./Login.svelte";
    import Signup from "./signup/Index.svelte";
    import LoginSignupToggle from "./LoginSignupToggle.svelte";

    verify({ conds: { login: false }, failRedirect: "/account" });
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
        margin-top: 2rem;
    }
    .ground__window {
        width: 34rem;
        padding: 3rem 4rem;
        border-radius: 0.6rem;
        border: thin solid rgba(255, 255, 255, 0.2);
        background: var(--widget-background);
        box-shadow: 0 0 2rem 0.1rem rgba(0, 0, 0, 0.5);
    }
</style>
