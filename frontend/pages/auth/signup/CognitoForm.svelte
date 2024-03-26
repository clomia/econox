<script lang="ts">
  import { createEventDispatcher } from "svelte";
  import { api } from "../../../modules/request";
  import { Text, auth } from "../../../modules/state";
  import CircleDotLoader from "../../../assets/animation/CircleDotLoader.svelte";
  import CircleLoader from "../../../assets/animation/CircleLoader.svelte";
  import { inputStrip } from "../../../modules/functions";
  import type { AxiosResponse } from "axios";

  const InputResult = auth.signup.InputResult;

  const dispatch = createEventDispatcher();

  let response: null | Promise<AxiosResponse> = null; // 요청 전
  let message = "";

  const statusMessages = (statusCode: number | undefined) => {
    switch (statusCode) {
      case 400:
        return $Text.EmailInputIncorrect;
      case 409:
        return $Text.UserAlreadyExists;
      default:
        return $Text.UnexpectedError;
    }
  };

  const signup = async (event: SubmitEvent) => {
    message = "";
    const form = event.target as HTMLFormElement;
    const email = form.email.value as string;
    const password = form.password.value as string;
    const retypePassword = form.retypePassword.value as string;
    if (!email || !password) {
      message = $Text.InsufficientInput;
      return;
    }

    if (password !== retypePassword) {
      message = $Text.RetypePasswordMismatch;
      return;
    }

    if (password.length < 6) {
      message = $Text.IncorrectPasswordLength;
      return;
    }

    if (!email.includes("@") || !email.includes(".")) {
      message = $Text.EmailFormatIncorrect;
      return;
    }
    try {
      response = api.public.post("/user/cognito", { email, password });
      $InputResult = { ...$InputResult, email, password };
      document.body.style.overflow = "hidden";
      auth.signup.UserId.set((await response).data["cognito_id"]);
      document.body.style.overflow = "";
      dispatch("complete");
    } catch (error: any) {
      response = null;
      message = statusMessages(error?.response?.status);
    }
  };
</script>

<form on:submit|preventDefault={signup}>
  <section>
    <label>
      <span>{$Text.Email}</span>
      <input
        type="text"
        name="email"
        autocomplete="off"
        on:input={inputStrip}
      />
    </label>
  </section>
  <section>
    <label>
      <span>{$Text.Password}</span>
      <input
        class="password-input"
        type="password"
        name="password"
        autocomplete="off"
        on:input={inputStrip}
      />
    </label>
  </section>
  <section>
    <label>
      <span>{$Text.RetypePassword}</span>
      <input
        class="password-input"
        type="password"
        name="retypePassword"
        autocomplete="off"
        on:input={inputStrip}
      />
    </label>
  </section>
  {#await response}<CircleDotLoader />{/await}
  <div>{message}</div>
  {#if !(response instanceof Promise)}
    <button type="submit">{$Text.Next}</button>
  {/if}
</form>

{#await response}
  <div class="loader">
    <CircleLoader />
  </div>
{/await}

<style>
  .loader {
    width: 100vw;
    height: 100vh;
    position: fixed;
    top: 0;
    left: 0;
    z-index: 11;
    background-color: rgba(0, 0, 0, 0.4);
    display: flex;
    align-items: center;
    justify-content: center;
  }

  form {
    display: flex;
    flex-direction: column;
    align-items: center;
    width: 100%;
    height: 23rem;
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
    text-align: center;
    letter-spacing: 0.14rem;
  }
  .password-input {
    letter-spacing: 0.6rem;
  }
  section:focus-within label span {
    color: white;
  }
  button {
    display: flex;
    justify-content: center;
    align-items: center;
    width: 15rem;
    height: 2.5rem;
    border: thin solid var(--border-white);
    border-radius: 1rem;
    color: var(--white);
    margin-top: 1.4rem;
  }
  button:hover {
    cursor: pointer;
    background-color: rgba(255, 255, 255, 0.2);
  }
</style>
