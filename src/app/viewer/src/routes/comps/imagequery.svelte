
<script>
    import ImageGrid from "./imagegrid.svelte";
    import QueryForm from "./queryform.svelte";

    let images = [];

    function query_images(event) {
        fetch("http://127.0.0.1:8000/query/", {
            method: "post",
            body: JSON.stringify(event.detail),
        })
            .then(r => r.json())
            .then(r => images = r.images)
    }
</script>

<QueryForm on:submit={query_images}/>

<ImageGrid images={images}/>
