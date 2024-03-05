<script lang="ts">
  import { Text } from "../../modules/state";
  import { format } from "../../modules/functions";
  import type { PublicFgRespType } from "./function";

  export let data: PublicFgRespType;

  let desc = data.feature_group.description;
  if (!desc) desc = $Text.GroupNoteNoneText;
</script>

<main>
  <div class="share-title">
    {format($Text.f_ShareTitle, { name: data.user })}
  </div>
  <div class="group-name">{data.feature_group.name}</div>
  <pre class="group-description">{desc}</pre>
</main>

<style>
  main {
    width: 44rem;
    color: var(--white);
  }
  .share-title {
    text-align: end;
  }
  .group-name {
    display: flex;
    justify-content: center;
    margin-top: 0.5rem;
    font-size: 1.4rem;
  }
  .group-description {
    white-space: pre-wrap;
    word-wrap: break-word;
    margin-top: 0.5rem;
    padding-top: 0.5rem;
    border-top: thin solid rgba(255, 255, 255, 0.2);
    padding-right: 1rem;
    padding-left: 1rem;
  }
</style>
