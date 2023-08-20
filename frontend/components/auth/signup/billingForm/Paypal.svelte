<script>
    import { onMount } from "svelte";

    let isSdkLoaded = false;
    const paypalClientId = "AaJ-FuCRcsENw_dBXYGEJ75w8vJI0UUmRDXUbuUCbUCCValnyQfLEB5GgCrjO2FdLJNhE9q_boMs70Fm";

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

    function initializePaypalButton() {
        window.paypal
            .Buttons({
                style: {
                    shape: "pill",
                    color: "black",
                    layout: "vertical",
                    label: "paypal",
                },
                createSubscription: function (data, actions) {
                    return actions.subscription.create({
                        plan_id: "P-76B92140LE320861RMTQ2A2A",
                    });
                },
                onApprove: function (data, actions) {
                    alert(data.subscriptionID);
                },
            })
            .render("#paypal-button");
    }
</script>

<section>
    <div id="paypal-button" />
</section>

<style>
    #paypal-button {
        margin-top: 10rem;
    }
</style>
