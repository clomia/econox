<script lang="ts">
    import { createEventDispatcher } from "svelte";
    import { getCodes, getName } from "country-list";
    import { getCountryCallingCode } from "libphonenumber-js";

    import * as state from "../../../modules/state";
    import { api } from "../../../modules/request";
    import LoadingAnimation from "../../../assets/LoadingAnimation.svelte";

    import type { CountryCode } from "libphonenumber-js";

    const text = state.uiText.text;
    const inputResult = state.auth.signup.inputResult;
    const inputPhoneNumberStore = state.auth.signup.inputPhoneNumber;

    const dispatch = createEventDispatcher();

    let response = null;
    let message = "";
    let phoneNumber = "";
    $: phoneNumber = phoneNumber.replace(/\D/g, "");

    const phoneConfirm = async (event: SubmitEvent) => {
        message = "";
        const form = event.target as HTMLFormElement;
        const callingCode = getCountryCallingCode(form.countryCode.value as CountryCode);
        const phone = `+${callingCode}${phoneNumber}`; // "-" & 공백 제거}
        if (!phoneNumber) {
            message = $text.noPhoneNumber;
            return;
        }
        // 앞에 + 빼고 숫자만 있는지 검사
        if (/\D/.test(phone.slice(1))) {
            message = $text.phoneNumberNotNumber;
            return;
        }
        try {
            response = api.public.post("/auth/phone", { phone });
            await response;
            $inputResult = { ...$inputResult, phone };
            $inputPhoneNumberStore = phoneNumber;
            dispatch("complete");
        } catch (error) {
            response = null;
            message = $text.phoneConfirmRequestFailed;
        }
    };
</script>

<div class="description">{$text.phoneConfirmDescription}</div>

<form on:submit|preventDefault={phoneConfirm}>
    {#await api.public.get("/user/country") then response}
        <label>
            <span>{$text.country}</span>
            <select name="countryCode" value={response.data.country}>
                {#each getCodes() as country}
                    <option value={country}>{getName(country)}</option>
                {/each}
            </select>
        </label>
    {/await}
    <label class="phone-number">
        <span>{$text.inputPhoneNumber}</span>
        <input bind:value={phoneNumber} name="phone" type="text" />
    </label>
    <div class="message">{message}</div>
    {#if !(response instanceof Promise)}
        <button>{$text.sendVerificationCode}</button>
    {/if}
    {#await response}
        <LoadingAnimation />
    {/await}
</form>

<style>
    .description {
        color: rgba(255, 255, 255, 0.8);
        text-align: center;
        margin-top: 2rem;
        padding: 0 3rem;
    }
    form {
        display: flex;
        flex-direction: column;
        align-items: center;
        width: 100%;
        height: 21rem;
        margin-top: 1.5rem;
        color: white;
    }
    label {
        margin-bottom: 3rem;
    }
    label span {
        display: block;
        width: 100%;
        color: rgba(255, 255, 255, 0.7);
        margin-bottom: 0.5rem;
        text-align: center;
    }
    select {
        width: 25rem;
        border-radius: 1rem;
        border: solid thin white;
        color: white;
        margin: 0 0.5rem;
        padding: 0 1rem;
        height: 3rem;
    }
    select:hover {
        cursor: pointer;
        background-color: rgba(255, 255, 255, 0.16);
    }
    option {
        text-align: center;
    }
    label input {
        width: 25rem;
        border-radius: 1rem;
        border: solid thin white;
        color: white;
        padding: 0 1rem;
        height: 3rem;
        text-align: center;
        letter-spacing: 0.24rem;
    }
    .phone-number {
        margin-bottom: 0;
    }
    .phone-number span {
        transition: color 100ms ease-out;
    }
    .phone-number:hover span,
    .phone-number:focus-within span {
        color: white;
    }
    .message {
        margin: 1.5rem 0;
        padding: 0 2rem;
        color: rgba(255, 255, 255, 0.8);
        text-align: center;
        line-height: 1.1;
    }

    button {
        display: flex;
        justify-content: center;
        align-items: center;
        color: white;
        padding: 1rem 2rem;
        border-radius: 0.5rem;
        border: solid thin white;
        opacity: 0.8;
    }
    button:hover {
        cursor: pointer;
        background-color: rgba(255, 255, 255, 0.16);
    }
</style>
