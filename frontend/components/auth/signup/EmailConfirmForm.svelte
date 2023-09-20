<script lang="ts">
    import { createEventDispatcher, onMount } from "svelte";
    import * as state from "../../../modules/state";
    import { api } from "../../../modules/request";
    import { timeToString } from "../../../modules/functions";
    import LoadingAnimation from "../../../assets/LoadingAnimation.svelte";

    import type { AxiosResponse } from "axios";

    const text = state.uiText.text;
    const inputResult = state.auth.signup.inputResult;
    const emailConfirmTimeLimit = state.auth.signup.emailConfirmTimeLimit;

    const dispatch = createEventDispatcher();

    let response: null | Promise<AxiosResponse> = null; // 요청 전
    let message = $text.PleaseEnterEmailConfirmCode;

    if ($emailConfirmTimeLimit === -1) {
        $emailConfirmTimeLimit = 180;
    }

    onMount(() => setInterval(() => $emailConfirmTimeLimit > 0 && $emailConfirmTimeLimit--, 1000));

    $: placeHolder =
        $emailConfirmTimeLimit > 0 ? timeToString($emailConfirmTimeLimit) : $text.ConfirmCodeExpired;

    const codeConfirmation = async (event: SubmitEvent) => {
        message = "";
        const form = event.target as HTMLFormElement;
        const code = form.code.value;
        if (!code) {
            message = $text.missingInput;
            return;
        }
        try {
            response = api.public.post("/auth/email/confirm", {
                email: $inputResult.email,
                confirm_code: code,
            });
            await response;
            dispatch("complete");
        } catch (error) {
            response = null;
            const statusMessage = {
                409: $text.ConfirmCodeMismatch,
                401: $text.ConfirmCodeAlreadyExpired,
                429: $text.tooManyRequests,
            };
            message = statusMessage[error.response?.status] || $text.UnexpectedError;
        }
    };

    const resendCode = async () => {
        try {
            response = api.public.post("/auth/email", { email: $inputResult.email });
            await response;
            message = $text.codeSended;
            $emailConfirmTimeLimit = 180;
        } catch (error) {
            message = error.response?.status === 429 ? $text.tooManyRequests : $text.UnexpectedError;
        }
        response = null;
    };
</script>

<form on:submit|preventDefault={codeConfirmation}>
    <section>
        <label>
            <span>{$inputResult.email}</span>
            <input type="text" name="code" placeholder={placeHolder} autocomplete="off" />
        </label>
    </section>
    {#await response}
        <LoadingAnimation />
    {/await}
    {#if !(response instanceof Promise)}
        <div>{message}</div>
        <div class="buttons">
            <button type="button" on:click={resendCode}>{$text.resendCode}</button>
            <button type="submit">{$text.Next}</button>
        </div>
    {/if}
</form>

<style>
    form {
        display: flex;
        flex-direction: column;
        align-items: center;
        width: 100%;
        height: 10rem;
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
        padding: 0 1rem;
        text-align: center;
        letter-spacing: 0.3rem;
    }
    section:focus-within label span {
        color: rgba(255, 255, 255, 1);
    }
    .buttons {
        width: 100%;
        padding: 0 1rem;
        display: flex;
        justify-content: space-between;
        margin-top: 2rem;
    }
    button {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 10rem;
        height: 2.5rem;
        border: solid thin white;
        border-radius: 0.7rem;
        color: white;
    }
    button:hover {
        cursor: pointer;
        background-color: rgba(255, 255, 255, 0.2);
    }
</style>
