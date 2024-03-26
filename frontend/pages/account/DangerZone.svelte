<script lang="ts">
  import Swal from "sweetalert2";
  import CircleLoader from "../../assets/animation/CircleLoader.svelte";
  import { paypalWidget } from "../../modules/paypal";
  import { Text, UserInfo } from "../../modules/state";
  import { api } from "../../modules/request";
  import { getBillingKey } from "../../modules/portOne";
  import {
    defaultSwalStyle,
    format,
    logout,
    swal,
  } from "../../modules/functions";
  import type { AxiosError } from "axios";
  import { load } from "js-yaml";

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

  let loading = false; // 로딩중일 때 스크롤 잠구기
  // 위젯이 떠있거나 로딩중일 때 스크롤 잠구기
  $: document.body.style.overflow = loading ? "hidden" : "";

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
      width: "27rem",
      icon: "info",
      showDenyButton: false,
      title: $Text.StopBillingComplete,
      confirmButtonText: $Text.Ok,
    });
    location.reload();
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
        let membership: string = "";
        let amount: string = "";
        if ($UserInfo.membership === "basic") {
          membership = $Text.BasicPlan;
          if ($UserInfo.billing.currency == "USD") {
            amount = $Text.BasicPlanDollerPrice;
          } else if ($UserInfo.billing.currency == "KRW") {
            amount = $Text.BasicPlanWonPrice;
          }
        } else if ($UserInfo.membership === "professional") {
          membership = $Text.ProfessionalPlan;
          if ($UserInfo.billing.currency == "USD") {
            amount = $Text.ProfessionalPlanDollerPrice;
          } else if ($UserInfo.billing.currency == "KRW") {
            amount = $Text.ProfessionalPlanWonPrice;
          }
        }
        await Swal.fire({
          ...defaultSwalStyle,
          width: "38rem",
          icon: "info",
          title: format($Text.f_WillMembershipBilling, { membership, amount }),
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
          loading = true;
          const billingKey = await getBillingKey($UserInfo.id, $UserInfo.email);
          try {
            await api.private.post("/user/billing/activate", {
              port_one: { billing_key: billingKey },
            });
          } catch {
            await swal($Text.UnexpectedError);
          }
          location.reload();
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
          try {
            await api.private.delete("/user");
            await Swal.fire({
              ...defaultSwalStyle,
              icon: "info",
              showDenyButton: false,
              title: $Text.DeleteAccountComplete,
              confirmButtonText: $Text.Ok,
            });
            await logout();
          } catch {
            await Swal.fire({
              ...defaultSwalStyle,
              icon: "error",
              showDenyButton: false,
              title: $Text.UnexpectedError,
              confirmButtonText: $Text.Ok,
            });
          }
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
    color: var(--white);
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
    z-index: 11;
    background-color: rgba(0, 0, 0, 0.4);
    display: flex;
    align-items: center;
    justify-content: center;
  }
</style>
