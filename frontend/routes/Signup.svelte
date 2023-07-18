<script>
    let email = "";
    let password = "";
    let code = "";
    const host = window.location.origin;

    const register = async () => {
        const response = await fetch(`${host}/api/account`, {
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
            document.getElementById("codeInput").style.display = "block";
            document.getElementById("verifyButton").style.display = "block";
        } else {
            alert("회원가입 실패");
        }
    };

    const verify = async () => {
        const response = await fetch(`${host}/api/account/email-verifi`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({
                email,
                code,
            }),
        });

        if (response.ok) {
            alert("인증 성공!");
        } else {
            alert("인증 실패");
        }
    };
</script>

<h1>회원가입</h1>
<div>
    <label for="email">이메일:</label>
    <input type="text" id="email" bind:value={email} />
</div>
<div>
    <label for="password">비밀번호:</label>
    <input type="password" id="password" bind:value={password} />
</div>
<button on:click={register}>회원가입</button>
<div id="codeInput" style="display: none;">
    <label for="code">인증 코드:</label>
    <input type="text" id="code" bind:value={code} />
</div>
<button id="verifyButton" on:click={verify} style="display: none;">인증</button>
