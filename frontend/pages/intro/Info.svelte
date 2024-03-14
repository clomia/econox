<script lang="ts">
  import { Lang } from "../../modules/state";
  import { infoText } from "./text";
  import TiltedCheck from "../../assets/icon/TiltedCheck.svelte";
  import LinkIcon from "../../assets/icon/LinkIcon.svelte";
  import HrefButton from "../../components/HrefButton.svelte";
</script>

<main>
  <section class="tags">
    {#each infoText.tags as tag}
      <span>
        <div class="check-icon"><TiltedCheck /></div>
        {tag[$Lang]}
      </span>
    {/each}
  </section>
  <section class="benefits">{infoText.benefit[$Lang]}</section>
  <section class="cost">
    <div class="cost__title">{infoText.cost.title[$Lang]}</div>
    <div class="cost-grid">
      <div class="cost-type">{infoText.cost.type1[$Lang]}</div>
      <div>{infoText.cost.type1Price[$Lang]}</div>
      <div>{infoText.cost.type1Desc[$Lang]}</div>
      <div class="cost-type">{infoText.cost.type2[$Lang]}</div>
      <div>{infoText.cost.type2Price[$Lang]}</div>
      <div>{infoText.cost.type2Desc[$Lang]}</div>
    </div>
    <div class="cost__ref">
      <div class="cost__ref__refund">
        <LinkIcon size="0.8rem" />
        <a
          href="https://www.econox.wiki"
          target="_blank"
          rel="noopener noreferrer"
        >
          {infoText.cost.refund[$Lang]}
        </a>
      </div>
    </div>
    <div class="cost__func-ref">
      <HrefButton
        href="https://www.econox.wiki"
        content={infoText.funcRef[$Lang]}
      />
    </div>
  </section>
  <section class="extra">
    <div class="extra__title">{infoText.download.title[$Lang]}</div>
    <div class="extra__content1">{infoText.download.content1[$Lang]}</div>
    <div class="extra__content2">{infoText.download.content2[$Lang]}</div>
  </section>
</main>

<style>
  main {
    width: 100%;
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
    color: rgba(255, 255, 255, 0.7);
  }
  .check-icon {
    opacity: 0.6;
    padding-right: 0.4rem;
  }
  .tags {
    width: 100%;
    display: flex;
    flex-wrap: wrap;
    justify-content: center;
    padding: 0 5rem;
  }
  .tags span {
    white-space: nowrap;
    padding: 0.2rem 1rem;
    display: flex;
    align-items: center;
  }
  .benefits {
    font-size: 1.2rem;
    color: rgba(255, 255, 255, 0.8);
    margin-top: 3rem;
    padding: 0 2rem;
    text-align: center;
  }
  .cost {
    margin-top: 1.5rem;
    padding: 0 2rem;
  }
  .cost__title {
    display: flex;
    width: 100%;
    justify-content: center;
    font-size: 1.5rem;
    padding-bottom: 0.5rem;
  }
  .cost-grid {
    display: grid;
    grid-template-columns: repeat(3, auto);
    grid-template-rows: repeat(2, auto);
    row-gap: 3px;
  }
  .cost-grid > :nth-child(-n + 3) {
    border-bottom: thin solid rgba(255, 255, 255, 0.2);
    padding-bottom: 3px;
  }
  .cost-grid div {
    padding-right: 0.5rem;
  }
  .cost__ref {
    display: flex;
    justify-content: flex-end;
    align-items: center;
    opacity: 0.7;
    margin-top: 0.7rem;
  }
  .cost__ref div {
    display: flex;
    align-items: center;
  }
  .cost__ref div a {
    color: white;
    text-decoration: none;
    margin-left: 0.3rem;
  }
  .cost__ref div a:hover {
    cursor: pointer;
    text-decoration: underline;
  }
  .cost__func-ref {
    display: flex;
    align-items: center;
    opacity: 0.7;
  }
  .extra {
    margin-top: 2rem;
    padding-bottom: 2rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    width: 100%;
    text-align: center;
  }
  .extra__title {
    font-size: 1.3rem;
    padding-bottom: 0.5rem;
  }
  .extra__content1 {
    padding-bottom: 0.5rem;
  }
  .extra__content1,
  .extra__content2 {
    padding: 0 2rem;
  }
</style>
