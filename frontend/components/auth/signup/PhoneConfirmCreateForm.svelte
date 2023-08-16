<script lang="ts">
    import { createEventDispatcher } from "svelte";
    import { getCodes, getName } from "country-list";
    import { getCountryCallingCode } from "libphonenumber-js";

    import * as state from "../../../modules/state";
    import { publicRequest } from "../../../modules/api";
    import LoadingAnimation from "../../../assets/LoadingAnimation.svelte";

    const text = state.uiText.text;
    const inputResult = state.auth.signup.inputResult;
    const inputPhoneNumberStore = state.auth.signup.inputPhoneNumber;

    const countries = {};
    getCodes().forEach((code) => {
        try {
            const name = getName(code);
            const callingCode = getCountryCallingCode(code);
            countries[name] = callingCode;
        } catch (error) {
            console.info(`No calling code for country: ${code}`);
        }
    });

    const getCurrentCountry = async () => {
        const response = await publicRequest.get("/user/country");
        return getCountryCallingCode(response.data.country);
    };

    const dispatch = createEventDispatcher();

    let request = null;
    let message = "";
    const phoneConfirm = async (event: SubmitEvent) => {
        message = "";
        const form = event.target as HTMLFormElement;
        const callingCode = form.callingCode.value;
        const inputPhoneNumber = form.phoneNumber.value;
        const phoneNumber = `+${callingCode}${inputPhoneNumber.replace(/-|\s/g, "")}`; // "-" & 공백 제거}
        if (!inputPhoneNumber) {
            message = $text.noPhoneNumber;
            return;
        }
        if (/\D/.test(inputPhoneNumber)) {
            message = $text.phoneNumberNotNumber;
            return;
        }
        try {
            request = publicRequest.post("/auth/phone", { phone_number: phoneNumber });
            await request;
            inputResult.set({ ...$inputResult, phoneNumber });
            inputPhoneNumberStore.set(inputPhoneNumber);
            dispatch("complete");
        } catch (error) {
            request = null;
            message = $text.phoneConfirmRequestFailed;
        }
    };
</script>

<div class="description">{$text.phoneConfirmDescription}</div>

<form on:submit|preventDefault={phoneConfirm}>
    {#await getCurrentCountry() then callingCode}
        <label>
            <span>{$text.country}</span>
            <select name="callingCode" value={callingCode}>
                {#each Object.entries(countries) as [name, callingCode]}
                    <option value={callingCode}>{name}</option>
                {/each}
            </select>
        </label>
    {/await}
    <label class="phone-number">
        <span>{$text.inputPhoneNumber}</span>
        <input name="phoneNumber" type="text" />
    </label>
    <div class="message">{message}</div>
    {#if !(request instanceof Promise)}
        <button>{$text.sendVerificationCode}</button>
    {/if}
    {#await request}
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
        letter-spacing: 0.2rem;
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
