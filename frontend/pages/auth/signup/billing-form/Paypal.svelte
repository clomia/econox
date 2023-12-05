<script lang="ts">
  import { onMount, createEventDispatcher } from "svelte";
  import { api } from "../../../../modules/request";
  import { auth } from "../../../../modules/state";
  import CircleDotLoader from "../../../../assets/animation/CircleDotLoader.svelte";

  const dispatch = createEventDispatcher();
  const InputResult = auth.signup.InputResult;

  let isSdkLoaded = false;

  const initializePaypalButton = (planId: string) => {
    (window as any).paypal
      .Buttons({
        style: {
          shape: "rect",
          color: "black",
          layout: "vertical",
          label: "paypal",
        },
        createSubscription: (data: any, actions: any) => {
          return actions.subscription.create({
            plan_id: planId,
          });
        },
        onApprove: (data: any, actions: any) => {
          $InputResult = {
            ...$InputResult,
            paypal: {
              order: data.orderID as string,
              subscription: data.subscriptionID as string,
            },
          };
          dispatch("complete");
        },
      })
      .render("#paypal-button");
  };

  onMount(async () => {
    const paypalPlans = await api.public.get("/paypal/plans");
    const planId = paypalPlans.data["plan_id"][$InputResult.membership];
    const clientId = paypalPlans.data["client_id"];

    if ((window as any).paypal) {
      isSdkLoaded = true;
      initializePaypalButton(planId);
      return;
    }
    const script = document.createElement("script");
    script.src = `https://www.paypal.com/sdk/js?client-id=${clientId}&vault=true&intent=subscription`;
    script.onload = () => {
      isSdkLoaded = true;
      initializePaypalButton(planId);
    };
    document.head.appendChild(script);
  });
</script>

<main>
  <section>
    {#if !isSdkLoaded}
      <CircleDotLoader />
    {/if}
    <div id="paypal-button" style={!isSdkLoaded ? "display: none;" : ""} />
  </section>
</main>

<style>
  main {
    display: flex;
    flex-direction: column;
    align-items: center;
  }
  section {
    width: 100%;
    height: 10rem;
    border-radius: 0.5rem;
    border: thin solid rgba(255, 255, 255, 0.2);
    background-color: rgba(255, 255, 255, 0.1);
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
  }
  #paypal-button {
    margin-top: 1.5rem;
  }
</style>
