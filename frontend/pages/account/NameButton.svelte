<script lang="ts">
  import Swal from "sweetalert2";
  import { Text, UserInfo } from "../../modules/state";
  import { api } from "../../modules/request";
  import { strip } from "../../modules/functions";
  import { defaultSwalStyle, format } from "../../modules/functions";

  const SwalStyle = {
    ...defaultSwalStyle,
    confirmButtonText: $Text.Submit,
    denyButtonText: $Text.Cancel,
  };

  const widget = async () =>
    await Swal.fire({
      ...SwalStyle,
      input: "text",
      text: $Text.EnterNewName,
      preConfirm: async (newName: string) => {
        if (!newName) {
          Swal.showValidationMessage($Text.InsufficientInput);
          return;
        } else if (newName.length > 10) {
          Swal.showValidationMessage(format($Text.f_LengthLimit, { v: 10 }));
          return;
        }
        try {
          await api.private.patch("/user/name", { new_name: strip(newName) });
          location.reload();
        } catch {
          Swal.showValidationMessage($Text.UnexpectedError);
        }
      },
    });
</script>

<button on:click={widget}>
  <p class="btn-text">{$UserInfo["name"]}</p>
  <div>{$Text.Change}</div>
</button>

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
    position: relative;
  }
  div {
    position: absolute;
    display: none;
    width: 100%;
    height: 100%;
  }
  button:hover {
    cursor: pointer;
    background-color: rgba(255, 255, 255, 0.2);
  }
  button:hover p {
    display: none;
  }
  button:hover div {
    display: flex;
    justify-content: center;
    align-items: center;
  }
</style>
