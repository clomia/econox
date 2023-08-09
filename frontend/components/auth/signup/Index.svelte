<script>
    import CognitoForm from "./CognitoForm.svelte";
    import EmailConfirmForm from "./EmailConfirmForm.svelte";
    import OptionForm from "./OptionForm.svelte";
    import BillingForm from "./BillingForm.svelte";
    import ResultProcess from "./ResultProcess.svelte";

    import * as state from "../../../modules/state";

    const componentStep = [CognitoForm, EmailConfirmForm, OptionForm, BillingForm, ResultProcess];
    const currentStep = state.auth.signup.step;
</script>

<svelte:component this={componentStep[$currentStep]} on:complete={() => currentStep.set($currentStep + 1)} />
