<script lang="ts">
  import Swal from "sweetalert2";
  import CircleDotLoader from "../../assets/animation/CircleDotLoader.svelte";
  import { paypalWidget } from "../../modules/paypal";
  import {
    format,
    defaultSwalStyle,
    timeString,
    defaultToastStyle,
  } from "../../modules/functions";
  import { api } from "../../modules/request";
  import { Text, UserInfo } from "../../modules/state";

  const membershipMapping: any = {
    basic: $Text.BasicPlan,
    professional: $Text.ProfessionalPlan,
  };

  let membershipWidgetOn = false;
  let membershipChangeLoader = false;

  const SwalStyle = {
    ...defaultSwalStyle,
    confirmButtonText: $Text.Submit,
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
    if (
      $UserInfo["billing"]["currency"] === "USD" &&
      $UserInfo["billing"]["registered"]
    ) {
      // PayPal 결제수단이 성공적으로 등록된 유저
      if (todayIsNextBillingDate) {
        // 오늘이 결제 예정일인 경우 변경 불가함 (웹훅 딜레이 길어서 위험함)
        await Swal.fire({
          ...defaultSwalStyle,
          icon: "info",
          showDenyButton: false,
          title: $Text.PaymentMethod_ChangeNotAllow_DueDate,
        });
      } else if (!currentBillingMethod) {
        // 결제 내역이 아직 없음
        await Swal.fire({
          ...defaultSwalStyle,
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

  const requestProcess = async (
    target: "basic" | "professional",
    body: object
  ) => {
    try {
      membershipChangeLoader = true;
      const resp = await api.private.patch("/user/membership", body);
      membershipChangeLoader = false;
      membershipWidgetOn = false;
      let alertText: string;
      if ($UserInfo["billing"]["registered"]) {
        alertText = format($Text.f_MembershipChangeComplete, {
          oldMembership: membershipMapping[$UserInfo["membership"]],
          newMembership: membershipMapping[target],
          oldBillingDate: timeString($UserInfo["next_billing_date"]),
          newBillingDate: timeString(resp.data["adjusted_next_billing"]),
        });
      } else {
        alertText = format($Text.f_MembershipChangeComplete_Benefit, {
          oldMembership: membershipMapping[$UserInfo["membership"]],
          newMembership: membershipMapping[target],
        });
      }
      await Swal.fire({
        ...SwalStyle,
        width: "35rem",
        showDenyButton: false,
        text: alertText,
        icon: "success",
        confirmButtonText: $Text.Ok,
        showLoaderOnConfirm: false,
      });
      location.reload();
    } catch {
      await Swal.fire({
        ...defaultToastStyle,
        position: "top",
        title: $Text.UnexpectedError,
      });
    }
  };

  const membershipChange = (target: "basic" | "professional") => {
    return async () => {
      if (membershipChangeLoader) {
        // 이미 전송된 동일한 요청을 계속 보내지 못하도록
        return await Swal.fire({
          ...defaultToastStyle,
          position: "top",
          title: $Text.AlreadyProgressPleaseWait,
        });
      } else if (target === $UserInfo["membership"]) {
        // 이미 적용된 맴버십인 경우 알림창
        return await Swal.fire({
          ...defaultSwalStyle,
          icon: "info",
          showDenyButton: false,
          title: format($Text.f_AlreadyAppliedMembership, {
            membership: membershipMapping[$UserInfo["membership"]],
          }),
        });
      }
      const available = await billingChangeAvailableCheck();
      if (!available) {
        return;
      } else if (
        $UserInfo["billing"]["currency"] === "USD" &&
        $UserInfo["billing"]["registered"]
      ) {
        // -> PayPal!
        membershipChangeLoader = true;
        const resp = await api.private.get(
          "/paypal/membership-change-subscription-start-time",
          {
            params: { new_membership: target },
          }
        );
        const startTime: string = resp.data["adjusted_next_billing"];
        await paypalWidget({
          planName: target,
          startTime: startTime,
          onApprove: async (subscriptionId: string) => {
            await requestProcess(target, {
              new_membership: target,
              paypal_subscription_id: subscriptionId,
            });
          },
          onLoad: () => {
            membershipChangeLoader = false;
          },
        });
      } else {
        // -> Toss! or 무료체험
        await requestProcess(target, { new_membership: target });
      }
    };
  };

  // 위젯 떳을 때 스크롤 잠구기
  $: document.body.style.overflow = membershipWidgetOn ? "hidden" : "";
</script>

<button class="btn" on:click={() => (membershipWidgetOn = true)}>
  <div class="btn-text">{membershipMapping[$UserInfo["membership"]]}</div>
  <div class="btn-wrap">{$Text.Change}</div>
</button>

{#if membershipWidgetOn}
  <div class="membership-options">
    <div class="membership-options__membrane" />
    <main>
      <div class="membership-options__title">{$Text.ChangeMembership}</div>
      <button
        class="membership-options__basic"
        class:membership-options__current={$UserInfo["membership"] === "basic"}
        on:click={membershipChange("basic")}
      >
        <div class="membership-options__basic__title">{$Text.BasicPlan}</div>
        <div class="membership-options__basic__price">
          {#if $UserInfo["billing"]["currency"] === "KRW"}
            {$Text.BasicPlanWonPrice}
          {:else}
            {$Text.BasicPlanDollerPrice}
          {/if}
        </div>
        <p>{$Text.BasicPlanDescription}</p>
      </button>

      <button
        class="membership-options__professional"
        class:membership-options__current={$UserInfo["membership"] ===
          "professional"}
        on:click={membershipChange("professional")}
      >
        <div class="membership-options__professional__title">
          {$Text.ProfessionalPlan}
        </div>
        <div class="membership-options__professional__price">
          {#if $UserInfo["billing"]["currency"] === "KRW"}
            {$Text.ProfessionalPlanWonPrice}
          {:else}
            {$Text.ProfessionalPlanDollerPrice}
          {/if}
        </div>
        <p>{$Text.ProfessionalPlanDescription}</p>
      </button>
      {#if membershipChangeLoader}
        <div style="position: absolute; bottom: -0.7rem;">
          <CircleDotLoader />
        </div>
      {:else}
        <button
          class="membership-options__cancel"
          on:click={() => (membershipWidgetOn = false)}>{$Text.Cancel}</button
        >
      {/if}
    </main>
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
    z-index: 2;
  }
  .membership-options > main {
    position: relative;
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
