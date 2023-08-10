<script>
    import { getCodes, getName } from "country-list";
    import { getCountryCallingCode } from "libphonenumber-js";

    const countries = {};
    getCodes().forEach((code) => {
        try {
            const name = getName(code);
            const callingCode = getCountryCallingCode(code);
            countries[name] = callingCode;
        } catch (error) {
            console.info(`No calling code for country: ${code}`);
        }
    });

    let callingCode = "";

    const phoneConfirm = async (event) => {
        return "hello";
    };
</script>

<form on:submit|preventDefault={phoneConfirm}>
    <label>
        <span>국가 선택</span>
        <select on:change={(event) => (callingCode = event.target.value)}>
            {#each Object.entries(countries) as [name, callingCode]}
                <option value={callingCode}>{name}</option>
            {/each}
        </select>
    </label>
    <label>
        <span>전화번호 입력</span>
        <input type="text" />
    </label>
    <button>인증코드 발송</button>
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
    label {
        margin-bottom: 3rem;
    }
    label span {
        display: block;
        width: 100%;
        color: rgba(255, 255, 255, 0.7);
        margin-bottom: 0.5rem;
        text-align: center;
    }
    select {
        width: 25rem;
        border-radius: 1rem;
        border: solid thin white;
        color: white;
        margin: 0 0.5rem;
        padding: 0 1rem;
        height: 3rem;
    }
    select:hover {
        cursor: pointer;
        background-color: rgba(255, 255, 255, 0.16);
    }
    option {
        text-align: center;
    }
    label input {
        width: 25rem;
        border-radius: 1rem;
        border: solid thin white;
        color: white;
        padding: 0 1rem;
        height: 3rem;
        text-align: center;
        letter-spacing: 0.2rem;
    }
</style>
