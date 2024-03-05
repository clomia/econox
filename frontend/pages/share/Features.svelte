<script lang="ts">
  import type { PublicFgRespType } from "./function";

  export let data: PublicFgRespType;
</script>

<main>
  {#each data.features as fe}
    <div class="fe">
      <div class="fe__color" style="background-color: {fe.color};" />
      <div class="fe__info">
        <div class="fe__info__ele">
          <div class="fe__info__ele__code">{fe.element.code}</div>
          <div class="fe__info__ele__name">{fe.element.name}</div>
        </div>
        <div class="fe__info__fac">
          <div class="fe__info__fac__sec">{fe.factor.section}</div>
          <div class="fe__info__fac__name">{fe.factor.name}</div>
        </div>
      </div>
    </div>
  {/each}
</main>

<style>
  main {
    width: 44rem;
    color: var(--white);
    margin-top: 2rem;
    padding-bottom: 1rem;
    border-top: thin solid rgba(255, 255, 255, 0.2);
    border-bottom: thin solid rgba(255, 255, 255, 0.2);
    display: flex;
    flex-direction: column;
    align-items: flex-start;
  }
  .fe {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0.5rem;
    margin: 0.5rem;
    padding-bottom: 0;
    margin-bottom: 0;
    padding-right: 0;
    margin-right: 0;
  }
  .fe__color {
    width: 4rem;
    height: 4rem;
    border-radius: 0.15rem;
    margin-right: 0.5rem;
    border: thin solid rgba(255, 255, 255, 0.5);
    box-shadow: 0 0 0.7rem 0 rgba(0, 0, 0, 0.6);
  }
  .fe__info__ele,
  .fe__info__fac {
    display: flex;
    align-items: center;
    max-width: 37.5rem;
  }
  .fe__info__ele {
    margin-bottom: 0.5rem;
  }
  .fe__info__ele__name,
  .fe__info__fac__name {
    margin-left: 0.5rem;
  }
  .fe__info__ele__code {
    background-color: #41425e;
  }
  .fe__info__ele__name {
    background-color: #36446c;
  }
  .fe__info__fac__sec {
    background-color: #613a55;
  }
  .fe__info__fac__name {
    background-color: #40533e;
  }
  .fe__info__ele__code,
  .fe__info__ele__name,
  .fe__info__fac__sec,
  .fe__info__fac__name {
    padding: 0.2rem 0.4rem;
    border-radius: 0.15rem;
  }
</style>
