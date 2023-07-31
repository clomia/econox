<script>
    import * as lang from "../modules/lang";
    const multilingual = lang.setup();
</script>

<header class="header">
    <div>ECONOX</div>
    <div>{$multilingual.console}</div>
    <div>{$multilingual.featureHub}</div>
    <div>{$multilingual.signInOut}</div>
</header>

<style>
    .header {
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        padding: 3rem 0;
    }

    .header div {
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 0 0.7rem;
        width: 10rem;
        height: 2.4rem;
        color: white;
        border: solid white thin;
        border-radius: 2rem;
    }

    .header div:hover {
        background-color: rgba(255, 255, 255, 0.16);
        cursor: pointer;
    }
</style>
