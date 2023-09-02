<script lang="ts">
    import { createEventDispatcher } from "svelte";

    import * as state from "../../../modules/state";
    import { request } from "../../../modules/api";
    import LoadingAnimation from "../../../assets/LoadingAnimation.svelte";

    import type { AxiosResponse } from "axios";

    const text = state.uiText.text;
    const inputResult = state.auth.signup.inputResult;

    const dispatch = createEventDispatcher();

    let response: null | Promise<AxiosResponse> = null; // 요청 전
    let message = "";

    const signup = async (event: SubmitEvent) => {
        message = "";
        const form = event.target as HTMLFormElement;
        const email = form.email.value as string;
        const password = form.password.value as string;
        const retypePassword = form.retypePassword.value as string;
        if (!email || !password) {
            message = $text.missingInput;
            return;
        }

        if (password !== retypePassword) {
            message = $text.passwordMismatch;
            return;
        }

        if (password.length < 6) {
            message = $text.passwordLengthWarning;
            return;
        }

        if (!email.includes("@") || !email.includes(".")) {
            message = $text.emailFormatError;
            return;
        }
        try {
            response = request.public.post("/user/cognito", { email, password });
            const cognitoId = (await response).data.cognito_id;
            inputResult.set({ ...$inputResult, cognitoId, email, password });
            dispatch("complete");
        } catch (error) {
            response = null;
            const statusMessages = {
                409: $text.alreadyExistsUser,
                400: $text.invalidEmailInput,
            };
            message = statusMessages[error.response?.status] || $text.error;
        }
    };
</script>

<form on:submit|preventDefault={signup}>
    <section>
        <label>
            <span>{$text.email}</span>
            <input type="text" name="email" autocomplete="email" />
        </label>
    </section>
    <section>
        <label>
            <span>{$text.password}</span>
            <input class="password-input" type="password" name="password" autocomplete="off" />
        </label>
    </section>
    <section>
        <label>
            <span>{$text.retypePassword}</span>
            <input class="password-input" type="password" name="retypePassword" autocomplete="off" />
        </label>
    </section>
    {#await response}
        <LoadingAnimation />
    {/await}
    <div>{message}</div>
    {#if !(response instanceof Promise)}
        <button type="submit">{$text.next}</button>
    {/if}
</form>

<style>
    form {
        display: flex;
        flex-direction: column;
        align-items: center;
        width: 100%;
        height: 23rem;
        margin-top: 2.5rem;
        color: white;
        text-align: center;
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
