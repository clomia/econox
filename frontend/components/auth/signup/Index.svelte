<script>
    import CognitoForm from "./CognitoForm.svelte";
    import EmailAuthForm from "./EmailAuthForm.svelte";
    import OptionForm from "./OptionForm.svelte";
    import BillingForm from "./BillingForm.svelte";
    import Complete from "./Complete.svelte";

    const step = [CognitoForm, EmailAuthForm, OptionForm, BillingForm, Complete];
</script>
