<script lang="ts">
    import { onMount, createEventDispatcher } from "svelte";
    import { api } from "../../../modules/request";

    import * as state from "../../../modules/state";

    const text = state.uiText.text;
    const inputResult = state.auth.signup.inputResult;

    let currency = "USD";

    const dispatch = createEventDispatcher();

    const submit = (membership: string) => {
        return () => {
            inputResult.set({ ...$inputResult, currency, membership });
            dispatch("complete");
        };
    };

    onMount(async () => {
        const response = await api.public.get("/country");
        currency = response.data.country === "KR" ? "KRW" : "USD";
    });
</script>

<main>
    <div class="title">{$text.SelectMembership}</div>
    <div class="subtitle">{$text.SelectMembershipSubtitle}</div>

    <button class="basic" on:click={submit("basic")}>
        <div class="basic__title">{$text.BasicPlan}</div>
        <div class="basic__price">
            {#if currency === "KRW"}
                {$text.BasicPlanWonPrice}
            {:else}
                {$text.BasicPlanDollerPrice}
            {/if}
        </div>
        <p>{$text.BasicPlanDescription}</p>
    </button>

    <button class="professional" on:click={submit("professional")}>
        <div class="professional__title">{$text.ProfessionalPlan}</div>
        <div class="professional__price">
            {#if currency === "KRW"}
                {$text.ProfessionalPlanWonPrice}
            {:else}
                {$text.ProfessionalPlanDollerPrice}
            {/if}
        </div>
        <p>{$text.ProfessionalPlanDescription}</p>
    </button>
</main>

<style>
    main {
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 0 1rem;
    }
    .title {
        color: aqua;
        font-size: 1.2rem;
        padding-top: 2.1rem;
        padding-bottom: 1.3rem;
    }
    .subtitle {
        color: rgba(255, 255, 255, 0.8);
        text-align: center;
        padding: 0 1rem;
        margin-bottom: 2rem;
    }
    .basic,
    .professional {
        color: white;
        border: thin solid white;
        border-radius: 1rem;
        padding: 1.2rem;
        width: 100%;
        transition: background-color 50ms ease-out;
    }
    .basic {
        margin-bottom: 2rem;
    }
    .basic:hover,
    .professional:hover {
        background-color: rgba(255, 255, 255, 0.1);
        cursor: pointer;
    }
    .basic__title,
    .professional__title {
        padding-bottom: 0.7rem;
        color: aqua;
    }
    .basic__price,
    .professional__price {
        padding-bottom: 0.5rem;
        color: rgba(255, 255, 255, 0.7);
    }
    p {
        color: rgba(255, 255, 255, 0.8);
    }
</style>
