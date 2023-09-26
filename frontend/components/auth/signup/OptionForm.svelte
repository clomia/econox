<script lang="ts">
    import { onMount, createEventDispatcher } from "svelte";
    import { api } from "../../../modules/request";
    import { Text, auth } from "../../../modules/state";

    const InputResult = auth.signup.InputResult;

    let currency = "USD";

    const dispatch = createEventDispatcher();

    const submit = (membership: string) => {
        return () => {
            $InputResult = { ...$InputResult, currency, membership };
            dispatch("complete");
        };
    };

    onMount(async () => {
        const response = await api.public.get("/country");
        currency = response.data.country === "KR" ? "KRW" : "USD";
    });
</script>

<main>
    <div class="title">{$Text.SelectMembership}</div>
    <div class="subtitle">{$Text.SelectMembershipSubtitle}</div>

    <button class="basic" on:click={submit("basic")}>
        <div class="basic__title">{$Text.BasicPlan}</div>
        <div class="basic__price">
            {#if currency === "KRW"}
                {$Text.BasicPlanWonPrice}
            {:else}
                {$Text.BasicPlanDollerPrice}
            {/if}
        </div>
        <p>{$Text.BasicPlanDescription}</p>
    </button>

    <button class="professional" on:click={submit("professional")}>
        <div class="professional__title">{$Text.ProfessionalPlan}</div>
        <div class="professional__price">
            {#if currency === "KRW"}
                {$Text.ProfessionalPlanWonPrice}
            {:else}
                {$Text.ProfessionalPlanDollerPrice}
            {/if}
        </div>
        <p>{$Text.ProfessionalPlanDescription}</p>
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
        color: var(--white);
        font-size: 1.2rem;
        padding-top: 2.1rem;
        padding-bottom: 1.3rem;
    }
    .subtitle {
        color: var(--white);
        text-align: center;
        padding: 0 1rem;
        margin-bottom: 2rem;
    }
    .basic,
    .professional {
        color: var(--white);
        border: thin solid var(--white);
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
        color: var(--white);
    }
    .basic__price,
    .professional__price {
        padding-bottom: 0.5rem;
        color: var(--white);
    }
    p {
        color: var(--white);
    }
</style>
