<script>
    import * as lang from "../../modules/lang";

    const text = lang.setup();
    function login(event) {
        const email = event.target.elements.email.value;
        const password = event.target.elements.password.value;

        console.log(email, password);
    }
</script>

<form on:submit|preventDefault={login}>
    <section>
        <label>
            <span>{$text.email}</span>
            <input type="email" name="email" required />
        </label>
    </section>
    <section>
        <label>
            <span>{$text.password}</span>
            <input type="password" name="password" required />
        </label>
    </section>

    <button type="submit">{$text.login}</button>
</form>

<style>
    form {
        display: flex;
        flex-direction: column;
        align-items: center;
        width: 100%;
        margin-top: 2.5rem;
    }
    section {
        width: 24.5rem;
        margin-bottom: 1.7rem;
    }
    label span {
        display: block;
        color: rgba(255, 255, 255, 0.5);
        padding-left: 0.7rem;
        padding-bottom: 0.2rem;
        transition: color 100ms ease-out;
    }
    input {
        width: 100%;
        height: 2.5rem;
        border: solid thin white;
        border-radius: 0.7rem;
        color: white;
        padding-left: 1rem;
    }
    section:focus-within label span {
        color: rgba(255, 255, 255, 1);
    }
    button {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 15rem;
        height: 2.5rem;
        border: solid thin white;
        border-radius: 1rem;
        color: white;
        margin-top: 1.4rem;
    }
    button:hover {
        cursor: pointer;
        background-color: rgba(255, 255, 255, 0.2);
    }
</style>
