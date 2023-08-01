<script>
    function login(event) {
        // 여기에서 로그인 로직을 처리합니다.
        console.log("로그인 처리 시작!");
        console.log(event);
    }
</script>

<form on:submit|preventDefault={login}>
    <label for="email">이메일:</label>
    <input type="email" id="email" name="email" required />

    <label for="password">비밀번호:</label>
    <input type="password" id="password" name="password" required />

    <label for="password">비밀번호 확인:</label>
    <input type="password" id="password" name="password" required />

    <button type="submit">로그인</button>
</form>
