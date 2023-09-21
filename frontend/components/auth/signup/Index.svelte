<script lang="ts">
    import { auth } from "../../../modules/state";
    import CognitoForm from "./CognitoForm.svelte";
    import EmailConfirmForm from "./EmailConfirmForm.svelte";
    import OptionForm from "./OptionForm.svelte";
    import PhoneConfirmCreateForm from "./PhoneConfirmCreateForm.svelte";
    import PhoneConfirmForm from "./PhoneConfirmForm.svelte";
    import BillingForm from "./billingForm/index.svelte";
    import ResultProcess from "./ResultProcess.svelte";

    const componentStep = [
        CognitoForm,
        EmailConfirmForm,
        OptionForm,
        PhoneConfirmCreateForm,
        PhoneConfirmForm,
        BillingForm,
        ResultProcess,
    ];
    const Step = auth.signup.Step;
</script>

<div class="component">
    <svelte:component this={componentStep[$Step]} on:complete={() => $Step++} />
</div>

<!-- ResultProcess 상태일때 다른 컴포넌트가 클릭되지 않도록 바로 밑에 얆은 막 깔기 -->
{#if $Step === 6}
    <div class="membrane" />
{/if}

<style>
    .component {
        position: relative;
        z-index: 2;
    }
    .membrane {
        width: 100vw;
        height: 100vh;
        position: fixed;
        top: 0;
        left: 0;
        z-index: 1;
        opacity: 0;
    }
</style>
