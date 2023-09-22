<script lang="ts">
    import { Text, UserInfo } from "../modules/state";
    import type { UserDetail } from "../modules/state";

    const userDetail = $UserInfo as UserDetail;
    const currentBillingMethod = userDetail.billing.transactions?.[0].method;

    let membership: string;
    switch (userDetail.membership) {
        case "basic":
            membership = $Text.BasicPlan;
        case "professional":
            membership = $Text.ProfessionalPlan;
    }
</script>

<main>
    <section class="title">{$Text.AccountInfo}</section>
    <section class="email">{userDetail.email}</section>
    <section class="setting">
        <div class="setting__info">
            <div class="label-text">{$Text.Membership}</div>
            <button>{membership}</button>
        </div>
        <div class="setting__info">
            <div class="label-text">{$Text.Name}</div>
            <button>{userDetail.name}</button>
        </div>
        <div class="setting__btn">
            <button>{$Text.ChangePassword}</button>
        </div>
    </section>
    <section class="setting">
        <div class="setting__info card">
            <div class="label-text">{$Text.PaymentMethod}</div>
            <button>{currentBillingMethod}</button>
        </div>
        <div class="setting__btn">
            <button>{$Text.Logout}</button>
        </div>
    </section>
</main>

<style>
    * {
        color: rgba(255, 255, 255, 0.75);
    }
    main {
        width: 44rem;
        height: 30rem;
        border-radius: 1rem;
        border: thin solid rgba(255, 255, 255, 0.75);
    }
    section {
        text-align: center;
    }
    button {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 100%;
        height: 2.5rem;
        border: solid thin var(--white);
        border-radius: 0.5rem;
        color: var(--white);
    }
    button:hover {
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
</style>
