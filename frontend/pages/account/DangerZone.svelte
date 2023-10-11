<script lang="ts">
    import Swal from "sweetalert2";
    import CircleLoader from "../../assets/animation/CircleLoader.svelte";
    import { paypalWidget } from "../../modules/paypal";
    import { Text, UserInfo } from "../../modules/state";
    import { api } from "../../modules/request";
    import { defaultSwalStyle } from "../../modules/functions";
    import type { AxiosError } from "axios";

    let status: string;
    if ($UserInfo["billing"]["status"] === "active") {
        status = $Text.AccountStatusActive;
    } else if ($UserInfo["billing"]["status"] === "deactive") {
        status = $Text.AccountDeactiveScheduled;
    } else if ($UserInfo["billing"]["status"] === "require") {
        status = $Text.AccountStatusDeactive;
    }

    const nextBillingDate = new Date($UserInfo["next_billing_date"]);
    const currentDate = new Date();
    const todayIsNextBillingDate =
        nextBillingDate.getDate() === currentDate.getDate() &&
        nextBillingDate.getMonth() === currentDate.getMonth() &&
        nextBillingDate.getFullYear() === currentDate.getFullYear();

    let tosspaymentsWidgetOn = false;
    let loading = false; // 로딩중일 때 스크롤 잠구기
    // 위젯이 떠있거나 로딩중일 때 스크롤 잠구기
    $: document.body.style.overflow = loading || tosspaymentsWidgetOn ? "hidden" : "";

    // tosspayments
    let cardNumber = "";
    let expiryDate = "";
    let cardType = "personal";
    let ownerId = "";
    let message: string = "";
    const cardNumberHandler = (event: Event) => {
        let value = (event.target as HTMLInputElement).value.replace(/\D/g, "");
        if (value.length > 16) {
            value = value.slice(0, 16); // 첫 16자리만 가져옵니다.
        }
        value = value.replace(/(\d{4})/g, "$1  "); // 4자리마다 두 개의 띄어쓰기 추가
        cardNumber = value.trim();
    };
    const expiryDateHandler = (event: Event) => {
        let value = (event.target as HTMLInputElement).value.replace(/\D/g, "");
        if (value.length > 4) {
            value = value.slice(0, 4); // 첫 4자리만 가져옵니다.
        }
        if (value.length > 2) {
            value = value.slice(0, 2) + " / " + value.slice(2);
        }
        expiryDate = value;
    };
    const ownerIdHandler = (event: Event) => {
        ownerId = (event.target as HTMLInputElement).value
            .replace(/\D/g, "")
            .slice(0, cardType === "personal" ? 6 : 10);
    };

    const billingDeactivate = async () => {
        if ($UserInfo["billing"]["currency"] === "USD" && todayIsNextBillingDate) {
            // 오늘이 결제 예정일인 경우 변경 불가함 (웹훅 딜레이 길어서 위험함)
            // Paypal이 결제 수행 -> 비활성화 -> PayPal로부터 웹훅을 수신 (이렇게 되면 안됌)
            return await Swal.fire({
                ...defaultSwalStyle,
                icon: "info",
                showDenyButton: false,
                title: $Text.PaymentMethod_ChangeNotAllow_DueDate,
            });
        }
        if (!$UserInfo["billing"]["registered"]) {
            return await Swal.fire({
                ...defaultSwalStyle,
                icon: "info",
                showDenyButton: false,
                title: $Text.ConnotStopPayment,
                confirmButtonText: $Text.Ok,
            });
        }
        loading = true;
        await api.private.post("/user/billing/deactivate");
        loading = false;
        await Swal.fire({
            ...defaultSwalStyle,
            icon: "info",
            showDenyButton: false,
            title: $Text.StopBillingComplete,
            confirmButtonText: $Text.Ok,
        });
        location.reload();
    };

    const billingActivateWithTosspayments = async () => {
        loading = true;
        const [expirMonth, expirYear] = expiryDate.replace(/\s/g, "").split("/");
        try {
            await api.private.post("/user/billing/activate", {
                tosspayments: {
                    card_number: cardNumber.replace(/\s/g, ""),
                    expiration_year: expirYear,
                    expiration_month: expirMonth,
                    owner_id: ownerId,
                },
            });
            location.reload();
        } catch (error: any) {
            const e = error as AxiosError;
            if (e.response?.status === 402) {
                message = $Text.PaymentInfoIncorrect;
            } else {
                message = $Text.UnexpectedError;
            }
        }
        loading = false;
    };

    const billingActivate = async () => {
        loading = true;
        try {
            await api.private.post("/user/billing/activate", {});
            location.reload();
        } catch (error: any) {
            const e = error as AxiosError;
            if (e.response?.status === 402) {
                let deny = false;
                await Swal.fire({
                    ...defaultSwalStyle,
                    icon: "info",
                    title: $Text.WillMembershipBilling,
                    denyButtonText: $Text.Cancel,
                    confirmButtonText: $Text.Ok,
                    preDeny: () => {
                        deny = true;
                    },
                });
                if (deny) {
                    loading = false;
                    return;
                }
                if ($UserInfo["billing"]["currency"] === "USD") {
                    await paypalWidget({
                        planName: $UserInfo["membership"],
                        onApprove: async (subscriptionId: string, orderId: string) => {
                            loading = true;
                            await api.private.post("/user/billing/activate", {
                                paypal: { order: orderId, subscription: subscriptionId },
                            });
                            location.reload();
                        },
                        onLoad: () => {
                            loading = false;
                        },
                    });
                } else {
                    tosspaymentsWidgetOn = true;
                }
            }
        }
        loading = false;
    };

    const deleteAccount = async () => {
        await Swal.fire({
            ...defaultSwalStyle,
            icon: "warning",
            title: $Text.DeleteAccountMessage,
            denyButtonText: $Text.Cancel,
            confirmButtonText: $Text.Ok,
            focusDeny: true,
            input: "text",
            width: "31rem",
            padding: "1rem",
            inputPlaceholder: $Text.DeleteAccountConfirmCheck,
            preConfirm: async (input: string) => {
                if (input === $Text.DeleteAccountConfirmCheck) {
                    await api.private.delete("/user");
                    location.reload();
                } else {
                    Swal.showValidationMessage($Text.InvalidInput);
                }
            },
        });
    };
</script>

<section class="section">
    <div class="status">{status}</div>
    {#if $UserInfo["billing"]["status"] === "active"}
        <button on:click={billingDeactivate}>{$Text.StopBilling}</button>
    {:else if $UserInfo["billing"]["status"] === "deactive"}
        <button on:click={billingActivate}>{$Text.BillingActivation}</button>
    {:else if $UserInfo["billing"]["status"] === "require"}
        <button on:click={billingActivate}>{$Text.AccountActivation}</button>
    {/if}
    <button class="danger" on:click={deleteAccount}>{$Text.DeleteAccount}</button>
</section>

{#if tosspaymentsWidgetOn}
    <div class="tosspayments-background">
        <form on:submit|preventDefault={billingActivateWithTosspayments}>
            <div class="title">{$Text.PaymentMethod_Enter}</div>
            <section class="card-number">
                <label>
                    <span>{$Text.CreditCardNumber}</span>
                    <input
                        type="text"
                        placeholder="••••  ••••  ••••  ••••"
                        bind:value={cardNumber}
                        on:input={cardNumberHandler}
                    />
                </label>
            </section>
            <section class="card-detail">
                <label class="card-detail__expiry">
                    <span>{$Text.ExpiryDate}</span>
                    <input
                        type="text"
                        bind:value={expiryDate}
                        on:input={expiryDateHandler}
                        placeholder="MM / YY"
                    />
                </label>
                <label class="card-detail__type">
                    <span>{$Text.CardType}</span>
                    <button
                        type="button"
                        on:click={() => (cardType = cardType === "personal" ? "business" : "personal")}
                    >
                        <div
                            class="card-detail__type__toggle"
                            style={cardType === "personal" ? "left:0" : "left:50%"}
                        />
                        <div
                            class="card-detail__type__text"
                            style="{cardType === 'personal' ? 'color: white' : ''};"
                        >
                            {$Text.Card_Personal}
                        </div>
                        <div
                            class="card-detail__type__text"
                            style="{cardType === 'business' ? 'color: white' : ''};"
                        >
                            {$Text.Card_Business}
                        </div>
                    </button>
                </label>
            </section>
            <section class="owner-id">
                <label>
                    <span>{cardType === "personal" ? $Text.BirthDate : $Text.BusinessNumber}</span>
                    <input
                        type="text"
                        bind:value={ownerId}
                        on:input={ownerIdHandler}
                        placeholder={cardType === "personal" ? "YYMMDD" : "••••••••••"}
                        autocomplete="off"
                    />
                </label>
            </section>
            <div class="message">{message}</div>
            <div class="form-buttons">
                <button
                    class="form-buttons__button"
                    type="button"
                    on:click={() => (tosspaymentsWidgetOn = false)}>{$Text.Cancel}</button
                >
                <button class="form-buttons__button" type="submit">{$Text.Submit}</button>
            </div>
        </form>
    </div>
{/if}

{#if loading}
    <div class="loader">
        <CircleLoader />
    </div>
{/if}

<style>
    .section {
        width: 100%;
        height: 6rem;
        margin-top: 3rem;
        border-radius: 0.65rem;
        border: thin solid rgba(255, 255, 255, 0.2);
        background-color: rgb(32, 40, 44);
        box-shadow: 0 0 2rem 0.1rem rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        justify-content: space-evenly;
    }

    .section button {
        width: 11rem;
        height: 2.5rem;
        border-radius: 0.4rem;
        color: var(--white);
        border: thin solid var(--border-white);
    }

    .section button:hover {
        cursor: pointer;
        background-color: rgba(255, 255, 255, 0.2);
    }

    .status {
        width: 15rem;
        text-align: center;
        color: rgba(255, 255, 255, 0.5);
    }

    .danger:hover {
        background-color: rgba(255, 140, 124, 0.2) !important;
    }

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

    /* tosspayments */
    .tosspayments-background {
        position: fixed;
        top: 0;
        left: 0;
        z-index: 1;
        height: 100vh;
        width: 100vw;
        display: flex;
        justify-content: center;
        align-items: center;
        background-color: rgba(0, 0, 0, 0.4);
    }
    form {
        display: flex;
        flex-direction: column;
        align-items: center;
        width: 30rem;
        color: var(--white);
        background: var(--widget-background);
        padding: 2rem;
        border-radius: 0.3rem;
    }
    span {
        transition: opacity 50ms ease-out;
    }
    .title {
        margin-bottom: 2rem;
        font-size: 1.2rem;
    }
    .message {
        margin: 1.5rem 0;
    }
    .card-number {
        width: 100%;
    }
    .card-number input {
        width: 100%;
        height: 2.5rem;
        border: thin solid var(--border-white);
        border-radius: 0.3rem;
        text-align: center;
        letter-spacing: 0.3rem;
        color: var(--white);
        margin-top: 0.4rem;
    }
    .card-number span {
        display: flex;
        opacity: 0.5;
        justify-content: center;
    }
    .card-number:focus-within span {
        opacity: 1;
    }
    .card-detail {
        width: 100%;
        margin-top: 2rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .card-detail__expiry {
        display: flex;
        flex-direction: column;
        align-items: center;
        width: 40%;
    }
    .card-detail__expiry span {
        opacity: 0.5;
    }
    .card-detail__expiry:focus-within span {
        opacity: 1;
    }
    .card-detail__expiry input {
        height: 2.5rem;
        color: var(--white);
        border: thin solid var(--border-white);
        border-radius: 0.3rem;
        text-align: center;
        letter-spacing: 0.2rem;
        margin-top: 0.4rem;
    }
    .card-detail__type {
        width: 55%;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: space-between;
    }
    .card-detail__type span {
        opacity: 0.5;
    }
    .card-detail__type:hover span {
        opacity: 1;
    }
    .card-detail__type > button:hover {
        cursor: pointer;
    }
    .card-detail__type > button {
        position: relative;
        height: 2.5rem;
        width: 100%;
        border: thin solid var(--border-white);
        border-radius: 0.3rem;
        display: flex;
        justify-content: space-around;
        color: rgba(255, 255, 255, 0.5);
        margin-top: 0.4rem;
    }
    .card-detail__type__toggle {
        position: absolute;
        top: 0;
        width: 50%;
        height: 2.4rem;
        border: thin solid var(--border-white);
        border-radius: 0.3rem;
        transition: left 200ms;
    }
    .card-detail__type__text {
        color: rgba(255, 255, 255, 0.5);
        height: 100%;
        display: flex;
        align-items: center;
    }
    .owner-id {
        width: 100%;
        margin-top: 2rem;
    }
    .owner-id label {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: space-between;
    }
    .owner-id input {
        border: thin solid var(--border-white);
        border-radius: 0.3rem;
        width: 100%;
        height: 2.5rem;
        text-align: center;
        color: var(--white);
        letter-spacing: 0.5rem;
        margin-top: 0.4rem;
    }
    .owner-id span {
        opacity: 0.5;
    }
    .owner-id:focus-within span {
        opacity: 1;
    }
    .form-buttons {
        width: 100%;
        display: flex;
        justify-content: space-between;
    }
    .form-buttons__button {
        color: var(--white);
        width: 10rem;
        height: 2.5rem;
        border: thin solid var(--border-white);
        border-radius: 0.3rem;
    }
    .form-buttons__button:hover {
        background-color: rgba(255, 255, 255, 0.3);
        cursor: pointer;
    }
</style>
