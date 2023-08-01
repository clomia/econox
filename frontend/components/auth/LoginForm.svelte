<script>
    function login(event) {
        // 여기에서 로그인 로직을 처리합니다.
        console.log("로그인 처리 시작!");
        console.log(event);
    }
</script>

<form on:submit|preventDefault={login}>
    <section>
        <label for="email">이메일</label>
        <input type="email" id="email" name="email" required />
    </section>
    <section>
        <label for="password">비밀번호</label>
        <input type="password" id="password" name="password" required />
    </section>

    <button type="submit">로그인</button>
</form>

<style>
    form {
        display: flex;
        flex-direction: column;
        align-items: center;
        width: 100%;
        margin-top: 2rem;
    }
    section {
        width: 25rem;
        margin-bottom: 1rem;
    }
    label {
        display: block;
        color: rgba(255, 255, 255, 0.7);
    }
    input {
        width: 100%;
        height: 2rem;
        border: solid thin white;
        border-radius: 0.5rem;
    }
</style>
