<script>
    import { onMount } from "svelte";
    import { publicRequest } from "../../../modules/api";

    import * as state from "../../../modules/state";
    const text = state.uiText.text;

    let currency = "USD";

    onMount(async () => {
        const response = await publicRequest.get("/user/country");
        currency = response.data.country === "KR" ? "KRW" : "USD";
    });
</script>

<main>
    <div class="title">{$text.selectMembership}</div>
    <div class="subtitle">{$text.selectMembershipSubtitle}</div>

    <button class="currency" on:click={() => (currency = currency === "USD" ? "KRW" : "USD")}>
        <div class="currency__toggle" style={currency === "USD" ? "left:0" : "left:50%"} />
        <div class="currency__text" style="{currency === 'USD' ? 'color: white' : ''};">
            {$text.dollarPlan}
        </div>
        <div class="currency__text" style="{currency === 'KRW' ? 'color: white' : ''};">
            {$text.wonPlan}
        </div>
    </button>

    <div class="additional">{currency === "USD" ? $text.dollarPlanLimit : $text.wonPlanLimit}</div>

    <button class="basic">
        <div class="basic__title">{$text.basicPlan}</div>
        <div class="basic__price">
            {currency === "USD" ? $text.basicPlanDollerPrice : $text.basicPlanWonPrice}
        </div>
        <p>{$text.basicPlanDescription}</p>
    </button>

    <button class="professional">
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
    }
    .basic {
        margin-bottom: 2rem;
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
    button:hover {
        cursor: pointer;
    }
</style>
