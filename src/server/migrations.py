from pymongo.database import Database
from server.migration_functions import register_migration

@register_migration(1, "Rename 'variants'/'variant' fields to 'comments' on recipes")
def migration_001(db: Database):
    recipes = db.get_collection('recipes')

    # Find documents that have legacy fields
    cursor = recipes.find({"$or": [{"variants": {"$exists": True}}, {"variant": {"$exists": True}}]})

    updated = 0
    for doc in cursor:
        legacy = []
        if 'variants' in doc and isinstance(doc['variants'], list):
            legacy = doc['variants']
        elif 'variant' in doc:
            # single variant -> wrap it
            legacy = [doc['variant']] if doc['variant'] is not None else []

        existing_comments = doc.get('comments', []) if isinstance(doc.get('comments', []), list) else []

        new_comments = []
        for v in legacy:
            if isinstance(v, dict):
                # Map common/likely fields from old Variant objects to Comment fields
                mapped = {}
                if 'userId' in v:
                    mapped['userId'] = v['userId']
                elif 'user' in v:
                    mapped['userId'] = v['user']

                # comment text could be stored under different keys
                mapped['comment'] = v.get('comment') or v.get('text') or v.get('body') or v.get('value')

                # initials
                if 'initials' in v:
                    mapped['initials'] = v['initials']
                elif 'authorInitials' in v:
                    mapped['initials'] = v['authorInitials']

                # Only add if we at least have a comment text
                if mapped.get('comment'):
                    new_comments.append(mapped)
            else:
                # primitive types -> store as comment text
                new_comments.append({'comment': str(v)})

        if new_comments:
            merged = existing_comments + new_comments
            update_ops = {'$set': {'comments': merged}, '$unset': {}}
            # unset whichever legacy key exists
            if 'variants' in doc:
                update_ops['$unset']['variants'] = ""
            if 'variant' in doc:
                update_ops['$unset']['variant'] = ""

            recipes.update_one({'_id': doc['_id']}, update_ops)
            updated += 1

    print(f"Migration 001: updated {updated} recipes")
