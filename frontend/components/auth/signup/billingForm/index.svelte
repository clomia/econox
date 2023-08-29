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
</script>

{#if $inputResult.currency === "KRW"}
    <Tosspayments on:complete={() => dispatch("complete")} />
{:else if $inputResult.currency === "USD"}
    <Paypal on:complete={() => dispatch("complete")} />
{/if}
