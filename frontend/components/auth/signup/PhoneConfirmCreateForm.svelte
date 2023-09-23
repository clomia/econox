<script lang="ts">
    import { createEventDispatcher } from "svelte";
    import { getCodes, getName } from "country-list";
    import { getCountryCallingCode } from "libphonenumber-js";
    import { api } from "../../../modules/request";
    import { Text, auth } from "../../../modules/state";
    import DefaultLoader from "../../../assets/animation/DefaultLoader.svelte";
    import type { CountryCode } from "libphonenumber-js";

    const InputResult = auth.signup.InputResult;
    const InputPhoneNumber = auth.signup.InputPhoneNumber;

    const dispatch = createEventDispatcher();

    let response: null | Promise<any> = null;
    let message = "";
    let phoneNumber = "";
    $: phoneNumber = phoneNumber.replace(/\D/g, "");

    const phoneConfirm = async (event: SubmitEvent) => {
        message = "";
        const form = event.target as HTMLFormElement;
        const callingCode = getCountryCallingCode(form.countryCode.value as CountryCode);
        const phone = `+${callingCode}${phoneNumber}`;
        if (!phoneNumber) {
            message = $Text.PleaseEnterPhoneNumber;
            return;
        }
        try {
            response = api.public.post("/auth/phone", { phone });
            await response;
            $InputResult = { ...$InputResult, phone };
            $InputPhoneNumber = phoneNumber;
            dispatch("complete");
        } catch (error) {
            response = null;
            message = $Text.PhoneConfirmCodeSendFailed;
        }
    };
</script>

<div class="description">{$Text.PhoneConfirmReason}</div>

<form on:submit|preventDefault={phoneConfirm}>
    {#await api.public.get("/country") then response}
        <label>
            <span>{$Text.Country}</span>
            <select name="countryCode" value={response.data.country}>
                {#each getCodes() as country}
                    <option value={country}>{getName(country)}</option>
                {/each}
            </select>
        </label>
    {/await}
    <label class="phone-number">
        <span>{$Text.EnterPhoneNumber}</span>
        <input bind:value={phoneNumber} name="phone" type="text" />
    </label>
    <div class="message">{message}</div>
    {#if !(response instanceof Promise)}
        <button>{$Text.SendVerificationCode}</button>
    {/if}
    {#await response}<DefaultLoader />{/await}
</form>

<style>
    .description {
        color: var(--white);
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
        color: var(--white);
    }
    label {
        margin-bottom: 3rem;
    }
    label span {
        display: block;
        width: 100%;
        color: var(--white);
        margin-bottom: 0.5rem;
        text-align: center;
    }
    select {
        width: 25rem;
        border-radius: 1rem;
        border: solid thin var(--white);
        color: var(--white);
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
        border: solid thin var(--white);
        color: var(--white);
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
        color: var(--white);
    }
    .message {
        margin: 1.5rem 0;
        padding: 0 2rem;
        color: var(--white);
        text-align: center;
        line-height: 1.1;
    }

    button {
        display: flex;
        justify-content: center;
        align-items: center;
        color: var(--white);
        padding: 1rem 2rem;
        border-radius: 0.5rem;
        border: solid thin var(--white);
        opacity: 0.8;
    }
    button:hover {
        cursor: pointer;
        background-color: rgba(255, 255, 255, 0.16);
    }
</style>
