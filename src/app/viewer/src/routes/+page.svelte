<style>
    :global(body) {
        background-color: #333;
        color: #eee;
        font-family: monospace;
    }
    :global(.flex) {
        display: flex;
    }
    :global(.flex-grow) {
        flex-grow: 1;
    }
</style>

<script>
    import Status from "./comps/status.svelte";
    import ImageQuery from "./comps/imagequery.svelte";
</script>

<div class="flex">
    <div>
    </div>
    <div class="flex-grow"></div>
    <div>
        <Status/>
    </div>
</div>

<ImageQuery/>

