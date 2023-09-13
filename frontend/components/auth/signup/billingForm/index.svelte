<script lang="ts">
    import { onMount, createEventDispatcher } from "svelte";
    import Paypal from "./Paypal.svelte";
    import Tosspayments from "./Tosspayments.svelte";

    import * as state from "../../../../modules/state";

    const dispatch = createEventDispatcher();
    const inputResult = state.auth.signup.inputResult;
    const paymentError = state.auth.signup.paymentError;
    const text = state.uiText.text;

    onMount(() => {
        if (!$inputResult.reregistration) {
            dispatch("complete"); // 최초 회원가입인 경우 결제정보 입력할 필요 없음
        }
    });
</script>

<div>{$paymentError ? $text.paymentError : $text.noFirstPleasePayment}</div>

{#if $inputResult.reregistration && $inputResult.currency === "KRW"}
    <Tosspayments on:complete={() => dispatch("complete")} />
{:else if $inputResult.reregistration && $inputResult.currency === "USD"}
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
