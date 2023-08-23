<script>
    import { onMount } from "svelte";
    import * as state from "../../../modules/state";
    import { publicRequest } from "../../../modules/api";
    import LoadingAnimation from "../../../assets/LoadingAnimation.svelte";
    import { login } from "../../../modules/functions";

    const inputResult = state.auth.signup.inputResult;
    const text = state.uiText.text;

    let request;
    onMount(async () => {
        request = publicRequest.post("/user", {
            cognito_id: $inputResult.cognitoId,
            email: $inputResult.email,
            phone: $inputResult.phone,
            membership: $inputResult.membership,
            currency: $inputResult.currency,
            tosspayments: $inputResult.tosspayments,
            paypal: $inputResult.paypal,
        });
        await request;
    });

    const sucessMessage = (response) => {
        return response.data.benefit ? $text.benefitsResultSummry : "";
    };

    const failureMessage = (error) => {
        const statusMessages = {
            401: $text.failureSignup401, // 이메일 인증 안됌
            402: $text.failureSignup402, // 결제 정보 필요한데 없음
            409: $text.failureSignup409,
        };
        return statusMessages[error.response?.status] || $text.error;
    };

    const loginProcess = async () => {
        login($inputResult.email, $inputResult.password);
    };

    const cancelProcess = async () => {
        window.location.replace(window.location.origin);
    };
</script>

<main>
    {#if request}
        {#await request}
            <section class="loading">
                <LoadingAnimation scale={2.3} />
            </section>
        {:then response}
            <section class="sucess">
                <div class="sucess__title">{$text.sucessSignup}</div>
                <div class="sucess__message">{sucessMessage(response)}</div>
                <button on:click={loginProcess}>{$text.ok}</button>
            </section>
        {:catch error}
            <section class="failure">
                <div class="failure__message">{failureMessage(error)}</div>
                <button on:click={cancelProcess}>{$text.ok}</button>
            </section>
        {/await}
    {/if}
</main>

<style>
    main {
        display: flex;
        position: relative;
        flex-direction: column;
        align-items: center;
        height: 15rem;
        color: white;
    }
    .loading {
        margin-top: 3.5rem;
    }
    .failure {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 100%;
        padding-bottom: 3.5rem;
    }
    .failure__message,
    .sucess__title {
        font-size: 1.3rem;
    }
    .sucess {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 100%;
    }
    .sucess__message {
        margin-top: 2.5rem;
        margin-bottom: 1rem;
        width: 88%;
        text-align: center;
        color: rgba(255, 255, 255, 0.7);
    }
    button {
        position: absolute;
        bottom: 0;
        padding: 0.5rem 2rem;
        border: thin solid white;
        border-radius: 1rem;
        color: white;
    }
    button:hover {
        cursor: pointer;
        background-color: rgba(255, 255, 255, 0.2);
    }
</style>
