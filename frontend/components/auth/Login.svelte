<script lang="ts">
    import { login } from "../../modules/functions";
    import { Text } from "../../modules/state";
    import { api } from "../../modules/request";
    import DefaultLoader from "../../assets/animation/DefaultLoader.svelte";
    import type { AxiosResponse } from "axios";

    let message = "";
    let response: null | Promise<AxiosResponse> = null; // 요청 전
    const loginProcess = async (event: SubmitEvent) => {
        message = "";
        const form = event.target as HTMLFormElement;
        const email = form.email.value;
        const password = form.password.value;
        if (!email || !password) {
            message = $Text.InsufficientInput;
            return;
        }
        try {
            response = api.public.post("/auth/user", { email, password });
            const result = await response;
            await login(result["cognito_token"], result["cognito_refresh_token"]);
        } catch (error) {
            response = null;
            const statusMessages = {
                404: $Text.LoginInfoIncorrect,
                401: $Text.LoginInfoIncorrect,
            };
            message = statusMessages[error.response?.status] || $Text.UnexpectedError;
        }
    };
</script>

<form on:submit|preventDefault={loginProcess}>
    <section>
        <label>
            <span>{$Text.Email}</span>
            <input type="text" name="email" autocomplete="email" />
        </label>
    </section>
    <section>
        <label>
            <span>{$Text.Password}</span>
            <input class="password-input" type="password" name="password" autocomplete="current-password" />
        </label>
    </section>
    {#await response}<DefaultLoader />{/await}
    <div>{message}</div>
    {#if !(response instanceof Promise)}
        <button type="submit">{$Text.Login}</button>
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
