<script lang="ts">
    import { format, logout, timeString, paymentMethodString } from "../../modules/functions";
    import { Text, UserInfo } from "../../modules/state";
    import ToggleArrow from "../../assets/icon/ToggleArrow.svelte";
    import NameButton from "./NameButton.svelte";
    import PasswordButton from "./PasswordButton.svelte";
    import MembershipButton from "./MembershipButton.svelte";
    import PaymentMethodButton from "./PaymentMethodButton.svelte";
    import DangerZone from "./DangerZone.svelte";
    import type { UserDetail } from "../../modules/state";

    const userDetail = $UserInfo as UserDetail;

    /**
     *  언어에 맞게 금액을 표현하는 문자열을 변환
     */
    const amountString = (amount: number): string => {
        const str = userDetail["billing"]["currency"] === "KRW" ? $Text.f_KRW : $Text.f_USD;
        return format(str, { v: amount });
    };

    /**
     * 맴버십 이름을 간결하게 표현
     * Econox Basic Membership 앞에 Econox를 제거
     */
    const membershipNameString = (str: string): string => {
        return str.split(" ").slice(1).join(" ");
    };

    const transactions = userDetail.billing.transactions;
    const nextBillingDate = new Date(userDetail["next_billing_date"]);

    let paymentListToggle = false;
</script>

<main>
    <section class="title">{$Text.AccountInfo}</section>
    <section class="email">{userDetail["email"]}</section>
    <section class="setting">
        <div class="setting__info">
            <div class="label-text">{$Text.Membership}</div>
            <MembershipButton />
        </div>
        <div class="setting__info">
            <div class="label-text">{$Text.Name}</div>
            <NameButton />
        </div>
        <div class="setting__btn">
            <PasswordButton />
        </div>
    </section>
    <section class="setting">
        <div class="setting__info card">
            <div class="label-text">{$Text.PaymentMethod}</div>
            <PaymentMethodButton />
        </div>
        <div class="setting__btn">
            <button class="btn" on:click={logout}>{$Text.Logout}</button>
        </div>
    </section>
    <section class="billing">
        <div class="billing__next">
            {format($Text.f_NextBillingDate, {
                y: nextBillingDate.getFullYear(),
                m: nextBillingDate.getMonth() + 1,
                d: nextBillingDate.getDate(),
            })}
        </div>
        {#if paymentListToggle}
            <ol class="billing__list">
                <li style="justify-content: center;">{$Text.PaymentHistory}</li>
                {#each transactions as transaction}
                    <li>
                        <div>{timeString(transaction.time)}</div>
                        <div>{amountString(transaction.amount)}</div>
                        <div>{paymentMethodString(transaction.method)}</div>
                        <div>{membershipNameString(transaction.name)}</div>
                    </li>
                {/each}
            </ol>
            <div class="billing__limit">{$Text.PaymentHistoryLimit}</div>
        {/if}
        {#if transactions.length}
            <button
                class="billing__toggle"
                style={paymentListToggle ? "transform: rotate(180deg)" : ""}
                on:click={() => (paymentListToggle = !paymentListToggle)}><ToggleArrow /></button
            >
        {:else}
            <div style="height: 3rem;" />
        {/if}
    </section>
</main>

<DangerZone />

<style>
    * {
        color: rgba(255, 255, 255, 0.75);
    }
    main {
        width: 44rem;
        border-radius: 0.65rem;
        border: thin solid rgba(255, 255, 255, 0.2);
        background-color: rgb(32, 40, 44);
        box-shadow: 0 0 2rem 0.1rem rgba(0, 0, 0, 0.5);
        position: relative;
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
        border: thin solid var(--border-white);
        border-radius: 0.4rem;
        color: var(--white);
        position: relative;
    }
    .btn:hover {
        cursor: pointer;
        background-color: rgba(255, 255, 255, 0.2);
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
        opacity: 0.6;
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
        opacity: 0.3;
        transition: transform 100ms;
        padding-bottom: 1rem;
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
    .billing__limit {
        opacity: 0.5;
        margin-top: 1rem;
    }
</style>
