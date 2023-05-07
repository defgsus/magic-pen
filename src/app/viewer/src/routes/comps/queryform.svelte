<script>
    import { createEventDispatcher } from 'svelte';
    const dispatch = createEventDispatcher();

    export let text = "hallo";
    export let count = 10;

    function handle_submit() {
        dispatch('submit', {
            text, count,
        });
    }
</script>


<form on:submit|preventDefault={handle_submit}>
    <div class="flex">
        <div class="flex-grow">
            <input type="text" name="text" value="{text}" style="width: 98%" on:change={e => text = e.target.value}/>
        </div>
        <div>
            <input type="number" name="count" value="{count}" style="width: 5rem" on:change={e => count = parseInt(e.target.value)}/>
        </div>
        <div>
            <button type="submit">-></button>
        </div>
    </div>
</form>