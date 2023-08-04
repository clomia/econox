<script lang="ts">
    import { createEventDispatcher } from "svelte";
    import { publicRequest } from "../../../modules/requests";
    import type { AxiosResponse } from "axios";
    import LoadingAnimation from "../../../assets/LoadingAnimation.svelte";
    export let text: { [key: string]: string };

    let request: null | Promise<AxiosResponse> = null; // 요청 전
    let message = "";

    const dispatch = createEventDispatcher();
    const result = { email: null, password: null };

    async function signup(event: SubmitEvent) {
        const form = event.target as HTMLFormElement;
        const email = form.email.value;
        const password = form.password.value;
        const retypePassword = form.retypePassword.value;
        if (password !== retypePassword) {
            message = text.passwordMismatch;
            return;
        } else if (password.length < 6) {
            message = text.passwordLengthWarning;
            return;
        }
        try {
            request = publicRequest.post("/user/cognito", { email, password });
            result["email"] = email;
            result["password"] = password;
            await request;
            dispatch("complete", result); // 상위 컴포넌트로 이벤트 전달!
        } catch (error) {
            if (error.response.status === 409) {
                message = text.alreadyExistsUser; // 이미 가입되어있는 이메일입니다
            } else if (error.response.status === 400) {
                message = text.invalidInput; // 입력 내용이 Cognito로부터 거부됌
            } else {
                message = text.error;
            }
        }
    }
</script>

<form on:submit|preventDefault={signup}>
    <section>
        <label>
            <span>{text.email}</span>
            <input type="text" name="email" required autocomplete="email" />
        </label>
    </section>
    <section>
        <label>
            <span>{text.password}</span>
            <input type="password" name="password" required autocomplete="off" />
        </label>
    </section>
    <section>
        <label>
            <span>{text.retypePassword}</span>
            <input type="password" name="retypePassword" required autocomplete="off" />
        </label>
    </section>
    {#await request}
        <LoadingAnimation />
    {/await}
    <div>{message}</div>
    {#if !(request instanceof Promise)}
        <button type="submit">{text.signup}</button>
    {/if}
</form>

<style>
    form {
        display: flex;
        flex-direction: column;
        align-items: center;
        width: 100%;
        height: 21rem;
        margin-top: 2.5rem;
        color: white;
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
