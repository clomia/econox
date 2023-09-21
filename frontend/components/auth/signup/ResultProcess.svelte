<script lang="ts">
    import { onMount } from "svelte";
    import Swal from "sweetalert2";
    import * as state from "../../../modules/state";
    import { api } from "../../../modules/request";
    import LoadingTextAnimation from "../../../assets/LoadingTextAnimation.svelte";
    import WellcomeAnimation from "../../../assets/WellcomeAnimation.svelte";
    import { login, format } from "../../../modules/functions";

    import type { AxiosResponse, AxiosError } from "axios";

    const inputResult = state.auth.signup.inputResult;
    const currentStep = state.auth.signup.step;
    const paymentError = state.auth.signup.paymentError;
    const text = state.uiText.text;

    let response: null | Promise<any> = null;
    let loginPromise: null | Promise<void> = null;
    let timeout = 30;
    let animationEnd = false;
    let sucessBtn: HTMLButtonElement;

    const sucessRedirect = () => window.location.replace(window.location.origin + "/console");
    onMount(async () => {
        response = api.public.post("/user", {
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

    const sucessMessage = (response: AxiosResponse<any>) => {
        return response.data.first_signup_benefit ? $text.BenefitExplanation : "";
    };

    const failureMessage = (error: AxiosError): string => {
        if (error.response?.status === 402) {
            // 결제 실패인 경우 결제정보 입력 단계로 롤백
            $paymentError = true;
            $inputResult.tosspayments = null;
            $inputResult.paypal = null;
            $currentStep = 5;
        }
        const statusMessages = {
            401: $text.EmailConfirmIncompleted, // 이메일 인증 안됌
            409: $text.UnusualSignupRequest,
        };
        return statusMessages[error.response?.status] || $text.UnexpectedError;
    };

    const cancelProcess = async () => {
        window.location.replace(window.location.origin);
    };

    const focusOnExitBtnAlert = async (event: Event) => {
        if (animationEnd && event.target !== sucessBtn) {
            Swal.fire({
                title: $text.ClickLogin_for_SignupComplete,
                toast: true,
                position: "top",
                showConfirmButton: false,
                timer: 3000,
                timerProgressBar: true,
            });
        }
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
                <div class="sucess__title">{$text.SignupComplete}</div>
                <div class="sucess__message">{sucessMessage(data)}</div>
                <div class="sucess_login-timer">{format($text.AutoLoginTimer, { time: timeout })}</div>
                {#await loginPromise then}
                    {#if animationEnd}
                        <button bind:this={sucessBtn} on:click={sucessRedirect}>{$text.Login}</button>
                    {/if}
                {/await}
            </section>
        {:catch error}
            <section class="failure">
                <div class="failure__message">{failureMessage(error)}</div>
                <button on:click={cancelProcess}>{$text.Ok}</button>
            </section>
        {/await}
    {/if}
</main>

<svelte:body on:click={focusOnExitBtnAlert} />

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
