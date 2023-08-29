<script>
    import { createEventDispatcher } from "svelte";
    import LoadingAnimation from "../../../../assets/LoadingAnimation.svelte";
    import * as state from "../../../../modules/state";
    import { request } from "../../../../modules/api";

    const dispatch = createEventDispatcher();
    const inputResult = state.auth.signup.inputResult;

    let cardNumber = "";
    let expiryDate = "";
    let cardType = "personal";
    let ownerId = "";

    const cardNumberHandler = (event) => {
        let value = event.target.value.replace(/\D/g, "");
        if (value.length > 16) {
            value = value.slice(0, 16); // 첫 16자리만 가져옵니다.
        }
        value = value.replace(/(\d{4})/g, "$1  "); // 4자리마다 두 개의 띄어쓰기 추가
        cardNumber = value.trim();
    };

    const expiryDateHandler = (event) => {
        let value = event.target.value.replace(/\D/g, "");
        if (value.length > 4) {
            value = value.slice(0, 4); // 첫 4자리만 가져옵니다.
        }
        if (value.length > 2) {
            value = value.slice(0, 2) + " / " + value.slice(2);
        }
        expiryDate = value;
    };

    const ownerIdHandler = (event) => {
        ownerId = event.target.value.slice(0, cardType === "personal" ? 6 : 10);
    };

    let response = null;
    let message = "";
    const billing = async () => {
        message = "";
        const [expir_month, expir_year] = expiryDate.replace(/\s/g, "").split("/");
        try {
            response = request.public.post("/billing/tosspayments", {
                user_id: $inputResult.cognitoId,
                card_number: cardNumber.replace(/\s/g, ""),
                expiration_year: expir_year,
                expiration_month: expir_month,
                owner_id: ownerId,
            });
            const key = (await response).data.key;
            inputResult.set({ ...$inputResult, tosspayments: { key } });
            dispatch("complete");
        } catch (error) {
            response = null;
            const statusMessages = {
                400: "잘못된 값이 있습니다.",
                422: "누락된 값이 있습니다.",
            };
            message = statusMessages[error.response?.status] || "에러!";
        }
    };
</script>

<form on:submit|preventDefault={billing}>
    <section class="card-number">
        <label>
            <span>Credit card number</span>
            <input
                type="text"
                placeholder="••••  ••••  ••••  ••••"
                bind:value={cardNumber}
                on:input={cardNumberHandler}
                x-autocompletetype="cc-number"
            />
        </label>
    </section>
    <section class="card-detail">
        <label class="card-detail__expiry">
            <span>Expiry date</span>
            <input type="text" bind:value={expiryDate} on:input={expiryDateHandler} placeholder="MM / YY" />
        </label>
        <label class="card-detail__type">
            <span>Card type</span>
            <div>
                <div
                    class="card-detail__type__toggle"
                    style={cardType === "personal" ? "left:0" : "left:50%"}
                />
                <button
                    type="button"
                    class="card-detail__type__text"
                    on:click={() => (cardType = "personal")}
                    style="{cardType === 'personal' ? 'color: white' : ''};"
                >
                    Personal
                </button>
                <button
                    type="button"
                    class="card-detail__type__text"
                    on:click={() => (cardType = "business")}
                    style="{cardType === 'business' ? 'color: white' : ''};"
                >
                    Business
                </button>
            </div>
        </label>
    </section>
    <section class="owner-id">
        <label>
            <span>{cardType === "personal" ? "Birth date" : "Business Number"}</span>
            <input
                type="text"
                bind:value={ownerId}
                on:input={ownerIdHandler}
                placeholder={cardType === "personal" ? "YYMMDD" : "••••••••••"}
                autocomplete="off"
            />
        </label>
    </section>
    {#await response}
        <LoadingAnimation />
    {/await}
    <div class="message">{message}</div>
    {#if !(response instanceof Promise)}
        <button class="submit-button" type="submit">Next</button>
    {/if}
</form>

<style>
    form {
        display: flex;
        flex-direction: column;
        align-items: center;
        width: 100%;
        height: 23rem;
        margin-top: 2.5rem;
        color: white;
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
        border: thin solid white;
        border-radius: 2rem;
        text-align: center;
        letter-spacing: 0.3rem;
        color: rgba(255, 255, 255, 0.8);
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
        color: rgba(255, 255, 255, 0.8);
        border: thin solid white;
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
    .card-detail__type > div button:hover {
        cursor: pointer;
    }
    .card-detail__type > div {
        position: relative;
        height: 2.5rem;
        width: 100%;
        border: thin solid white;
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
        border: thin solid white;
        border-radius: 1rem;
        transition: left 200ms;
    }
    .card-detail__type__text {
        color: rgba(255, 255, 255, 0.5);
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
        border: thin solid white;
        border-radius: 1rem;
        width: 100%;
        height: 2.5rem;
        text-align: center;
        color: rgba(255, 255, 255, 0.8);
        letter-spacing: 0.5rem;
        margin-top: 0.4rem;
    }
    .owner-id span {
        opacity: 0.5;
    }
    .owner-id:focus-within span {
        opacity: 1;
    }
    .message {
        display: flex;
        align-items: center;
        margin: 1.25rem 0;
        height: 2rem;
        color: rgba(255, 255, 255, 0.8);
    }
    .submit-button {
        color: rgba(255, 255, 255, 0.8);
        width: 10rem;
        height: 2.5rem;
        border: thin solid white;
        border-radius: 1rem;
    }
    .submit-button:hover {
        background-color: rgba(255, 255, 255, 0.3);
        cursor: pointer;
    }
</style>
