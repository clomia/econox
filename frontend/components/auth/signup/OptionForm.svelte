<script lang="ts">
    import { onMount, createEventDispatcher } from "svelte";
    import { publicRequest } from "../../../modules/api";

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
        const response = await publicRequest.get("/user/country");
        currency = response.data.country === "KR" ? "KRW" : "USD";
    });
</script>

<main>
    <div class="title">{$text.selectMembership}</div>
    <div class="subtitle">{$text.selectMembershipSubtitle}</div>

    <div class="currency">
        <div class="currency__toggle" style={currency === "USD" ? "left:0" : "left:50%"} />
        <button
            class="currency__text"
            on:click={() => (currency = "USD")}
            style="{currency === 'USD' ? 'color: white' : ''};"
        >
            {$text.dollarPlan}
        </button>
        <button
            class="currency__text"
            on:click={() => (currency = "KRW")}
            style="{currency === 'KRW' ? 'color: white' : ''};"
        >
            {$text.wonPlan}
        </button>
    </div>

    <div class="additional">{currency === "USD" ? $text.dollarPlanLimit : $text.wonPlanLimit}</div>

    <button class="basic" on:click={submit("basic")}>
        <div class="basic__title">{$text.basicPlan}</div>
        <div class="basic__price">
            {currency === "USD" ? $text.basicPlanDollerPrice : $text.basicPlanWonPrice}
        </div>
        <p>{$text.basicPlanDescription}</p>
    </button>

    <button class="professional" on:click={submit("professional")}>
        <div class="professional__title">{$text.professionalPlan}</div>
        <div class="professional__price">
            {currency === "USD" ? $text.professionalPlanDollerPrice : $text.professionalPlanWonPrice}
        </div>
        <p>{$text.professionalPlanDescription}</p>
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

    .currency {
        position: relative;
        display: flex;
        justify-content: space-around;
        height: 2.4rem;
        width: 100%;
        border: thin solid white;
        border-radius: 2rem;
    }
    .currency__toggle {
        position: absolute;
        top: 0rem;
        width: 50%;
        /* 미세한 틀어짐이 있어서 height가 currency보다 약간 작아야 한다.*/
        height: 2.3rem;
        border: thin solid white;
        border-radius: 2rem;
        transition: left 200ms;
    }
    .currency__text {
        display: flex;
        align-items: center;
        color: rgba(255, 255, 255, 0.4);
        height: 100%;
        padding: 0 1rem;
        transition: color ease-out 100ms;
    }
    .currency__text:hover {
        color: white;
        cursor: pointer;
    }
    .additional {
        margin: 1.2rem 0;
        font-size: 0.9rem;
        text-align: center;
        color: rgba(255, 255, 255, 0.7);
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
