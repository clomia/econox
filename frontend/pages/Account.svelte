<script lang="ts">
    import { format, logout, defaultSwalStyle } from "../modules/functions";
    import { Text, UserInfo } from "../modules/state";
    import ToggleArrow from "../assets/icon/ToggleArrow.svelte";
    import DefaultLoader from "../assets/animation/DefaultLoader.svelte";
    import Swal from "sweetalert2";
    import { api } from "../modules/request";
    import type { UserDetail } from "../modules/state";
    import type { AxiosError } from "axios";

    const userDetail = $UserInfo as UserDetail;
    // 아래 변수는 트랜젝션 내역 여부 확인에도 사용함 currentBilling이 없으면 undefined이니까
    const currentBillingMethod: string | undefined = userDetail["billing"]["transactions"][0]?.["method"];

    const membershipMapping = {
        basic: $Text.BasicPlan,
        professional: $Text.ProfessionalPlan,
    };
    const membership = membershipMapping[userDetail["membership"]];
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
    const billingMethodString = (str: string) => {
        if (str) {
            if (/^[0-9*]+$/.test(str)) {
                return str.match(/.{1,4}/g)?.join(" ");
            }
            return str;
        } else {
            if (userDetail["billing"]["registered"]) {
                return $Text.PaymentMethod_Waiting;
            } else {
                return $Text.PaymentMethod_Benefit;
            }
        }
    };
    const membershipNameString = (str: string) => {
        return str.split(" ").slice(1).join(" ");
    };
    const SwalStyle = {
        ...defaultSwalStyle,
        confirmButtonText: $Text.Submit,
        denyButtonText: $Text.Cancel,
    };
    const ToastStyle = {
        width: "30rem",
        toast: true,
        showConfirmButton: false,
        timer: 2000,
        timerProgressBar: true,
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

    let membershipWidgetOn = false;

    const nextBillingDate = new Date(userDetail["next_billing_date"]);
    const currentDate = new Date();

    const todayIsNextBillingDate = // 사용자의 시간대를 기반으로 년, 월, 일 정보를 추출
        nextBillingDate.getDate() === currentDate.getDate() &&
        nextBillingDate.getMonth() === currentDate.getMonth() &&
        nextBillingDate.getFullYear() === currentDate.getFullYear();

    /**
     * 사용자의 결제정보 수정 가능 여부를 알려줍니다.
     * 결제 정보 수정 불가 시, 관련 알람을 띄우고 false를 반환합니다.
     * @returns 결제정보 수정 가능 여부
     */
    const billingInfoChangeAvailableCheck = async (): Promise<boolean> => {
        if (userDetail["billing"]["currency"] === "USD" && userDetail["billing"]["registered"]) {
            // PayPal 결제수단이 성공적으로 등록된 유저
            if (todayIsNextBillingDate) {
                // 오늘이 결제 예정일인 경우 변경 불가함 (웹훅 딜레이 길어서 위험함)
                await Swal.fire({
                    ...ToastStyle,
                    position: "top",
                    title: $Text.PaymentMethod_ChangeNotAllow_DueDate,
                });
            } else if (!currentBillingMethod) {
                // 결제 내역이 아직 없음
                await Swal.fire({
                    ...ToastStyle,
                    position: "top",
                    title: $Text.PaymentMethod_ChangeNotAllow_Waiting,
                });
            }
        } else {
            return true;
        }
        return false;
    };

    let membershipChangeLoader: boolean = false;
    const membershipChange = (to: "basic" | "professional") => {
        return async () => {
            if (membershipChangeLoader) {
                // 이미 전송된 동일한 요청을 계속 보내지 못하도록
                return await Swal.fire({
                    ...ToastStyle,
                    position: "top",
                    title: $Text.AlreadyProgressPleaseWait,
                });
            } else if (to === userDetail["membership"]) {
                // 이미 적용된 맴버십인 경우 알림창
                return await Swal.fire({
                    ...ToastStyle,
                    position: "top",
                    title: format($Text.f_AlreadyAppliedMembership, { membership }),
                });
            }
            const available = await billingInfoChangeAvailableCheck();
            if (available && userDetail["billing"]["currency"] === "USD") {
                // PayPal!
            } else if (available && userDetail["billing"]["currency"] === "KRW") {
                // Toss!
                try {
                    membershipChangeLoader = true;
                    const resp = await api.private.patch("/user/membership", { new_membership: to });
                    membershipChangeLoader = false;
                    membershipWidgetOn = false;
                    await Swal.fire({
                        ...SwalStyle,
                        width: "35rem",
                        showDenyButton: false,
                        text: format($Text.f_MembershipChangeComplete, {
                            oldMembership: membershipMapping[userDetail["membership"]],
                            newMembership: membershipMapping[to],
                            oldBillingDate: timeString(userDetail["next_billing_date"]),
                            newBillingDate: timeString(resp.data["adjusted_next_billing"]),
                        }),
                        icon: "success",
                        confirmButtonText: $Text.Ok,
                        showLoaderOnConfirm: false,
                    });
                    location.reload();
                } catch {
                    await Swal.fire({
                        ...ToastStyle,
                        position: "top",
                        title: $Text.UnexpectedError,
                    });
                }
            }
        };
    };

    const paymentMethodChange = () => {
        if (!userDetail["billing"]["registered"]) {
            // 무료 체험중
            console.log("이거 왜 안대");
            Swal.fire({
                ...ToastStyle,
                position: "top",
                title: "아직 결제수단 없어서 수정할게 없다고",
            });
        }
    };
</script>

<main>
    <section class="title">{$Text.AccountInfo}</section>
    <section class="email">{userDetail["email"]}</section>
    <section class="setting">
        <div class="setting__info">
            <div class="label-text">{$Text.Membership}</div>
            <button class="btn" on:click={() => (membershipWidgetOn = true)}>
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
                <div class="btn-text">{billingMethodString(currentBillingMethod)}</div>
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
        {#if transactions.length}
            <button
                class="billing__toggle"
                style={toggle ? "transform: rotate(180deg)" : ""}
                on:click={() => {
                    toggle = toggle ? false : true;
                }}><ToggleArrow /></button
            >
        {:else}
            <div style="height: 3rem;" />
        {/if}
    </section>
</main>

{#if membershipWidgetOn}
    <div class="membership-options">
        <div class="membership-options__membrane" />
        <main>
            <div class="membership-options__title">{$Text.SelectMembership}</div>
            <button
                class="membership-options__basic"
                class:membership-options__current={userDetail["membership"] === "basic"}
                on:click={membershipChange("basic")}
            >
                <div class="membership-options__basic__title">{$Text.BasicPlan}</div>
                <div class="membership-options__basic__price">
                    {#if userDetail["billing"]["currency"] === "KRW"}
                        {$Text.BasicPlanWonPrice}
                    {:else}
                        {$Text.BasicPlanDollerPrice}
                    {/if}
                </div>
                <p>{$Text.BasicPlanDescription}</p>
            </button>

            <button
                class="membership-options__professional"
                class:membership-options__current={userDetail["membership"] === "professional"}
                on:click={membershipChange("professional")}
            >
                <div class="membership-options__professional__title">{$Text.ProfessionalPlan}</div>
                <div class="membership-options__professional__price">
                    {#if userDetail["billing"]["currency"] === "KRW"}
                        {$Text.ProfessionalPlanWonPrice}
                    {:else}
                        {$Text.ProfessionalPlanDollerPrice}
                    {/if}
                </div>
                <p>{$Text.ProfessionalPlanDescription}</p>
            </button>
            {#if membershipChangeLoader}
                <div style="position: absolute; bottom: -1.1rem;"><DefaultLoader /></div>
            {:else}
                <button class="membership-options__cancel" on:click={() => (membershipWidgetOn = false)}
                    >{$Text.Cancel}</button
                >
            {/if}
        </main>
    </div>
{/if}

<style>
    * {
        color: rgba(255, 255, 255, 0.75);
    }
    main {
        width: 44rem;
        border-radius: 1rem;
        border: thin solid rgba(255, 255, 255, 0.75);
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
    .payment-method {
        letter-spacing: 0.07rem;
    }

    /* Membership option change styles */
    .membership-options {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    .membership-options__membrane {
        width: 100vw;
        height: 100vh;
        position: fixed;
        top: 0;
        left: 0;
        z-index: 1;
        background-color: rgba(0, 0, 0, 0.4);
    }
    .membership-options main {
        z-index: 2;
        width: 30rem;
        height: 31rem;
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 0 2rem;
        padding-bottom: 2rem;
        background: var(--widget-background);
        border-radius: 0.3rem;
        border: none;
    }
    .membership-options__title {
        color: var(--white);
        font-size: 1.2rem;
        padding-bottom: 1rem;
        padding-top: 1.5rem;
    }
    .membership-options__basic,
    .membership-options__professional {
        color: var(--white);
        border-radius: 0.3rem;
        padding: 1.2rem;
        width: 100%;
        background-color: rgba(255, 255, 255, 0.05);
        transition: background-color 50ms ease-out;
    }
    .membership-options__basic {
        margin-bottom: 2rem;
    }
    .membership-options__cancel:hover,
    .membership-options__basic:hover,
    .membership-options__professional:hover {
        background-color: rgba(255, 255, 255, 0.15);
        cursor: pointer;
    }
    .membership-options__basic__title,
    .membership-options__professional__title {
        padding-bottom: 0.7rem;
        color: var(--white);
    }
    .membership-options__basic__price,
    .membership-options__professional__price {
        padding-bottom: 0.5rem;
        color: var(--white);
    }
    .membership-options p {
        color: var(--white);
    }
    .membership-options__current {
        background-color: rgba(0, 0, 0, 0.08);
    }
    .membership-options__current:hover {
        background-color: rgba(0, 0, 0, 0.08);
    }
    .membership-options__cancel {
        color: var(--white);
        border-radius: 0.3rem;
        padding: 0.6rem 1rem;
        margin-top: 2rem;
        background-color: rgba(255, 255, 255, 0.05);
    }
</style>
