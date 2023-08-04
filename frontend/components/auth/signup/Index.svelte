<script>
    import CognitoForm from "./CognitoForm.svelte";
    import EmailAuthForm from "./EmailAuthForm.svelte";
    import OptionForm from "./OptionForm.svelte";
    import BillingForm from "./BillingForm.svelte";
    import ResultProcess from "./ResultProcess.svelte";
    export let text;

    // DB 유저 생성시 필요한 정보들
    let inputResult = {
        email: "sample@gmail.com",
    };

    const componentStep = [CognitoForm, EmailAuthForm, OptionForm, BillingForm, ResultProcess];
    $: currentStep = 0;
</script>

<EmailAuthForm bind:inputResult {text} />

<!-- <svelte:component
    this={componentStep[currentStep]}
    bind:inputResult
    {text}
    on:complete={() => currentStep++}
/> -->
