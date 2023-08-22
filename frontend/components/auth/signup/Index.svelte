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

<ResultProcess />
<!-- <svelte:component this={componentStep[$currentStep]} on:complete={() => currentStep.set($currentStep + 1)} /> -->
