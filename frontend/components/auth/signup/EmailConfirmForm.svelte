<script lang="ts">
    import { createEventDispatcher } from "svelte";

    import * as state from "../../../modules/state";
    import { publicRequest } from "../../../modules/api";
    import LoadingAnimation from "../../../assets/LoadingAnimation.svelte";

    import type { AxiosResponse } from "axios";

    const text = state.uiText.text;
    const inputResult = state.auth.signup.inputResult;
    const emailConfirmTimeLimit = state.auth.signup.emailConfirmTimeLimit;

    const dispatch = createEventDispatcher();

    let request: null | Promise<AxiosResponse> = null; // 요청 전
    let message = $text.enterEmailConfirmationCode;
    let expired = false;
    const countdown = async (totalSeconds: number) => {
        expired = false;
        while (totalSeconds >= 0) {
            const minutes = Math.floor(totalSeconds / 60);
            const seconds = (totalSeconds % 60).toString().padStart(2, "0");
            emailConfirmTimeLimit.update(() => `${minutes}:${seconds}`);
            await new Promise((resolve) => setTimeout(resolve, 1000));
            totalSeconds--;
        }
        emailConfirmTimeLimit.update(() => $text.confirmCodeExpiration);
        expired = true;
        message = "";
    };
    countdown(180); // Cognito 이메일 인증코드 유효기간 3분

    const codeConfirmation = async (event: SubmitEvent) => {
        message = "";
        const form = event.target as HTMLFormElement;
        const code = form.code.value;
        if (!code) {
            message = $text.missingInput;
            return;
        }
        try {
            request = publicRequest.post("/auth/email/confirm", {
                email: $inputResult.email,
                confirmation_code: code,
            });
            await request;
            dispatch("complete");
        } catch (error) {
            request = null;
            const statusMessage = {
                409: $text.confirmCodeMismatch, // 인증 코드가 올바르지 않음
                401: $text.expiredConfirmCode, // 인증 코드가 만료됌
                429: $text.tooManyRequests, // 요청 너무 많이함
            };
            message = statusMessage[error.response?.status] || $text.error;
        }
    };

    const resendCode = async () => {
        request = publicRequest.post("/auth/email", { email: $inputResult.email });
        await request;
        request = null;
        message = "인증 코드가 전송되었습니다";
        expired = false;
        countdown(180);
    };
</script>

<form on:submit|preventDefault={codeConfirmation}>
    <section>
        <label>
            <span>{$inputResult.email}</span>
            <input type="text" name="code" placeholder={$emailConfirmTimeLimit} autocomplete="off" />
        </label>
    </section>
    {#await request}
        <LoadingAnimation />
    {/await}
    <div>{message}</div>
    {#if !(request instanceof Promise)}
        {#if !expired}
            <button type="submit">{$text.next}</button>
        {:else}
            <button type="button" on:click={resendCode}>코드 재전송</button>
        {/if}
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
