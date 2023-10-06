<script lang="ts">
    import Swal from "sweetalert2";
    import CircleLoader from "../../assets/animation/CircleLoader.svelte";
    import { paypalWidget } from "../../modules/paypal";
    import { Text, UserInfo } from "../../modules/state";
    import { api } from "../../modules/request";
    import { defaultSwalStyle } from "../../modules/functions";
    import type { AxiosError } from "axios";

    const today = new Date();
    const nexy_billing = new Date($UserInfo.next_billing_date);
    let status: string;
    if ($UserInfo["billing"]["status"] === "active") {
        status = $Text.AccountStatusActive;
    } else if (today < nexy_billing) {
        status = $Text.AccountDeactiveScheduled;
    } else {
        status = $Text.AccountStatusDeactive;
    }

    let loading = false; // 로딩중일 때 스크롤 잠구기
    $: document.body.style.overflow = loading ? "hidden" : "";

    const billingDeactivate = async () => {
        if (!$UserInfo["billing"]["registered"]) {
            return await Swal.fire({
                ...defaultSwalStyle,
                icon: "info",
                showDenyButton: false,
                title: $Text.ConnotStopPayment,
            });
        }
        loading = true;
        await api.private.post("/user/billing/deactivate");
        loading = false;
        await Swal.fire({
            ...defaultSwalStyle,
            icon: "info",
            showDenyButton: false,
            title: $Text.StopBillingComplete,
        });
        location.reload();
    };

    const billingActivate = async () => {
        loading = true;
        try {
            await api.private.post("/user/billing/activate");
        } catch (error: any) {
            const e = error as AxiosError;
            if (e.response?.status === 406) {
                // PayPal subscription id 필요!
                await paypalWidget({
                    planName: $UserInfo["membership"],
                    onApprove: async (subscriptionId: string) => {
                        await api.private.post("/user/billing/activate", {
                            paypal_subscription_id: subscriptionId,
                        });
                    },
                    onLoad: () => {
                        loading = false;
                    },
                });
            }
        }
        loading = false;
        location.reload();
    };
</script>

<section>
    <div class="status">{status}</div>
    {#if $UserInfo["billing"]["status"] === "active"}
        <button on:click={billingDeactivate}>{$Text.StopBilling}</button>
    {:else if $UserInfo["billing"]["status"] === "deactive"}
        <button on:click={billingActivate}>{$Text.BillingActivation}</button>
    {:else if $UserInfo["billing"]["status"] === "require"}
        <button>{$Text.AccountActivation}</button>
    {/if}
    <button class="danger">{$Text.DeleteAccount}</button>
</section>

{#if loading}
    <div class="loader">
        <CircleLoader />
    </div>
{/if}

<style>
    section {
        width: 100%;
        height: 6rem;
        margin-top: 3rem;
        border-radius: 0.65rem;
        border: thin solid rgba(255, 255, 255, 0.2);
        background-color: rgb(32, 40, 44);
        box-shadow: 0 0 2rem 0.1rem rgba(0, 0, 0, 0.5);
        display: flex;
        align-items: center;
        justify-content: space-evenly;
    }

    section button {
        width: 11rem;
        height: 2.5rem;
        border-radius: 0.4rem;
        color: var(--white);
        border: thin solid var(--border-white);
    }

    section button:hover {
        cursor: pointer;
        background-color: rgba(255, 255, 255, 0.2);
    }

    .status {
        width: 15rem;
        text-align: center;
        color: rgba(255, 255, 255, 0.5);
    }

    .danger:hover {
        background-color: rgba(255, 140, 124, 0.2);
    }

    .loader {
        width: 100vw;
        height: 100vh;
        position: fixed;
        top: 0;
        left: 0;
        z-index: 1;
        background-color: rgba(0, 0, 0, 0.4);
        display: flex;
        align-items: center;
        justify-content: center;
    }
</style>
