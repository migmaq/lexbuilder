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
