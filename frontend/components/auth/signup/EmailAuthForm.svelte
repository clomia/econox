<script lang="ts">
    import { createEventDispatcher } from "svelte";
    import { publicRequest } from "../../../modules/requests";
    import type { AxiosResponse } from "axios";
    import LoadingAnimation from "../../../assets/LoadingAnimation.svelte";
    export let text: { [key: string]: string };
    export let inputResult: { [key: string]: string };

    let request: null | Promise<AxiosResponse> = null; // 요청 전
    let message = text.enterEmailVerificationCode;

    const dispatch = createEventDispatcher();

    async function confirmVerificationCode(event: SubmitEvent) {
        const form = event.target as HTMLFormElement;
        const email = inputResult.email;
        const verification_code = form.code.value;
        try {
            request = publicRequest.post("/auth/email", { email, verification_code });
            message = "";
            await request;
            dispatch("complete");
        } catch (error) {
            request = null;
            if (error.response.status === 409) {
                message = text.emailVerifiCodeMismatch; // 인증 코드가 올바르지 않음
            } else if (error.response.status === 401) {
                message = text.expiredEmailVerifiCode; // 인증 코드가 만료됌
            } else {
                message = text.error;
            }
        }
    }
</script>

<form on:submit|preventDefault={confirmVerificationCode}>
    <section>
        <label>
            <span>{inputResult.email}</span>
            <input type="text" name="code" required autocomplete="off" />
        </label>
    </section>
    {#await request}
        <LoadingAnimation />
    {/await}
    <div>{message}</div>
    {#if !(request instanceof Promise)}
        <button type="submit">{text.next}</button>
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
        padding-left: 1rem;
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
