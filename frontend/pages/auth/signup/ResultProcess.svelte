<script lang="ts">
  import { onMount } from "svelte";
  import Swal from "sweetalert2";
  import { api } from "../../../modules/request";
  import {
    login,
    format,
    defaultToastStyle,
    navigate,
  } from "../../../modules/functions";
  import { Text, auth } from "../../../modules/state";
  import TextLoader from "../../../assets/animation/TextLoader.svelte";
  import Wellcome from "../../../assets/animation/Wellcome.svelte";

  import type { AxiosResponse, AxiosError } from "axios";

  const InputResult = auth.signup.InputResult;
  const Step = auth.signup.Step;
  const PaymentError = auth.signup.PaymentError;

  let response: null | Promise<any> = null;
  let loginPromise: null | Promise<AxiosResponse> = null;
  let timeout = 30;
  let animationEnd = false;
  let sucessBtn: HTMLButtonElement;

  const sucessRedirect = () => navigate("/console");
  onMount(async () => {
    response = api.public.post("/user", {
      email: $InputResult.email,
      phone: $InputResult.phone,
      membership: $InputResult.membership,
      currency: $InputResult.currency,
      tosspayments: $InputResult.tosspayments,
      paypal: $InputResult.paypal,
    });
    await response;
    setTimeout(() => (animationEnd = true), 4300);
    loginPromise = api.public.post("/auth/user", {
      email: $InputResult.email,
      password: $InputResult.password,
    });
    const authResult = (await loginPromise).data;
    login(
      authResult["cognito_token"],
      authResult["cognito_refresh_token"],
      false
    );
    setInterval(() => {
      timeout -= 1;
      if (timeout <= 0) {
        sucessRedirect();
      }
    }, 1000);
  });

  const sucessMessage = (response: AxiosResponse<any>) => {
    return response.data.first_signup_benefit ? $Text.BenefitExplanation : "";
  };

  const statusMessages = (statusCode: number | undefined) => {
    switch (statusCode) {
      case 401:
        return $Text.EmailConfirmIncompleted;
      case 409:
        return $Text.UnusualSignupRequest;
      default:
        return $Text.UnexpectedError;
    }
  };

  const failureMessage = (error: AxiosError): string => {
    if (error.response?.status === 402) {
      // 결제 실패인 경우 결제정보 입력 단계로 롤백
      $PaymentError = true;
      $InputResult.tosspayments = null;
      $InputResult.paypal = null;
      $Step = 5;
    }
    return statusMessages(error.response?.status);
  };

  const cancelProcess = async () => navigate("/");

  const focusOnExitBtnAlert = async (event: Event) => {
    if (animationEnd && event.target !== sucessBtn) {
      Swal.fire({
        ...defaultToastStyle,
        position: "bottom-end",
        title: $Text.ClickLogin_for_SignupComplete,
      });
    }
  };
</script>

<main>
  {#if response}
    {#await response}
      <section class="loading">
        <TextLoader />
      </section>
    {:then data}
      <div class="sucess__title">{$Text.SignupComplete}</div>
      <div class="sucess__message">{sucessMessage(data)}</div>
      <section class="sucess">
        <div class="sucess__wellcome"><Wellcome /></div>
        <div class="sucess_login-timer">
          {format($Text.f_AutoLoginTimer, { time: timeout })}
        </div>
        {#await loginPromise then}
          {#if animationEnd}
            <button bind:this={sucessBtn} on:click={sucessRedirect}>
              {$Text.Login}
            </button>
          {/if}
        {/await}
      </section>
    {:catch error}
      <section class="failure">
        <div class="failure__message">{failureMessage(error)}</div>
        <button on:click={cancelProcess}>{$Text.Ok}</button>
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
    color: var(--white);
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
    font-size: 1.2rem;
  }
  .sucess__title {
    margin-top: 2.5rem;
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
    color: var(--white);
    opacity: 0;
    animation: fadeIn ease-in 1;
    animation-fill-mode: forwards;
    animation-duration: 1s;
    animation-delay: 4s;
  }
  .sucess__title {
    padding-bottom: 1rem;
  }
  .sucess_login-timer {
    padding-bottom: 2rem;
    color: var(--white);
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
    border: thin solid var(--border-white);
    border-radius: 1rem;
    color: var(--white);
    z-index: 12;
  }
  button:hover {
    cursor: pointer;
    background-color: rgba(255, 255, 255, 0.2);
  }
</style>
