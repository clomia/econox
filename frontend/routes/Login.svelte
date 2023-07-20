<script>
    let email = "";
    let password = "";
    const host = window.location.origin;

    const login = async () => {
        const response = await fetch(`${host}/api/login`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                email,
                password,
            }),
        });

        if (response.ok) {
            alert("로그인 성공!");
            const data = await response.json();
            localStorage.setItem("idToken", data.idToken);
            localStorage.setItem("refreshToken", data.refreshToken);
        } else {
            alert("로그인 실패");
        }
    };
</script>

<h1>로그인</h1>
<div>
    <label for="email">이메일:</label>
    <input type="text" id="email" bind:value={email} />
</div>
<div>
    <label for="password">비밀번호:</label>
    <input type="password" id="password" bind:value={password} />
</div>
<button on:click={login}>로그인</button>
