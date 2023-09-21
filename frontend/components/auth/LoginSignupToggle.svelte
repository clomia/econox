<script lang="ts">
    import { Text, auth } from "../../modules/state";

    const Toggle = auth.Toggle;

    const color = {
        activate: "white",
        deactivate: "rgba(255, 255, 255, 0.3)",
    };

    const select = (key: string) => {
        $Toggle = { login: key === "login", signup: key === "signup" };
    };

    $: styles = {
        login: `border-bottom-color: ${$Toggle.login ? color.activate : color.deactivate}`,
        signup: `border-bottom-color: ${$Toggle.signup ? color.activate : color.deactivate}`,
    };
</script>

<div class="toggle">
    <button on:click={() => select("login")} style={styles.login}>{$Text.Login}</button>
    <button on:click={() => select("signup")} style={styles.signup}>{$Text.Signup}</button>
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
