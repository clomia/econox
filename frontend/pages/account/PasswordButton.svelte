<script lang="ts">
  import Swal from "sweetalert2";
  import { Text, UserInfo } from "../../modules/state";
  import { api } from "../../modules/request";
  import { defaultSwalStyle, logout } from "../../modules/functions";
  import type { AxiosError } from "axios";

  const SwalStyle = {
    ...defaultSwalStyle,
    confirmButtonText: $Text.Submit,
    denyButtonText: $Text.Cancel,
  };

  const widget = async () => {
    let newPassword: string = "";
    let complete: boolean = false;
    await Swal.fire({
      ...SwalStyle,
      input: "password",
      text: $Text.EnterNewPassword,
      preConfirm: async (input: string) => {
        if (input.length < 6) {
          Swal.showValidationMessage($Text.IncorrectPasswordLength);
          return;
        }
        try {
          await api.public.post("/auth/send-password-reset-code", { email: $UserInfo["email"] });
          newPassword = input;
        } catch (error: any) {
          const e = error as AxiosError;
          if (e.response?.status === 429) {
            Swal.showValidationMessage($Text.TooManyRequests);
          } else {
            Swal.showValidationMessage($Text.UnexpectedError);
          }
        }
      },
    });
    if (!newPassword) {
      return;
    }
    await Swal.fire({
      ...SwalStyle,
      input: "text",
      text: $Text.PleaseEnterEmailConfirmCode,
      preConfirm: async (input: string) => {
        if (!input) {
          Swal.showValidationMessage($Text.InsufficientInput);
          return;
        }
        try {
          await api.public.patch("/user/password", {
            new_password: newPassword,
            confirm_code: input,
            email: $UserInfo["email"],
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
    });
    await logout();
  };
</script>

<button class="btn" on:click={widget}>{$Text.ChangePassword}</button>

<style>
  button {
    display: flex;
    justify-content: center;
    align-items: center;
    width: 100%;
    height: 2.5rem;
    border: thin solid var(--border-white);
    border-radius: 0.4rem;
    color: var(--white);
  }
  button:hover {
    cursor: pointer;
    background-color: rgba(255, 255, 255, 0.2);
  }
</style>
