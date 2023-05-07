<script>
    async function fetchStatus() {
        const response = await fetch("http://127.0.0.1:8000/status/")
            .then(r => r.json());
        return response;
    }

    let promise = fetchStatus();
</script>

<div>
    {#await promise}
        ...
    {:then status}
        {#each Object.keys(status) as key}
            {#if (key !== "embeddings")}
                <div>{key}: {status[key]}</div>
            {:else}
                <div>{key}:</div>
                {#each status[key] as embedding}
                    <div>- {embedding.model}: {embedding.count}</div>
                {/each}
            {/if}
        {/each}
    {:catch error}
        <p style="color: red">{error.message}</p>
    {/await}
</div>
