<script lang="ts">
    import CognitoForm from "./CognitoForm.svelte";
    import EmailAuthForm from "./EmailAuthForm.svelte";
    import OptionForm from "./OptionForm.svelte";
    import BillingForm from "./BillingForm.svelte";
    import Result from "./ResultProcess.svelte";
    export let text: { [key: string]: string };

    let result = {};

    const componentStep = [CognitoForm, EmailAuthForm, OptionForm, BillingForm, Result];
    $: currentStep = 0;
</script>

<svelte:component
    this={componentStep[currentStep]}
    on:complete={(event) => {
        result = { ...result, ...event.detail };
        currentStep++;
    }}
    {text}
/>
