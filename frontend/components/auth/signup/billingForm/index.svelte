<script>
    import { onMount, createEventDispatcher } from "svelte";
    import Paypal from "./Paypal.svelte";
    import Tosspayments from "./Tosspayments.svelte";

    import * as state from "../../../../modules/state";

    const dispatch = createEventDispatcher();
    const inputResult = state.auth.signup.inputResult;

    onMount(() => {
        if (!$inputResult.reregistration) {
            dispatch("complete"); // 최초 회원가입인 경우 결제정보 입력할 필요 없음
        }
    });
    $inputResult.currency = "KRW";
</script>

<div>첫 회원가입 혜택 대상자가 아닙니다 결제 정보를 입력해주세요</div>

{#if $inputResult.currency === "KRW"}
    <Tosspayments on:complete={() => dispatch("complete")} />
{:else if $inputResult.currency === "USD"}
    <Paypal on:complete={() => dispatch("complete")} />
{/if}

<style>
    div {
        width: 100%;
        display: flex;
        justify-content: center;
        color: white;
        padding: 2rem 0;
        text-align: center;
    }
</style>
