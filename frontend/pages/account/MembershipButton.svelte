<script lang="ts">
    import DefaultLoader from "../../assets/animation/DefaultLoader.svelte";
    import { Text, UserInfo } from "../../modules/state";
    import type { UserDetail } from "../../modules/state";

    const userDetail = $UserInfo as UserDetail;
    const membershipMapping = {
        basic: $Text.BasicPlan,
        professional: $Text.ProfessionalPlan,
    };
    const membership = membershipMapping[userDetail["membership"]];

    let membershipWidgetOn = false;
    let membershipChangeLoader = false;

    const membershipChange = (to: "basic" | "professional") => {
        return () => {
            console.log("맴버십 체인지!");
        };
    };
</script>

<button class="btn" on:click={() => (membershipWidgetOn = true)}>
    <div class="btn-text">{membership}</div>
    <div class="btn-wrap">{$Text.Change}</div>
</button>

{#if membershipWidgetOn}
    <div class="membership-options">
        <div class="membership-options__membrane" />
        <main>
            <div class="membership-options__title">{$Text.SelectMembership}</div>
            <button
                class="membership-options__basic"
                class:membership-options__current={userDetail["membership"] === "basic"}
                on:click={membershipChange("basic")}
            >
                <div class="membership-options__basic__title">{$Text.BasicPlan}</div>
                <div class="membership-options__basic__price">
                    {#if userDetail["billing"]["currency"] === "KRW"}
                        {$Text.BasicPlanWonPrice}
                    {:else}
                        {$Text.BasicPlanDollerPrice}
                    {/if}
                </div>
                <p>{$Text.BasicPlanDescription}</p>
            </button>

            <button
                class="membership-options__professional"
                class:membership-options__current={userDetail["membership"] === "professional"}
                on:click={membershipChange("professional")}
            >
                <div class="membership-options__professional__title">{$Text.ProfessionalPlan}</div>
                <div class="membership-options__professional__price">
                    {#if userDetail["billing"]["currency"] === "KRW"}
                        {$Text.ProfessionalPlanWonPrice}
                    {:else}
                        {$Text.ProfessionalPlanDollerPrice}
                    {/if}
                </div>
                <p>{$Text.ProfessionalPlanDescription}</p>
            </button>
            {#if membershipChangeLoader}
                <div style="position: absolute; bottom: -1.1rem;"><DefaultLoader /></div>
            {:else}
                <button class="membership-options__cancel" on:click={() => (membershipWidgetOn = false)}
                    >{$Text.Cancel}</button
                >
            {/if}
        </main>
    </div>
{/if}

<style>
    .btn {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 100%;
        height: 2.5rem;
        border: solid thin var(--white);
        border-radius: 0.5rem;
        color: var(--white);
        position: relative;
    }
    .btn-wrap {
        position: absolute;
        display: none;
        width: 100%;
        height: 100%;
    }
    .btn:hover {
        cursor: pointer;
        background-color: rgba(255, 255, 255, 0.2);
    }
    .btn:hover .btn-text {
        display: none;
    }
    .btn:hover .btn-wrap {
        display: flex;
        justify-content: center;
        align-items: center;
    }

    /* Membership option change styles */
    .membership-options {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        display: flex;
        justify-content: center;
        align-items: center;
        z-index: 2;
    }
    .membership-options__membrane {
        width: 100vw;
        height: 100vh;
        position: fixed;
        top: 0;
        left: 0;
        z-index: 1;
        background-color: rgba(0, 0, 0, 0.4);
    }
    .membership-options main {
        z-index: 2;
        width: 30rem;
        height: 31rem;
        display: flex;
        flex-direction: column;
        align-items: center;
        padding: 0 2rem;
        padding-bottom: 2rem;
        background: var(--widget-background);
        border-radius: 0.3rem;
        border: none;
    }
    .membership-options__title {
        color: var(--white);
        font-size: 1.2rem;
        padding-bottom: 1rem;
        padding-top: 1.5rem;
    }
    .membership-options__basic,
    .membership-options__professional {
        color: var(--white);
        border-radius: 0.3rem;
        padding: 1.2rem;
        width: 100%;
        background-color: rgba(255, 255, 255, 0.05);
        transition: background-color 50ms ease-out;
    }
    .membership-options__basic {
        margin-bottom: 2rem;
    }
    .membership-options__cancel:hover,
    .membership-options__basic:hover,
    .membership-options__professional:hover {
        background-color: rgba(255, 255, 255, 0.15);
        cursor: pointer;
    }
    .membership-options__basic__title,
    .membership-options__professional__title {
        padding-bottom: 0.7rem;
        color: var(--white);
    }
    .membership-options__basic__price,
    .membership-options__professional__price {
        padding-bottom: 0.5rem;
        color: var(--white);
    }
    .membership-options p {
        color: var(--white);
    }
    .membership-options__current {
        background-color: rgba(0, 0, 0, 0.08);
    }
    .membership-options__current:hover {
        background-color: rgba(0, 0, 0, 0.08);
    }
    .membership-options__cancel {
        color: var(--white);
        border-radius: 0.3rem;
        padding: 0.6rem 1rem;
        margin-top: 2rem;
        background-color: rgba(255, 255, 255, 0.05);
    }
</style>
