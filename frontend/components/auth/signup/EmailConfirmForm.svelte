<script lang="ts">
    import { createEventDispatcher, onMount } from "svelte";
    import { api } from "../../../modules/request";
    import { timeToString } from "../../../modules/functions";
    import LoadingAnimation from "../../../assets/LoadingAnimation.svelte";
    import { Text, auth } from "../../../modules/state";
    import type { AxiosResponse } from "axios";

    const dispatch = createEventDispatcher();

    const InputResult = auth.signup.InputResult;
    const EmailConfirmTimeLimit = auth.signup.EmailConfirmTimeLimit;

    let response: null | Promise<AxiosResponse> = null; // 요청 전
    let message = $Text.PleaseEnterEmailConfirmCode;

    if ($EmailConfirmTimeLimit === -1) {
        $EmailConfirmTimeLimit = 180;
    }

    onMount(() => setInterval(() => $EmailConfirmTimeLimit > 0 && $EmailConfirmTimeLimit--, 1000));

    $: placeHolder =
        $EmailConfirmTimeLimit > 0 ? timeToString($EmailConfirmTimeLimit) : $Text.ConfirmCodeExpired;

    const codeConfirmation = async (event: SubmitEvent) => {
        message = "";
        const form = event.target as HTMLFormElement;
        const code = form.code.value;
        if (!code) {
            message = $Text.InsufficientInput;
            return;
        }
        try {
            response = api.public.post("/auth/email/confirm", {
                email: $InputResult.email,
                confirm_code: code,
            });
            await response;
            dispatch("complete");
        } catch (error) {
            response = null;
            const statusMessage = {
                409: $Text.ConfirmCodeMismatch,
                401: $Text.ConfirmCodeAlreadyExpired,
                429: $Text.TooManyRequests,
            };
            message = statusMessage[error.response?.status] || $Text.UnexpectedError;
        }
    };

    const resendCode = async () => {
        try {
            response = api.public.post("/auth/email", { email: $InputResult.email });
            await response;
            message = $Text.ConfirmCodeSended;
            $EmailConfirmTimeLimit = 180;
        } catch (error) {
            message = error.response?.status === 429 ? $Text.TooManyRequests : $Text.UnexpectedError;
        }
        response = null;
    };
</script>

<form on:submit|preventDefault={codeConfirmation}>
    <section>
        <label>
            <span>{$InputResult.email}</span>
            <input type="text" name="code" placeholder={placeHolder} autocomplete="off" />
        </label>
    </section>
    {#await response}
        <LoadingAnimation />
    {/await}
    {#if !(response instanceof Promise)}
        <div>{message}</div>
        <div class="buttons">
            <button type="button" on:click={resendCode}>{$Text.ResendConfirmCode}</button>
            <button type="submit">{$Text.Next}</button>
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
