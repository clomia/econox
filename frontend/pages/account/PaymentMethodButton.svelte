<script lang="ts">
    import Swal from "sweetalert2";
    import CircleLoader from "../../assets/animation/CircleLoader.svelte";
    import { paymentMethodString, defaultSwalStyle } from "../../modules/functions";
    import { api } from "../../modules/request";
    import { paypalWidget } from "../../modules/paypal";
    import { UserInfo, Text } from "../../modules/state";
    import type { AxiosError } from "axios";

    const SwalStyle = {
        ...defaultSwalStyle,
        confirmButtonText: $Text.Ok,
        denyButtonText: $Text.Cancel,
    };

    // 아래 변수는 트랜젝션 내역 여부 확인에도 사용함 currentBilling이 없으면 undefined이니까
    const currentBillingMethod: string | undefined = $UserInfo["billing"]["transactions"][0]?.["method"];
    const nextBillingDate = new Date($UserInfo["next_billing_date"]);
    const currentDate = new Date();
    const todayIsNextBillingDate =
        nextBillingDate.getDate() === currentDate.getDate() &&
        nextBillingDate.getMonth() === currentDate.getMonth() &&
        nextBillingDate.getFullYear() === currentDate.getFullYear();

    /**
     * 사용자의 결제정보 수정 가능 여부를 알려줍니다.
     * 결제 정보 수정 불가 시, 관련 알람을 띄우고 false를 반환합니다.
     * @returns 결제정보 수정 가능 여부
     */
    const billingChangeAvailableCheck = async (): Promise<boolean> => {
        if ($UserInfo["billing"]["currency"] === "USD" && $UserInfo["billing"]["registered"]) {
            // PayPal 결제수단이 성공적으로 등록된 유저
            if (todayIsNextBillingDate) {
                // 오늘이 결제 예정일인 경우 변경 불가함 (웹훅 딜레이 길어서 위험함)
                await Swal.fire({
                    ...SwalStyle,
                    icon: "info",
                    showDenyButton: false,
                    title: $Text.PaymentMethod_ChangeNotAllow_DueDate,
                });
            } else if (!currentBillingMethod) {
                // 결제 내역이 아직 없음
                await Swal.fire({
                    ...SwalStyle,
                    icon: "info",
                    showDenyButton: false,
                    title: $Text.PaymentMethod_ChangeNotAllow_Waiting,
                });
            } else {
                return true;
            }
        } else {
            return true;
        }
        return false;
    };

    let tosspaymentsWidgetOn = false;
    let loading = false;

    const widget = async () => {
        const available = await billingChangeAvailableCheck();
        if (!available) {
            return;
        } else if (!$UserInfo["billing"]["registered"]) {
            // -> Benefit~
            await Swal.fire({
                ...SwalStyle,
                icon: "info",
                showDenyButton: false,
                title: $Text.PaymentMethod_Benefit_ChangeAlert,
            });
        } else if ($UserInfo["billing"]["currency"] === "USD") {
            // -> PayPal!
            loading = true;
            await paypalWidget({
                planName: $UserInfo["membership"],
                startTime: $UserInfo["next_billing_date"],
                onApprove: async (subscriptionId: string) => {
                    loading = true;
                    await api.private.patch("/user/payment-method", {
                        paypal_subscription_id: subscriptionId,
                    });
                    loading = false;
                    await Swal.fire({
                        ...SwalStyle,
                        showDenyButton: false,
                        text: $Text.PaymentMethod_ChangeCompleted,
                        icon: "success",
                        showLoaderOnConfirm: false,
                    });
                    location.reload();
                },
                onLoad: () => {
                    loading = false;
                },
            });
        } else if ($UserInfo["billing"]["currency"] === "KRW") {
            // -> Tosspayments
            tosspaymentsWidgetOn = true;
        }
    };

    let currentBillingMethodString: string;
    if ($UserInfo["billing"]["transactions"][0]) {
        currentBillingMethodString = paymentMethodString($UserInfo["billing"]["transactions"][0]["method"]);
    } else {
        if ($UserInfo["billing"]["registered"]) {
            currentBillingMethodString = $Text.PaymentMethod_Waiting;
        } else {
            currentBillingMethodString = $Text.PaymentMethod_Benefit;
        }
    }

    // 위젯이 떠있거나 로딩중일 때 스크롤 잠구기
    $: document.body.style.overflow = loading || tosspaymentsWidgetOn ? "hidden" : "";

    // tosspayments
    let cardNumber = "";
    let expiryDate = "";
    let cardType = "personal";
    let ownerId = "";

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

    let message: string = $Text.PaymentMethod_EnterNewCard;
    const changePaymentMethod = async () => {
        const [expirMonth, expirYear] = expiryDate.replace(/\s/g, "").split("/");
        if (!(cardNumber && expirYear && expirMonth && ownerId)) {
            message = $Text.InsufficientInput;
            return;
        }
        try {
            loading = true;
            await api.private.patch("/user/payment-method", {
                tosspayments: {
                    card_number: cardNumber.replace(/\s/g, ""),
                    expiration_year: expirYear,
                    expiration_month: expirMonth,
                    owner_id: ownerId,
                },
            });
            loading = false;
            await Swal.fire({
                ...SwalStyle,
                showDenyButton: false,
                text: $Text.PaymentMethod_ChangeCompleted,
                icon: "success",
                showLoaderOnConfirm: false,
            });
            location.reload();
        } catch (error: any) {
            loading = false;
            const e = error as AxiosError;
            if (e.response?.status === 402) {
                message = $Text.InvalidInput;
            } else {
                message = $Text.UnexpectedError;
            }
        }
    };
</script>

<button class="btn payment-method" on:click={widget}>
    <div class="btn-text">{currentBillingMethodString}</div>
    <div class="btn-wrap">{$Text.Change}</div>
</button>

{#if tosspaymentsWidgetOn}
    <div class="tosspayments-background">
        <form on:submit|preventDefault={changePaymentMethod}>
            <div class="title">{$Text.PaymentMethod_Change}</div>
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
    .btn-wrap {
        position: absolute;
        display: none;
        width: 100%;
        height: 100%;
    }
    .btn:hover .btn-text {
        display: none;
    }
    .btn:hover .btn-wrap {
        display: flex;
        justify-content: center;
        align-items: center;
    }
    .payment-method {
        letter-spacing: 0.07rem;
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
