from model import *

def entry_model():
    return RequiredObjectField(
        'entry', 'Entry', 'entry',

        # Lexeme
        lexeme_model(),

        # Definition, glosses etc
        EnumField('part_of_speech', 'Part of Speech'),
        pronunciation_guide_model(),
        TextField('definition', 'Definition'),
        examples_model(),
        glosses_model(),
        alternate_grammatical_forms_model(),

        # Categories, related words
        categories_model(),
        related_entries_model(),

        # Linguist and specialist info
        TextField('borrowed_word', 'Borrowed Word'),
        other_regional_forms_model(),
        other_attrs_model(),

        # Notes
        TextAreaField('internal_note', 'Internal Note'),
        TextAreaField('public_note', 'Public Note')
    )

def ortho_text_model(name, prompt):
    return RequiredObjectField(
        name, prompt, 'ortho',
        Row(
            TextField('li', 'Listuguj Spelling'),
            TextField('sf', 'Smith-Francis Spelling'),
        ))

def lexeme_model():
    return ortho_text_model('lexeme', 'Lexeme')

def pronunciation_guide_model():
    return RequiredObjectField(
        'pronunciation_guide', 'Pronunciation Guide', 'guide',
        Row(
            TextField('li', 'Listuguj Pronunciation'),
            TextField('sf', 'Smith-Francis Pronunciation')
        ))

def related_entries_model():
    return ObjectListField('related_entries', 'Related Entries', 'entry',
                           IdField(),
                           TextField('entry', 'Entry'))
    
def examples_model():
    return ObjectListField(
        'examples', 'Examples', 'example',
        IdField(),
        TextField('translation', 'Translation'),
        ortho_text_model('text', 'Text'),
    )
    
def glosses_model():
    return ObjectListField(
        'glosses', 'Glosses', 'gloss',
        IdField(),
        TextField('gloss', 'Gloss'))

def alternate_grammatical_forms_model():
    return ObjectListField(
        'alternate_grammatical_forms', 'Alternate Grammatical Forms', 'form',
        IdField(),
        TextField('gloss', 'Gloss'),
        EnumField('grammatical_form', 'Grammatical Form'),
        ortho_text_model('text', 'Text'),
    )

def categories_model():
    return ObjectListField(
        'categories', 'Categories', 'category',
        IdField(),
        TextField('category', 'Category'))
    
def other_regional_forms_model():
    return ObjectListField(
        'other_regional_forms', 'Other Regional Forms', 'form',
        IdField(),
        TextField('text', 'Text'))

def other_attrs_model():
    return ObjectListField(
        'attrs', 'Other Attributes', 'attr',
        IdField(),
        Row(
            TextField('name', 'Name'),
            TextField('value', 'Value'),
        ))
