<script lang="ts">
    import Swal from "sweetalert2";
    import { paymentMethodString, defaultToastStyle } from "../../modules/functions";
    import { paypalWidget } from "../../modules/paypal";
    import { UserInfo, Text } from "../../modules/state";
    import type { UserDetail } from "../../modules/state";

    const userDetail = $UserInfo as UserDetail;
    let paymentWidgetOn = false;

    // 아래 변수는 트랜젝션 내역 여부 확인에도 사용함 currentBilling이 없으면 undefined이니까
    const currentBillingMethod: string | undefined = userDetail["billing"]["transactions"][0]?.["method"];
    const nextBillingDate = new Date(userDetail["next_billing_date"]);
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
        if (userDetail["billing"]["currency"] === "USD" && userDetail["billing"]["registered"]) {
            // PayPal 결제수단이 성공적으로 등록된 유저
            if (todayIsNextBillingDate) {
                // 오늘이 결제 예정일인 경우 변경 불가함 (웹훅 딜레이 길어서 위험함)
                await Swal.fire({
                    ...defaultToastStyle,
                    position: "top",
                    title: $Text.PaymentMethod_ChangeNotAllow_DueDate,
                });
            } else if (!currentBillingMethod) {
                // 결제 내역이 아직 없음
                await Swal.fire({
                    ...defaultToastStyle,
                    position: "top",
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

    let currentBillingMethodString: string;
    if (userDetail["billing"]["transactions"][0]) {
        currentBillingMethodString = paymentMethodString(userDetail["billing"]["transactions"][0]["method"]);
    } else {
        if (userDetail["billing"]["registered"]) {
            currentBillingMethodString = $Text.PaymentMethod_Waiting;
        } else {
            currentBillingMethodString = $Text.PaymentMethod_Benefit;
        }
    }
</script>

<button class="btn payment-method" on:click={() => (paymentWidgetOn = true)}>
    <div class="btn-text">{currentBillingMethodString}</div>
    <div class="btn-wrap">{$Text.Change}</div>
</button>

{#if paymentWidgetOn}
    <div>새로운 결제수단을 입력해주세요</div>
{/if}

<style>
    .btn {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 100%;
        height: 2.5rem;
        border: thin solid var(--border-white);
        border-radius: 0.5rem;
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
</style>
