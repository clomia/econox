<script>
    import CognitoForm from "./CognitoForm.svelte";
    import EmailAuthForm from "./EmailAuthForm.svelte";
    import OptionForm from "./OptionForm.svelte";
    import BillingForm from "./BillingForm.svelte";
    import ResultProcess from "./ResultProcess.svelte";

    import * as state from "../../../modules/state";

    const componentStep = [CognitoForm, EmailAuthForm, OptionForm, BillingForm, ResultProcess];
    const currentStep = state.auth.signup.step;
</script>

<OptionForm />

<!-- <svelte:component this={componentStep[$currentStep]} on:complete={() => currentStep.set($currentStep + 1)} /> -->
