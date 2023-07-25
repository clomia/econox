<script>
    import axios from "axios";

    const host = window.location.origin;
    let amount,
        productName,
        customerEmail,
        customerName,
        billingKey,
        customerKey;

    const paymentRequest = async () => {
        const idToken = localStorage.getItem("idToken");
        try {
            const response = await axios.post(
                `${host}/api/payment`,
                { amount, productName, customerEmail, customerName },
                {
                    headers: {
                        idToken: idToken,
                    },
                }
            );
            console.log(response.data);
        } catch (error) {
            console.error("Error sending data:", error);
        }
    };

    const billing = async () => {
        const idToken = localStorage.getItem("idToken");
        try {
            const response = await axios.post(
                `${host}/api/real-billing`,
                { billingKey, customerKey },
                {
                    headers: {
                        idToken: idToken,
                    },
                }
            );
            console.log(response.data);
        } catch (error) {
            console.error("Error sending data:", error);
        }
    };
</script>

<label for="amount">amount</label>
<input bind:value={amount} type="text" id="amount" />

<label for="productName">productName</label>
<input bind:value={productName} type="text" id="productName" />

<label for="customerEmail">customerEmail</label>
<input bind:value={customerEmail} type="text" id="customerEmail" />

<label for="customerName">customerName</label>
<input bind:value={customerName} type="text" id="customerName" />

<button on:click={paymentRequest}>결제 요청 제출</button>

<label for="billingKey">billingKey</label>
<input bind:value={billingKey} type="text" id="billingKey" />

<label for="customerKey">customerKey</label>
<input bind:value={customerKey} type="text" id="customerKey" />
<button on:click={billing}>진짜 결제</button>
