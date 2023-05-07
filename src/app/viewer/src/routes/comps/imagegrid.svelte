<style>
    .image-grid {
        display: flex;
        flex-direction: row;
        flex-wrap: wrap;
    }
    .image-grid .image {
        margin: .5rem;
    }
    .image-grid img:hover {
        box-shadow: 0 0 5px #aaa;
    }
    .image-grid .image img {
        max-width: 150px;
    }

    .overlay {
        position: fixed;
        top: 0;
        width: 100%;
        height: 100%;
        z-index: 10;
        background-color: rgba(0, 0, 0, .6);
        display: flex;
        justify-content: center;
    }

</style>

<script>
    export let images;

    let selected_image_id = null;
    function handle_image_click(event) {
        selected_image_id = event.target.getAttribute("data-id");
    }

    function handle_image_key(event) {
        console.log(event.key);
        event.stopPropagation();
        selected_image_id = null;
    }

</script>

{#if selected_image_id}
    <div class="overlay" on:click={e => selected_image_id = null} on:keydown={handle_image_key}>
        <div class="image">
            <img
                src="http://127.0.0.1:8000/image/{selected_image_id}/"
                alt="image with id {selected_image_id}"
            />
        </div>
    </div>
{/if}

<div class="image-grid">
    {#if images}
        {#each images as image}
            <div class="image">
                <img
                    src="http://127.0.0.1:8000/image/{image.id}/"
                    alt="image with id {image.id}"
                    loading="lazy"
                    data-id={image.id}
                    on:click={handle_image_click}
                />
                <div>{image.score}</div>
            </div>
        {/each}
    {/if}
</div>