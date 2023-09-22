<script lang="ts">
    console.log("hello");
</script>

<div class="ground">
    <div class="ground__window">
        <section>hello</section>
    </div>
</div>

<style>
    .ground {
        display: flex;
        justify-content: center;
        align-items: start;
        position: absolute;
        top: 10rem;
        left: 0;
        right: 0;
        bottom: 0;
    }
    .ground__window {
        width: 34rem;
        padding: 3rem 4rem;
        border-radius: 1rem;
        border: thin solid rgba(255, 255, 255, 0.2);
        background: linear-gradient(to bottom, #2e2f32, rgb(32, 49, 55));
    }
</style>
