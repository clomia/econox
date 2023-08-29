<script>
    import { onMount, createEventDispatcher } from "svelte";
    import * as state from "../../../../modules/state";

    const dispatch = createEventDispatcher();
    const inputResult = state.auth.signup.inputResult;

    let isSdkLoaded = false;
    const paypalClientId = "AaJ-FuCRcsENw_dBXYGEJ75w8vJI0UUmRDXUbuUCbUCCValnyQfLEB5GgCrjO2FdLJNhE9q_boMs70Fm";
    const paypalPlanId = "P-76B92140LE320861RMTQ2A2A";

    onMount(() => {
        if (window.paypal) {
            isSdkLoaded = true;
            initializePaypalButton();
            return;
        }

        const script = document.createElement("script");
        script.src = `https://www.paypal.com/sdk/js?client-id=${paypalClientId}&vault=true&intent=subscription`;
        script.onload = () => {
            isSdkLoaded = true;
            initializePaypalButton();
        };
        document.head.appendChild(script);
    });

    const initializePaypalButton = () => {
        window.paypal
            .Buttons({
                style: {
                    shape: "rect",
                    color: "black",
                    layout: "vertical",
                    label: "paypal",
                },
                createSubscription: (data, actions) => {
                    return actions.subscription.create({
                        plan_id: paypalPlanId,
                    });
                },
                onApprove: (data, actions) => {
                    inputResult.set({
                        ...$inputResult,
                        paypal: {
                            token: data.facilitatorAccessToken,
                            subscription: data.subscriptionID,
                        },
                    });
                    dispatch("complete");
                },
            })
            .render("#paypal-button");
    };
</script>

<main>
    <section>
        <div id="paypal-button" />
    </section>
</main>

<style>
    main {
        display: flex;
        flex-direction: column;
        align-items: center;
    }
    section {
        width: 100%;
        padding: 3rem;
        margin-top: 2rem;
        border-radius: 0.5rem;
        border: thin solid rgba(255, 255, 255, 0.2);
        background-color: rgba(255, 255, 255, 0.1);
    }
</style>
