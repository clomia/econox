<script>
    import { onMount } from "svelte";
    import { fade } from "svelte/transition";
    import * as state from "../../../modules/state";
    import { request } from "../../../modules/api";
    import LoadingTextAnimation from "../../../assets/LoadingTextAnimation.svelte";
    import WellcomeAnimation from "../../../assets/WellcomeAnimation.svelte";
    import { login, format } from "../../../modules/functions";

    const inputResult = state.auth.signup.inputResult;
    const text = state.uiText.text;

    let response;
    let loginPromise;
    let timeout = 30;
    let animationEnd = false;

    const sucessRedirect = () => window.location.replace(window.location.origin + "/console");
    onMount(async () => {
        response = request.public.post("/user", {
            cognito_id: $inputResult.cognitoId,
            email: $inputResult.email,
            phone: $inputResult.phone,
            membership: $inputResult.membership,
            currency: $inputResult.currency,
            tosspayments: $inputResult.tosspayments,
            paypal: $inputResult.paypal,
        });
        await response;
        setTimeout(() => (animationEnd = true), 4300);
        loginPromise = login($inputResult.email, $inputResult.password, false);
        setInterval(() => {
            timeout -= 1;
            if (timeout <= 0) {
                sucessRedirect();
            }
        }, 1000);
    });

    const sucessMessage = (response) => {
        return response.data.first_signup_benefit ? $text.benefitsResultSummry : "";
    };

    const failureMessage = (error) => {
        const statusMessages = {
            401: $text.failureSignup401, // 이메일 인증 안됌
            402: $text.failureSignup402, // 결제 정보 필요한데 없음
            409: $text.failureSignup409,
        };
        return statusMessages[error.response?.status] || $text.error;
    };

    const cancelProcess = async () => {
        window.location.replace(window.location.origin);
    };
</script>

<main>
    {#if response}
        {#await response}
            <section class="loading">
                <LoadingTextAnimation />
            </section>
        {:then data}
            <section class="sucess">
                <div class="sucess__wellcome"><WellcomeAnimation /></div>
                <div class="sucess__title">{$text.sucessSignup}</div>
                <div class="sucess__message">{sucessMessage(data)}</div>
                <div class="sucess_login-timer">{format($text.loginTimer, { time: timeout })}</div>
                {#await loginPromise then}
                    {#if animationEnd}
                        <button on:click={sucessRedirect}>{$text.login}</button>
                    {/if}
                {/await}
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
        flex-direction: column;
        align-items: center;
        color: white;
    }
    .loading {
        margin-top: 3.5rem;
        height: 15rem;
    }
    .failure {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: space-between;
        height: 15rem;
    }
    .failure__message {
        margin-top: 5rem;
    }
    .failure__message,
    .sucess__title {
        font-size: 1.2rem;
    }
    .sucess {
        display: flex;
        flex-direction: column;
        align-items: center;
        width: 100%;
    }
    .sucess__wellcome {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        height: 22rem;
        width: 100%;
    }
    @keyframes fadeIn {
        0% {
            opacity: 0;
        }
        100% {
            opacity: 1;
        }
    }
    .sucess__title,
    .sucess__message {
        width: 88%;
        text-align: center;
        color: rgba(255, 255, 255, 0.9);
        opacity: 0;
        animation: fadeIn ease-in 1;
        animation-fill-mode: forwards;
        animation-duration: 1s;
        animation-delay: 4s;
    }
    .sucess__title {
        padding-bottom: 1rem;
    }
    .sucess__message {
        padding-bottom: 1rem;
    }
    .sucess_login-timer {
        padding-bottom: 2rem;
        color: rgba(255, 255, 255, 0.7);
        opacity: 0;
        animation: fadeIn ease-in 1;
        animation-fill-mode: forwards;
        animation-duration: 1s;
        animation-delay: 4.15s;
    }
    .sucess button {
        opacity: 0;
        animation: fadeIn ease-in 1;
        animation-fill-mode: forwards;
        animation-duration: 1s;
        animation-delay: 0;
    }
    button {
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
