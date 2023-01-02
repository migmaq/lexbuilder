function new_item_id() {
    return crypto.randomUUID();
}

function find_ref_idx(items, ref_id) {
    return items.findIndex(e => e.id == ref_id);
}

function insert_item_before(items, ref_id, item) {
    insert_item(items, ref_id, item, true);
}

function insert_item_after(items, ref_id, item) {
    insert_item(items, ref_id, item, false);
}

function insert_item(items, ref_id, item, before) {
    if (!ref_id) {
        items.push(item);
    } else {
        console.info("loloking", items, ref_id);
        let ref_idx = find_ref_idx(items, ref_id);
        console.info("ref_idx", ref_idx);
        if (ref_idx == undefined) {
            throw new Error("Failed to find reference index for insert");
        }
        items.splice(ref_idx+(before?0:1), 0, item);
    }

}

function move_item_up(items, ref_id) {
    let ref_idx = find_ref_idx(items, ref_id);
    if (ref_idx == undefined || ref_idx<1)
        return;
    items.splice(ref_idx-1, 2, items[ref_idx], items[ref_idx-1]);
}

function move_item_down(items, ref_id) {
    let ref_idx = find_ref_idx(items, ref_id);
    if (ref_idx == undefined || ref_idx+1==items.length)
        return;
    items.splice(ref_idx, 2, items[ref_idx+1], items[ref_idx]);
}

function delete_item(items, ref_id) {
    let ref_idx = find_ref_idx(items, ref_id);
    console.info('delete got refidx', ref_idx);
    if (ref_idx == undefined)
        throw new Error("Failed to find item to delete");
    items.splice(ref_idx, 1);
}

/**
 * The mmo data model for an entity is a tree of JS {}'s and []'s.
 *
 * Every {} has a numeric id field.
 *
 * The id's are unique across the entity.
 *
 * To find the next free entity id, this function scans the object tree
 * and finds the current highest value of an "id" field.
 */
function max_id(value) {
    if (Array.isArray(value)) {
        return Math.max(...value.map(v => max_id(v)));
    } else if (typeof value == 'object') {
        let max_child_id = Math.max(...Object.values(value).map(v => max_id(v)));
        let max_local_id = typeof value.id == 'number' ? value.id : -1;
        return Math.max(max_child_id, max_local_id);
    } else {
        return -1;
    }
}

function next_id(value) {
    let current_max_id = max_id(value);
    return current_max_id == -1 ? 1 : current_max_id + 1;
}
