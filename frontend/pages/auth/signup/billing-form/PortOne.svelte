<script lang="ts">
  import { get } from "svelte/store";
  import { createEventDispatcher, onMount } from "svelte";
  import { auth } from "../../../../modules/state";
  import { getBillingKey } from "../../../../modules/portOne";

  const dispatch = createEventDispatcher();
  const InputResult = auth.signup.InputResult;
  const PaymentError = auth.signup.PaymentError;

  onMount(async () => {
    try {
      const billingKey = await getBillingKey(
        get(auth.signup.UserId),
        get(auth.signup.InputResult).email
      );
      $InputResult = {
        ...$InputResult,
        portOne: { billing_key: billingKey },
      };
    } catch {
      $PaymentError = true;
    }
    dispatch("complete");
  });
</script>
