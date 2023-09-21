<script lang="ts">
    import { onMount, createEventDispatcher } from "svelte";
    import { Text, auth } from "../../../../modules/state";
    import Paypal from "./Paypal.svelte";
    import Tosspayments from "./Tosspayments.svelte";

    const InputResult = auth.signup.InputResult;
    const PaymentError = auth.signup.PaymentError;

    const dispatch = createEventDispatcher();
    onMount(() => {
        if (!$InputResult.reregistration) {
            dispatch("complete"); // 최초 회원가입인 경우 결제정보 입력할 필요 없음
        }
    });
</script>

<div>{$PaymentError ? $Text.PaymentInfoIncorrect : $Text.NoBenefitPleasePayment}</div>

{#if $InputResult.reregistration && $InputResult.currency === "KRW"}
    <Tosspayments on:complete={() => dispatch("complete")} />
{:else if $InputResult.reregistration && $InputResult.currency === "USD"}
    <Paypal on:complete={() => dispatch("complete")} />
{/if}

<style>
    div {
        width: 100%;
        display: flex;
        justify-content: center;
        color: rgba(255, 255, 255, 0.7);
        padding: 2rem 0;
        text-align: center;
    }
</style>
