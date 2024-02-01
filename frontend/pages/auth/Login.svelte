<script lang="ts">
  import Swal from "sweetalert2";
  import {
    login,
    defaultSwalStyle,
    format,
    inputStrip,
  } from "../../modules/functions";
  import { Text } from "../../modules/state";
  import { api } from "../../modules/request";
  import CircleDotLoader from "../../assets/animation/CircleDotLoader.svelte";
  import CircleLoader from "../../assets/animation/CircleLoader.svelte";
  import type { AxiosResponse, AxiosError } from "axios";

  const statusMessages = (statusCode: number | undefined) => {
    switch (statusCode) {
      case 401:
      case 404:
        return $Text.LoginInfoIncorrect;
      default:
        return $Text.UnexpectedError;
    }
  };

  let message = "";
  let response: null | Promise<AxiosResponse> = null; // 요청 전
  const loginProcess = async (event: SubmitEvent) => {
    message = "";
    const form = event.target as HTMLFormElement;
    const email = form.email.value;
    const password = form.password.value;
    if (!email || !password) {
      message = $Text.InsufficientInput;
      return;
    }
    try {
      response = api.public.post("/auth/user", { email, password });
      const result = (await response).data;
      await login(result["cognito_token"], result["cognito_refresh_token"]);
    } catch (error: any) {
      response = null;
      message = statusMessages(error?.response?.status);
    }
  };
  let emailInput: HTMLInputElement;
  const SwalStyle = {
    ...defaultSwalStyle,
    confirmButtonText: $Text.Submit,
    denyButtonText: $Text.Cancel,
  };
  const resetPassword = async () => {
    let enteredEmail = "";
    let complete = false;
    await Swal.fire({
      ...SwalStyle,
      input: "text",
      text: $Text.ForgotPassword_EnterEmail,
      preConfirm: async (email: string) => {
        if (
          !email ||
          email.split("@").length !== 2 ||
          email.split(".").length < 2
        ) {
          Swal.showValidationMessage($Text.InvalidInput);
          return;
        }
        try {
          await api.private.post("/auth/send-password-reset-code", { email });
          enteredEmail = email;
        } catch (error: any) {
          const e = error as AxiosError;
          if (e.response?.status === 429) {
            Swal.showValidationMessage($Text.TooManyRequests);
          } else if (e.response?.status === 404) {
            Swal.showValidationMessage($Text.UserDoesNotExist);
          } else {
            Swal.showValidationMessage($Text.UnexpectedError);
          }
        }
      },
    });
    if (!enteredEmail) {
      return;
    }
    const manual = format($Text.f_ForgotPassword_EnterNewPassword, {
      email: enteredEmail,
    });
    await Swal.fire({
      ...SwalStyle,
      html: `
                <div style="font-size: 1rem;">${manual}</div>
                <input type="text" id="swal-input1" class="swal2-input" placeholder="${$Text.ConfirmCode}">
                <input type="password" id="swal-input2" class="swal2-input" placeholder="${$Text.NewPassword}">`,
      focusConfirm: false,
      preConfirm: async () => {
        const confirmCode = (
          document.getElementById("swal-input1") as HTMLInputElement
        ).value;
        const newPassword = (
          document.getElementById("swal-input2") as HTMLInputElement
        ).value;
        if (newPassword.length < 6) {
          Swal.showValidationMessage($Text.IncorrectPasswordLength);
          return;
        }
        try {
          await api.public.patch("/user/password", {
            new_password: newPassword,
            confirm_code: confirmCode,
            email: enteredEmail,
          });
          complete = true;
        } catch (error: any) {
          const e = error as AxiosError;
          if (e.response?.status === 429) {
            Swal.showValidationMessage($Text.TooManyRequests);
          } else if (e.response?.status === 409) {
            Swal.showValidationMessage($Text.ConfirmCodeMismatch);
          } else {
            Swal.showValidationMessage($Text.UnexpectedError);
          }
        }
      },
    });
    if (!complete) {
      return;
    }
    await Swal.fire({
      ...SwalStyle,
      text: $Text.PasswordChangeSuccessful,
      icon: "success",
      confirmButtonText: $Text.Ok,
      showLoaderOnConfirm: false,
      showDenyButton: false,
    });
    emailInput.value = enteredEmail;
  };
</script>

<form on:submit|preventDefault={loginProcess}>
  <section>
    <label>
      <span>{$Text.Email}</span>
      <input
        bind:this={emailInput}
        type="text"
        name="email"
        autocomplete="email"
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
        autocomplete="current-password"
        on:input={inputStrip}
      />
      <button on:click={resetPassword} type="button" class="reset-password-btn"
        >{$Text.ForgotPassword}</button
      >
    </label>
  </section>
  {#await response}<CircleDotLoader />{/await}
  <div>{message}</div>
  {#if !(response instanceof Promise)}
    <button type="submit" class="submit-btn">{$Text.Login}</button>
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
    z-index: 1;
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
    height: 18rem;
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
  .submit-btn {
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
  .submit-btn:hover {
    cursor: pointer;
    background-color: rgba(255, 255, 255, 0.2);
  }
  label {
    width: 100%;
    position: relative;
  }
  .reset-password-btn {
    position: absolute;
    right: 1rem;
    top: 0;
    opacity: 0.5;
    color: var(--white);
    transition: opacity 150ms ease-out;
  }
  .reset-password-btn:hover {
    opacity: 1;
    color: white;
    cursor: pointer;
  }
</style>
