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
                    data.facilitatorAccessToken; // This token need for get detail information that order and subscription (그리고 구독취소, 환불 시에도 필요)
                    data.orderID; // This is reference by sigle payments event, it will use to get sigle payments history
                    data.subscriptionID; // 구독 상태를 확인하거나 구독을 취소하고자 할 때 필요
                    console.log(data, actions);
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
