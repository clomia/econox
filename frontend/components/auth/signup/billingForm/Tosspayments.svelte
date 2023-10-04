<script lang="ts">
    import { createEventDispatcher } from "svelte";
    import { Text, auth } from "../../../../modules/state";
    import DefaultLoader from "../../../../assets/animation/DefaultLoader.svelte";

    const dispatch = createEventDispatcher();
    const InputResult = auth.signup.InputResult;
    const PaymentError = auth.signup.PaymentError;

    let cardNumber = "";
    let expiryDate = "";
    let cardType = "personal";
    let ownerId = "";

    const cardNumberHandler = (event: Event) => {
        let value = (event.target as HTMLInputElement).value.replace(/\D/g, "");
        if (value.length > 16) {
            value = value.slice(0, 16); // 첫 16자리만 가져옵니다.
        }
        value = value.replace(/(\d{4})/g, "$1  "); // 4자리마다 두 개의 띄어쓰기 추가
        cardNumber = value.trim();
    };

    const expiryDateHandler = (event: Event) => {
        let value = (event.target as HTMLInputElement).value.replace(/\D/g, "");
        if (value.length > 4) {
            value = value.slice(0, 4); // 첫 4자리만 가져옵니다.
        }
        if (value.length > 2) {
            value = value.slice(0, 2) + " / " + value.slice(2);
        }
        expiryDate = value;
    };

    const ownerIdHandler = (event: Event) => {
        ownerId = (event.target as HTMLInputElement).value
            .replace(/\D/g, "")
            .slice(0, cardType === "personal" ? 6 : 10);
    };

    let response: null | Promise<any> = null;
    const billing = async () => {
        const [expir_month, expir_year] = expiryDate.replace(/\s/g, "").split("/");
        if (cardNumber && expir_year && expir_month && ownerId) {
            $InputResult = {
                ...$InputResult,
                tosspayments: {
                    card_number: cardNumber.replace(/\s/g, ""),
                    expiration_year: expir_year,
                    expiration_month: expir_month,
                    owner_id: ownerId,
                },
            };
            dispatch("complete");
        } else {
            $PaymentError = true;
        }
    };
</script>

<form on:submit|preventDefault={billing}>
    <section class="card-number">
        <label>
            <span>{$Text.CreditCardNumber}</span>
            <input
                type="text"
                placeholder="••••  ••••  ••••  ••••"
                bind:value={cardNumber}
                on:input={cardNumberHandler}
            />
        </label>
    </section>
    <section class="card-detail">
        <label class="card-detail__expiry">
            <span>{$Text.ExpiryDate}</span>
            <input type="text" bind:value={expiryDate} on:input={expiryDateHandler} placeholder="MM / YY" />
        </label>
        <label class="card-detail__type">
            <span>{$Text.CardType}</span>
            <button
                type="button"
                on:click={() => (cardType = cardType === "personal" ? "business" : "personal")}
            >
                <div
                    class="card-detail__type__toggle"
                    style={cardType === "personal" ? "left:0" : "left:50%"}
                />
                <div class="card-detail__type__text" style="{cardType === 'personal' ? 'color: white' : ''};">
                    {$Text.Card_Personal}
                </div>
                <div class="card-detail__type__text" style="{cardType === 'business' ? 'color: white' : ''};">
                    {$Text.Card_Business}
                </div>
            </button>
        </label>
    </section>
    <section class="owner-id">
        <label>
            <span>{cardType === "personal" ? $Text.BirthDate : $Text.BusinessNumber}</span>
            <input
                type="text"
                bind:value={ownerId}
                on:input={ownerIdHandler}
                placeholder={cardType === "personal" ? "YYMMDD" : "••••••••••"}
                autocomplete="off"
            />
        </label>
    </section>
    {#await response}<DefaultLoader />{/await}
    {#if !(response instanceof Promise)}
        <button class="submit-button" type="submit">{$Text.Next}</button>
    {/if}
</form>

<style>
    form {
        display: flex;
        flex-direction: column;
        align-items: center;
        width: 100%;
        height: 23rem;
        color: var(--white);
        position: relative;
    }
    span {
        transition: opacity 50ms ease-out;
    }
    .card-number {
        width: 100%;
    }
    .card-number input {
        width: 100%;
        height: 2.5rem;
        border: thin solid var(--border-white);
        border-radius: 2rem;
        text-align: center;
        letter-spacing: 0.3rem;
        color: var(--white);
        margin-top: 0.4rem;
    }
    .card-number span {
        display: flex;
        opacity: 0.5;
        justify-content: center;
    }
    .card-number:focus-within span {
        opacity: 1;
    }
    .card-detail {
        width: 100%;
        margin-top: 2rem;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .card-detail__expiry {
        display: flex;
        flex-direction: column;
        align-items: center;
        width: 40%;
    }
    .card-detail__expiry span {
        opacity: 0.5;
    }
    .card-detail__expiry:focus-within span {
        opacity: 1;
    }
    .card-detail__expiry input {
        height: 2.5rem;
        color: var(--white);
        border: thin solid var(--border-white);
        border-radius: 1rem;
        text-align: center;
        letter-spacing: 0.2rem;
        margin-top: 0.4rem;
    }
    .card-detail__type {
        width: 55%;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: space-between;
    }
    .card-detail__type span {
        opacity: 0.5;
    }
    .card-detail__type:hover span {
        opacity: 1;
    }
    .card-detail__type > button:hover {
        cursor: pointer;
    }
    .card-detail__type > button {
        position: relative;
        height: 2.5rem;
        width: 100%;
        border: thin solid var(--border-white);
        border-radius: 1rem;
        display: flex;
        justify-content: space-around;
        color: rgba(255, 255, 255, 0.5);
        margin-top: 0.4rem;
    }
    .card-detail__type__toggle {
        position: absolute;
        top: 0;
        width: 50%;
        height: 2.4rem;
        border: thin solid var(--border-white);
        border-radius: 1rem;
        transition: left 200ms;
    }
    .card-detail__type__text {
        color: rgba(255, 255, 255, 0.5);
        height: 100%;
        display: flex;
        align-items: center;
    }
    .owner-id {
        width: 100%;
        margin-top: 2rem;
    }
    .owner-id label {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: space-between;
    }
    .owner-id input {
        border: thin solid var(--border-white);
        border-radius: 1rem;
        width: 100%;
        height: 2.5rem;
        text-align: center;
        color: var(--white);
        letter-spacing: 0.5rem;
        margin-top: 0.4rem;
    }
    .owner-id span {
        opacity: 0.5;
    }
    .owner-id:focus-within span {
        opacity: 1;
    }
    .submit-button {
        color: var(--white);
        width: 10rem;
        height: 2.5rem;
        border: thin solid var(--border-white);
        border-radius: 1rem;
        position: absolute;
        bottom: 0;
    }
    .submit-button:hover {
        background-color: rgba(255, 255, 255, 0.3);
        cursor: pointer;
    }
</style>
