<script lang="ts">
    import LoadingAnimation from "../../assets/LoadingAnimation.svelte";
    import * as state from "../../modules/state";
    import { login } from "../../modules/functions";
    const text = state.uiText.text;

    let message = "";
    let response: string | Promise<void> = "before"; // 요청 전
    const loginProcess = async (event: SubmitEvent) => {
        const form = event.target as HTMLFormElement;
        const email = form.email.value;
        const password = form.password.value;
        if (!email || !password) {
            message = $text.InsufficientInput;
            return;
        }
        try {
            response = login(email, password);
        } catch (error) {
            message = error.response?.status === 401 ? $text.LoginInfoIncorrect : $text.UnexpectedError;
        }
    };
</script>

<form on:submit|preventDefault={loginProcess}>
    <section>
        <label>
            <span>{$text.Email}</span>
            <input type="text" name="email" autocomplete="email" />
        </label>
    </section>
    <section>
        <label>
            <span>{$text.Password}</span>
            <input class="password-input" type="password" name="password" autocomplete="current-password" />
        </label>
    </section>
    {#await response}
        <LoadingAnimation />
    {/await}
    <div>{message}</div>
    {#if !(response instanceof Promise)}
        <button type="submit">{$text.Login}</button>
    {/if}
</form>

<style>
    form {
        display: flex;
        flex-direction: column;
        align-items: center;
        width: 100%;
        height: 16rem;
        margin-top: 2.5rem;
        color: white;
    }
    section {
        width: 24.5rem;
        margin-bottom: 1.7rem;
    }
    label span {
        display: block;
        color: rgba(255, 255, 255, 0.5);
        padding-left: 0.7rem;
        padding-bottom: 0.2rem;
        transition: color 100ms ease-out;
    }
    input {
        width: 100%;
        height: 2.5rem;
        border: solid thin white;
        border-radius: 0.7rem;
        color: white;
        text-align: center;
        letter-spacing: 0.14rem;
    }
    .password-input {
        letter-spacing: 0.6rem;
    }
    section:focus-within label span {
        color: rgba(255, 255, 255, 1);
    }
    button {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 15rem;
        height: 2.5rem;
        border: solid thin white;
        border-radius: 1rem;
        color: white;
        margin-top: 1.4rem;
    }
    button:hover {
        cursor: pointer;
        background-color: rgba(255, 255, 255, 0.2);
    }
</style>
