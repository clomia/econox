<script lang="ts">
    import CognitoForm from "./CognitoForm.svelte";
    import EmailConfirmForm from "./EmailConfirmForm.svelte";
    import OptionForm from "./OptionForm.svelte";
    import PhoneConfirmCreateForm from "./PhoneConfirmCreateForm.svelte";
    import PhoneConfirmForm from "./PhoneConfirmForm.svelte";
    import BillingForm from "./billingForm/index.svelte";
    import ResultProcess from "./ResultProcess.svelte";

    import * as state from "../../../modules/state";

    const componentStep = [
        CognitoForm,
        EmailConfirmForm,
        OptionForm,
        PhoneConfirmCreateForm,
        PhoneConfirmForm,
        BillingForm,
        ResultProcess,
    ];
    const currentStep = state.auth.signup.step;
</script>

<div class="index">
    <svelte:component
        this={componentStep[$currentStep]}
        on:complete={() => currentStep.set($currentStep + 1)}
    />
</div>
<div class="membrane" />

<style>
    .index {
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
