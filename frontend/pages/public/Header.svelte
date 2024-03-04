<script lang="ts">
  import { Text } from "../../modules/state";
  import { format } from "../../modules/functions";

  export let data: any;
</script>

<div>{format($Text.f_ShareTitle, { name: data.user })}</div>
