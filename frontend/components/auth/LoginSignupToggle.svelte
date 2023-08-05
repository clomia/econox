<script lang="ts">
    import * as state from "../../modules/state";

    const text = state.uiText.text;
    const toggleState = state.auth.toggle;

    const color = {
        activate: "white",
        deactivate: "rgba(255, 255, 255, 0.3)",
    };

    const select = (key: string) => {
        toggleState.set({ login: key === "login", signup: key === "signup" });
    };

    $: styles = {
        login: `border-bottom-color: ${$toggleState.login ? color.activate : color.deactivate}`,
        signup: `border-bottom-color: ${$toggleState.signup ? color.activate : color.deactivate}`,
    };
</script>

<div class="toggle">
    <button on:click={() => select("login")} style={styles.login}>{$text.login}</button>
    <button on:click={() => select("signup")} style={styles.signup}>{$text.signup}</button>
</div>

<style>
    .toggle {
        display: flex;
        justify-content: center;
        width: 100%;
    }
    .toggle button {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 15rem;
        height: 2.2rem;
        color: white;
        border-bottom: 4px solid rgba(255, 255, 255, 0.3);
        transition: border-bottom-color 0.1s ease-in-out;
    }
    .toggle button:hover {
        cursor: pointer;
        background: linear-gradient(to top, rgba(255, 255, 255, 0.04), transparent);
    }
</style>
