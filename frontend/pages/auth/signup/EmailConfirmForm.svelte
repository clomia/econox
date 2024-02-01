<script lang="ts">
  import { createEventDispatcher, onMount } from "svelte";
  import { api } from "../../../modules/request";
  import { secondToString, inputStrip } from "../../../modules/functions";
  import { Text, auth } from "../../../modules/state";
  import CircleDotLoader from "../../../assets/animation/CircleDotLoader.svelte";
  import type { AxiosResponse } from "axios";

  const dispatch = createEventDispatcher();

  const InputResult = auth.signup.InputResult;
  const EmailConfirmTimeLimit = auth.signup.EmailConfirmTimeLimit;

  let response: null | Promise<AxiosResponse> = null; // 요청 전
  let message: string = $Text.PleaseEnterEmailConfirmCode;

  if ($EmailConfirmTimeLimit === -1) {
    $EmailConfirmTimeLimit = 180;
  }

  const statusMessages = (statusCode: number | undefined) => {
    switch (statusCode) {
      case 401:
        return $Text.ConfirmCodeAlreadyExpired;
      case 409:
        return $Text.ConfirmCodeMismatch;
      case 429:
        return $Text.TooManyRequests;
      default:
        return $Text.UnexpectedError;
    }
  };

  onMount(() =>
    setInterval(
      () => $EmailConfirmTimeLimit > 0 && $EmailConfirmTimeLimit--,
      1000
    )
  );

  $: placeHolder =
    $EmailConfirmTimeLimit > 0
      ? secondToString($EmailConfirmTimeLimit)
      : $Text.ConfirmCodeExpired;

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
    } catch (error: any) {
      response = null;
      message = statusMessages(error?.response?.status);
    }
  };

  const resendCode = async () => {
    try {
      response = api.public.post("/auth/email", { email: $InputResult.email });
      await response;
      message = $Text.ConfirmCodeSended;
      $EmailConfirmTimeLimit = 180;
    } catch (error: any) {
      message = statusMessages(error?.response?.status);
    }
    response = null;
  };
</script>

<form on:submit|preventDefault={codeConfirmation}>
  <section>
    <label>
      <span>{$InputResult.email}</span>
      <input
        type="text"
        name="code"
        placeholder={placeHolder}
        autocomplete="off"
        on:input={inputStrip}
      />
    </label>
  </section>
  {#await response}<CircleDotLoader />{/await}
  {#if !(response instanceof Promise)}
    <div>{message}</div>
    <div class="buttons">
      <button type="button" on:click={resendCode}
        >{$Text.ResendConfirmCode}</button
      >
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
    height: 12rem;
    margin-top: 2.5rem;
    color: var(--white);
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
    border: thin solid var(--border-white);
    border-radius: 0.7rem;
    color: var(--white);
    padding: 0 1rem;
    text-align: center;
    letter-spacing: 0.3rem;
  }
  section:focus-within label span {
    color: white;
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
    border: thin solid var(--border-white);
    border-radius: 0.7rem;
    color: var(--white);
  }
  button:hover {
    cursor: pointer;
    background-color: rgba(255, 255, 255, 0.2);
  }
</style>
