<script lang="ts">
  import { api } from "../../../modules/request";
  import { FeatureGroupSelected, CountryCodeMap } from "../../../modules/state";
</script>

<main>
  {#each $FeatureGroupSelected.features as feature}
    <div class="li">
      <div class="li__colorbox" style="background-color: {feature.color};" />
      <div class="li__feature">
        <div class="li__feature__ele">
          <div class="li__feature__ele__code">
            {feature.element.code}
          </div>
          <div class="li__feature__ele__name">
            {feature.name.element}
            {#if feature.element.section === "country" && $CountryCodeMap}
              {@const code = feature.element.code}
              {@const flagCode = $CountryCodeMap[code].toLowerCase()}
              <img
                src={`https://flagcdn.com/w40/${flagCode}.png`}
                alt={feature.name.element}
                width="30px"
              />
            {/if}
          </div>
        </div>
        <div class="li__feature__fac">
          <div class="li__feature__fac__section">
            {feature.name.factor_section}
          </div>
          <div class="li__feature__fac__name">
            {feature.name.factor}
          </div>
        </div>
      </div>
    </div>
  {:else}
    피쳐가 하나도 안들어 있어..
  {/each}
</main>

<style>
  .li {
    display: flex;
    align-items: center;
    padding-left: 0.5rem;
  }
  .li__colorbox {
    width: 4rem;
    height: 4rem;
    border-radius: 0.5rem;
    margin: 0 0.5rem;
    box-shadow: 0 0 2rem 0.1rem black;
    border: thin solid white;
  }
  .li__colorbox:first-of-type {
    margin-top: 1rem;
  }
  .li__feature {
    width: 37rem;
  }
  .li__feature__ele {
    display: flex;
    align-items: center;
  }
  .li__feature__ele__code {
    background-color: #41425e;
  }
  .li__feature__ele__name {
    color: var(--white);
    display: flex;
    align-items: center;
    text-align: start;
  }
  .li__feature__ele__name img {
    margin-left: 0.5rem;
  }
  .li__feature__fac {
    display: flex;
    align-items: center;
  }
  .li__feature__fac__section {
    background-color: #613a55;
  }
  .li__feature__fac__name {
    background-color: #40533e;
  }
  .li__feature__ele__code,
  .li__feature__fac__section,
  .li__feature__fac__name {
    margin: 0.5rem;
    padding: 0.2rem 0.4rem;
    border-radius: 0.15rem;
    color: var(--white);
  }
  .li__feature__fac__section,
  .li__feature__fac__name {
    margin-top: 0;
  }
  .li__feature__fac__name {
    margin-left: 0;
  }
</style>
