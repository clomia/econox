<script lang="ts">
    import axios from "axios";

    const host = window.location.origin;

    async function sendData(): Promise<void> {
        const idToken: string | null = localStorage.getItem("idToken");
        const refreshToken: string | null =
            localStorage.getItem("refreshToken");

        if (!idToken || !refreshToken) {
            console.error("Tokens not found in local storage");
            return;
        }

        try {
            const response = await axios.post(
                `${host}/api/token-test`,
                {},
                {
                    headers: {
                        idToken: idToken,
                    },
                }
            );

            console.log(response.data);
        } catch (error) {
            console.error("Error sending data:", error);
        }
    }
    const tokenDelete = () => {
        localStorage.removeItem("idToken");
        localStorage.removeItem("refreshToken");
    };

    let userInput: string;
    const getInfo = async () => {
        const idToken: string | null = localStorage.getItem("idToken");
        try {
            const response = await axios.post(
                `${host}/api/user-info`,
                { text: userInput },
                { headers: { idToken: idToken } }
            );
            console.log(response.data);
        } catch (error) {
            if (error.response.status) {
                console.log("로그아웃 실행!");
                tokenDelete();
            }
        }
    };
</script>

<button on:click={sendData}>Send Tokens</button>
<button on:click={tokenDelete}>Sign out</button>

<input bind:value={userInput} type="text" />
<button on:click={getInfo}>Get Info</button>
