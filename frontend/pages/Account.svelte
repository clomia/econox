<script lang="ts">
    import { format, logout, defaultSwalStyle } from "../modules/functions";
    import { Text, UserInfo } from "../modules/state";
    import ToggleArrow from "../assets/icon/ToggleArrow.svelte";
    import Swal from "sweetalert2";
    import { api } from "../modules/request";
    import type { UserDetail } from "../modules/state";
    import type { AxiosError } from "axios";

    const userDetail = $UserInfo as UserDetail;
    const currentBillingMethod = userDetail["billing"]["transactions"]?.[0]["method"];

    let membership: string;
    switch (userDetail["membership"]) {
        case "basic":
            membership = $Text.BasicPlan;
        case "professional":
            membership = $Text.ProfessionalPlan;
    }
    const f_NextBillingDate = new Date(userDetail["next_billing_date"]);
    const nextBilling = {
        y: f_NextBillingDate.getFullYear(),
        m: f_NextBillingDate.getMonth() + 1,
        d: f_NextBillingDate.getDate(),
    };
    let toggle: boolean = false;
    const transactions = userDetail.billing.transactions;

    const timeString = (str: string) => {
        const date = new Date(str);
        const year = date.getFullYear();
        const month = (date.getMonth() + 1).toString().padStart(2, "0");
        const day = date.getDate().toString().padStart(2, "0");
        return `${year}.${month}.${day}`;
    };
    const amountString = (amount: number) => {
        const str = userDetail["billing"]["currency"] === "KRW" ? $Text.f_KRW : $Text.f_USD;
        return format(str, { v: amount });
    };
    const paymentMethodString = (str: string) => {
        if (/^[0-9*]+$/.test(str)) {
            return str.match(/.{1,4}/g)?.join(" ");
        }
        return str;
    };
    const membershipNameString = (str: string) => {
        return str.split(" ").slice(1).join(" ");
    };
    const SwalStyle = {
        ...defaultSwalStyle,
        confirmButtonText: $Text.Submit,
        denyButtonText: $Text.Cancel,
    };
    const changeName = () => {
        Swal.fire({
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
                    await api.private.patch("/user/name", { new_name: newName });
                    location.reload();
                } catch {
                    Swal.showValidationMessage($Text.UnexpectedError);
                }
            },
        });
    };

    const changePassword = async () => {
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
                    await api.public.post("/auth/send-password-reset-code", { email: userDetail["email"] });
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
                        email: userDetail["email"],
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

<main>
    <section class="title">{$Text.AccountInfo}</section>
    <section class="email">{userDetail["email"]}</section>
    <section class="setting">
        <div class="setting__info">
            <div class="label-text">{$Text.Membership}</div>
            <button class="btn">
                <div class="btn-text">{membership}</div>
                <div class="btn-wrap">{$Text.Change}</div>
            </button>
        </div>
        <div class="setting__info">
            <div class="label-text">{$Text.Name}</div>
            <button class="btn" on:click={changeName}>
                <div class="btn-text">{userDetail["name"]}</div>
                <div class="btn-wrap">{$Text.Change}</div>
            </button>
        </div>
        <div class="setting__btn">
            <button class="btn" on:click={changePassword}>{$Text.ChangePassword}</button>
        </div>
    </section>
    <section class="setting">
        <div class="setting__info card">
            <div class="label-text">{$Text.PaymentMethod}</div>
            <button class="btn payment-method">
                <div class="btn-text">{paymentMethodString(currentBillingMethod)}</div>
                <div class="btn-wrap">{$Text.Change}</div>
            </button>
        </div>
        <div class="setting__btn">
            <button class="btn" on:click={logout}>{$Text.Logout}</button>
        </div>
    </section>
    <section class="billing">
        <div class="billing__next">{format($Text.f_NextBillingDate, nextBilling)}</div>
        {#if toggle}
            <ol class="billing__list">
                <li style="justify-content: center;">{$Text.PaymentHistory}</li>
                {#each transactions as transaction}
                    <li>
                        <div>{timeString(transaction.time)}</div>
                        <div>{amountString(transaction.amount)}</div>
                        <div class="payment-method">{paymentMethodString(transaction.method)}</div>
                        <div>{membershipNameString(transaction.name)}</div>
                    </li>
                {/each}
            </ol>
        {/if}
        {#if transactions}
            <button
                class="billing__toggle"
                style={toggle ? "transform: rotate(180deg)" : ""}
                on:click={() => {
                    toggle = toggle ? false : true;
                }}><ToggleArrow /></button
            >
        {/if}
    </section>
</main>

<style>
    * {
        color: rgba(255, 255, 255, 0.75);
    }
    main {
        width: 44rem;
        border-radius: 1rem;
        border: thin solid rgba(255, 255, 255, 0.75);
    }
    section {
        text-align: center;
    }
    .btn {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 100%;
        height: 2.5rem;
        border: solid thin var(--white);
        border-radius: 0.5rem;
        color: var(--white);
        position: relative;
    }
    .btn-wrap {
        position: absolute;
        display: none;
        width: 100%;
        height: 100%;
    }
    .btn:hover {
        cursor: pointer;
        background-color: rgba(255, 255, 255, 0.2);
    }
    .btn:hover .btn-text {
        display: none;
    }
    .btn:hover .btn-wrap {
        display: flex;
        justify-content: center;
        align-items: center;
    }

    .setting__info:hover .label-text {
        opacity: 1;
    }
    .setting__info,
    .setting__btn {
        width: 10rem;
    }
    .card {
        width: 22rem;
    }
    .title {
        font-size: 1.3rem;
        margin-top: 2rem;
    }
    .email {
        margin-top: 2rem;
    }
    .setting {
        display: flex;
        justify-content: space-between;
        margin: 2rem 5rem;
    }
    .label-text {
        height: 2.3rem;
        display: flex;
        align-items: end;
        justify-content: center;
        padding-bottom: 0.5rem;
        color: white;
        opacity: 0.6;
        transition: opacity 100ms ease-out;
    }
    .setting__btn {
        margin-top: 2.3rem;
    }
    .billing__next {
        margin-top: 4rem;
    }
    .billing__toggle {
        padding-top: 2rem;
        padding-bottom: 1rem;
        opacity: 0.3;
        transition: transform 100ms;
    }
    .billing__toggle:hover {
        opacity: 1;
        cursor: pointer;
    }
    .billing__list {
        margin-top: 2rem;
    }
    .billing__list li {
        margin: 0 5rem;
        padding: 0.7rem 1rem;
        border-bottom: thin solid rgba(255, 255, 255, 0.3);
        display: flex;
        justify-content: space-between;
    }
    .payment-method {
        letter-spacing: 0.07rem;
    }
</style>
