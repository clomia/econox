<script lang="ts">
  import Swal from "sweetalert2";
  import CircleLoader from "../../assets/animation/CircleLoader.svelte";
  import {
    paymentMethodString,
    defaultSwalStyle,
    swal,
  } from "../../modules/functions";
  import { api } from "../../modules/request";
  import { getBillingKey } from "../../modules/portOne";
  import { paypalWidget } from "../../modules/paypal";
  import { UserInfo, Text } from "../../modules/state";

  const SwalStyle = {
    ...defaultSwalStyle,
    confirmButtonText: $Text.Ok,
    denyButtonText: $Text.Cancel,
  };

  // 아래 변수는 트랜젝션 내역 여부 확인에도 사용함 currentBilling이 없으면 undefined이니까
  const currentBillingMethod: string | undefined =
    $UserInfo["billing"]["transactions"][0]?.["method"];
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
    if ($UserInfo["billing"]["status"] !== "active") {
      if ($UserInfo["billing"]["registered"]) {
        await Swal.fire({
          ...SwalStyle,
          width: "30rem",
          icon: "info",
          showDenyButton: false,
          title: $Text.PaymentMethod_ChangeNotAllow_StatusError,
        });
      } else {
        await Swal.fire({
          ...SwalStyle,
          width: "35rem",
          icon: "info",
          showDenyButton: false,
          title: $Text.PaymentMethod_BenefitEnd_ChangeAlert,
        });
      }
      return false;
    }
    if (
      $UserInfo["billing"]["currency"] === "USD" &&
      $UserInfo["billing"]["registered"]
    ) {
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
          width: "30rem",
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
      await swal($Text.BillingMethodUpdate);
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
      // -> PortOne
      await swal($Text.BillingMethodUpdate);
      loading = true;
      const billingKey = await getBillingKey($UserInfo.id, $UserInfo.email);
      await api.private.patch("/user/payment-method", {
        port_one_billing_key: billingKey,
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
    }
  };

  let currentBillingMethodString: string;
  if ($UserInfo["billing"]["transactions"][0]) {
    currentBillingMethodString = paymentMethodString(
      $UserInfo["billing"]["method"]
    );
  } else {
    if ($UserInfo["billing"]["registered"]) {
      currentBillingMethodString = $Text.PaymentMethod_Waiting;
    } else {
      if ($UserInfo["billing"]["status"] == "active") {
        currentBillingMethodString = $Text.PaymentMethod_Benefit;
      } else {
        currentBillingMethodString = $Text.PaymentMethod_BenefitEnd;
      }
    }
  }

  // 위젯이 떠있거나 로딩중일 때 스크롤 잠구기
  $: document.body.style.overflow = loading ? "hidden" : "";
</script>

<button class="btn payment-method" on:click={widget}>
  <div class="btn-text">{currentBillingMethodString}</div>
  <div class="btn-wrap">{$Text.Change}</div>
</button>

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
    z-index: 12;
    background-color: rgba(0, 0, 0, 0.4);
    display: flex;
    align-items: center;
    justify-content: center;
  }
</style>
