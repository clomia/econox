<script>
    import { Text } from "../../modules/state";

    let status = $Text.AccountStatusNormal;
</script>

<section>
    <div class="status">{status}</div>
    <button>{$Text.MembershipDeactivation}</button>
    <button class="danger">{$Text.DeleteAccount}</button>
</section>

<style>
    section {
        width: 100%;
        height: 5rem;
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
        color: var(--white);
        font-size: 1.1rem;
        font-weight: 100;
    }

    .danger:hover {
        background-color: rgba(255, 140, 124, 0.2);
    }
</style>
