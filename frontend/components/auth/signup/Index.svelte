<script lang="ts">
    import CognitoForm from "./CognitoForm.svelte";
    import EmailAuthForm from "./EmailAuthForm.svelte";
    import OptionForm from "./OptionForm.svelte";
    import BillingForm from "./BillingForm.svelte";
    import Complete from "./Complete.svelte";
    export let text: { [key: string]: string };

    let formInput = {
        CognitoForm: { complete: false },
        EmailAuthForm: { complete: false },
        OptionForm: { complete: false },
        BillingForm: { complete: false },
    };
</script>

<CognitoForm {text} {formInput} formName={"CognitoForm"} />
