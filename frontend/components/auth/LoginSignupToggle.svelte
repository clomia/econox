<script>
    import * as lang from "../../modules/lang";
    export let toggle; // Main 컴포넌트에서 양방향 바인딩으로 할당됩니다.

    const text = lang.setup();

    const color = {
        activate: "white",
        deactivate: "rgba(255, 255, 255, 0.3)",
    };

    function select(key) {
        toggle = { login: key === "login", signup: key === "signup" };
    }

    $: styles = {
        login: `border-bottom-color: ${toggle.login ? color.activate : color.deactivate}`,
        signup: `border-bottom-color: ${toggle.signup ? color.activate : color.deactivate}`,
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
