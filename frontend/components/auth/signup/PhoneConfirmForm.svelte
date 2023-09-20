<script lang="ts">
    import { createEventDispatcher, onMount } from "svelte";
    import * as state from "../../../modules/state";
    import { api } from "../../../modules/request";
    import { timeToString } from "../../../modules/functions";
    import LoadingAnimation from "../../../assets/LoadingAnimation.svelte";

    const text = state.uiText.text;
    const inputResult = state.auth.signup.inputResult;
    const phoneConfirmTimeLimit = state.auth.signup.phoneConfirmTimeLimit;
    const inputPhoneNumber = state.auth.signup.inputPhoneNumber;

    const dispatch = createEventDispatcher();

    let response: null | Promise<any> = null; // 요청 전
    let message = $text.PleaseEnterPhoneConfirmCode;

    if ($phoneConfirmTimeLimit === -1) {
        $phoneConfirmTimeLimit = 180;
    }
    onMount(() => setInterval(() => $phoneConfirmTimeLimit > 0 && $phoneConfirmTimeLimit--, 1000));

    $: placeHolder =
        $phoneConfirmTimeLimit > 0 ? timeToString($phoneConfirmTimeLimit) : $text.ConfirmCodeExpired;

    const codeConfirmation = async (event: SubmitEvent) => {
        message = "";
        const form = event.target as HTMLFormElement;
        try {
            const phoneConfirm = api.public.post("/auth/phone/confirm", {
                phone: $inputResult.phone,
                confirm_code: form.code.value,
            });
            const reregistrationConfirm = api.public.post("/auth/is-reregistration", {
                email: $inputResult.email,
                phone: $inputResult.phone,
            });
            response = Promise.all([phoneConfirm, reregistrationConfirm]);
            const [, reregistrationConfirmResponse] = await response;
            const reregistration: boolean = reregistrationConfirmResponse.data.reregistration; // 재등록 여부
            inputResult.set({ ...$inputResult, reregistration });
            dispatch("complete");
        } catch (error) {
            response = null;
            const statusMessage = {
                409: $text.ConfirmCodeMismatch, // 인증 코드가 올바르지 않음
                401: $text.ConfirmCodeAlreadyExpired, // 인증 코드가 만료됌
            };
            message = statusMessage[error.response?.status] || $text.UnexpectedError;
        }
    };

    const resendCode = async () => {
        try {
            response = api.public.post("/auth/phone", { phone: $inputResult.phone });
            await response;
            message = $text.codeSended;
            $phoneConfirmTimeLimit = 180;
        } catch (error) {
            message = error.response?.status === 429 ? $text.tooManyRequests : $text.UnexpectedError;
        }
        response = null;
    };
</script>

<form on:submit|preventDefault={codeConfirmation}>
    <section>
        <label>
            <span>{$inputPhoneNumber}</span>
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
