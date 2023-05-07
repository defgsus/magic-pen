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
        align-content: center;
    }
    .overlay .image {
        position: relative;
    }
    .overlay .image img {
        max-height: 750px;
    }

</style>

<script>
    export let images = [];

    let selected_image_index = undefined;

    function select_image(index) {
        selected_image_index = parseInt(index);
        window.removeEventListener("keydown", handle_image_key);
        window.addEventListener("keydown", handle_image_key);
    }

    function close_image() {
        window.removeEventListener("keydown", handle_image_key);
        selected_image_index = null;
    }

    function handle_image_click(event) {
        select_image(event.target.getAttribute("data-index"));
    }

    function handle_image_key(event) {
        //console.log(event.key);
        let handled = true;
        switch (event.key) {
            case "Escape":
            case "Enter":
            case "Return":
                close_image();
                break;
            case "ArrowUp":
            case "ArrowLeft":
                if (images?.length)
                    selected_image_index = (selected_image_index - 1 + images.length) % images.length;
                break;
            case "ArrowDown":
            case "ArrowRight": {
                if (images?.length)
                    selected_image_index = (selected_image_index + 1) % images.length;
                break; }
            default:
                handled = false;
        }
        if (handled)
            event.stopPropagation();

    }

    let selected_image;
    $: selected_image = images?.length ? images[selected_image_index] : null;

</script>


{#if selected_image}
    <div class="overlay" on:click={close_image}>
        <div class="image">
            <img
                src="http://127.0.0.1:8000/image/{selected_image.id}/"
                alt="image with id {selected_image.id}"
            />
        </div>
    </div>
{/if}

<div class="image-grid">
    {#if images?.length}
        {#each images as image, idx}
            <div class="image">
                <img
                    src="http://127.0.0.1:8000/image/{image.id}/"
                    alt="image with id {image.id}"
                    loading="lazy"
                    data-index={idx}
                    on:click={handle_image_click}
                />
                <div>{image.score}</div>
            </div>
        {/each}
    {/if}
</div>