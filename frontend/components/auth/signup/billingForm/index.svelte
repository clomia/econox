<script>
    import Paypal from "./Paypal.svelte";
    import Tosspayments from "./Tosspayments.svelte";

    import * as state from "../../../../modules/state";

    const inputResult = state.auth.signup.inputResult;

    inputResult.set({ ...$inputResult, currency: "USD" });
</script>

{#if $inputResult.currency === "KRW"}
    <Tosspayments />
{:else if $inputResult.currency === "USD"}
    <Paypal />
{/if}
