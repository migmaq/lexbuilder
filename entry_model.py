from model import *

def root():
    return Root([entry()])

def entry():
    return RequiredObjectField(
        'entry', 'Entry', 'entry',

        # Spelling (in multiple orthographies)
        ortho_text('spelling', 'Spellings', 'spelling'),

        # Part of speech
        EnumField('part_of_speech', 'Part of Speech'),

        # Multiple definitions
        definitions(),

        # Multiple glosses
        glosses(),
        
        # Examples
        examples(),

        # Pronunciation
        pronunciation_guide(),

        # Alternate grammatical forms
        alternate_grammatical_forms(),

        # Categories, related words
        categories(),
        related_entries(),

        # Linguist and specialist info
        # TODO: experimient with removing other regional forms.
        #TextField('borrowed_word', 'Borrowed Word'),
        other_regional_forms(),
        other_attrs(),
        
        # Notes
        TextAreaField('internal_note', 'Internal Note'),
        TextAreaField('public_note', 'Public Note'),

        status(),
        TextField('last_modified_date', 'Last Modified Date'),
    )

def status():
    return ObjectListField(
        'status', 'Status', 'status',
        IdField(),
        FieldRow(
            TextField('variant', "Mi’kmaq Variant"),
            TextField('status', 'Status'),
            TextField('details', 'Details'))
    )

def ortho_text(name, prompt, scope_name):
    return ObjectListField(
        name, prompt, scope_name,
        IdField(),
        FieldRow(
            TextField('variant', "Mi’kmaq Variant"),  # ZZZ CHANGE
            TextField('text', "Mi’kmaq Text"))
    )

#def ortho_text(name, prompt):
#    return RequiredObjectField(
#        name, prompt, 'ortho',
#        FieldRow(
#            TextField('li', 'Listuguj Spelling'),
#            TextField('sf', 'Smith-Francis Spelling'),
#        ))

#def lexeme():
#    return ortho_text('lexeme', 'Lexeme')

def pronunciation_guide():
    return ortho_text('pronunciation_guide', 'Pronunciation Guide', 'guide')

def related_entries():
    return ObjectListField('related_entries', 'Related Entries', 'entry',
                           IdField(),
                           TextField('unresolved_text', 'Unresolved Text'))
    
def examples():
    return ObjectListField(
        'examples', 'Example Sentences', 'example',
        IdField(),
        TextField('translation', 'Example Sentence (English)'),
        ortho_text('text', 'English Text', 'text'),
    )

def definitions(): # ZZZ CHANGE
    return ObjectListField(
        'definitions', 'Definitions', 'definition',
        IdField(),
        TextField('definition', 'Definition (English)'))

def glosses():
    return ObjectListField(
        'glosses', 'Glosses', 'gloss',
        IdField(),
        TextField('gloss', 'Gloss (English)'))

def alternate_grammatical_forms():
    return ObjectListField(
        'alternate_grammatical_forms', 'Alternate Grammatical Forms', 'form',
        IdField(),
        TextField('gloss', 'Gloss (English)'),
        EnumField('grammatical_form', 'Grammatical Form'),
        ortho_text('text', 'Text', 'text'),
    )

def categories():
    return ObjectListField(
        'categories', 'Categories', 'category',
        IdField(),
        TextField('category', 'Category'))
    
def other_regional_forms():
    return ObjectListField(
        'other_regional_forms', 'Other Regional Forms', 'form',
        IdField(),
        TextField('text', 'Text'))

def other_attrs():
    return ObjectListField(
        'attrs', 'Other Attributes', 'attr',
        IdField(),
        FieldRow(
            TextField('attr', 'Attr'),
            TextField('value', 'Value'),
        ))

entry_model_factory = ModelFactory(root)
