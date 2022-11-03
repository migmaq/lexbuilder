import pymongo
from pymongo import MongoClient, InsertOne, DeleteOne, ReplaceOne
import datetime
import pprint
import json
import sys
from pathlib import Path
import re

sys.stdin.reconfigure(encoding='utf-8')
sys.stdout.reconfigure(encoding='utf-8')

def lexeme_to_id(lexeme):
    return re.sub(r"[^A-Za-z0-9_]", "_", lexeme.lower())

def main():

    # Load lexemes we have exported from legacy mmo
    mmo_json = None
    with open('import-data/legacy-mmo.json') as f:
        mmo_json = json.load(f)
    assert len(mmo_json) == 1, f"Expected root of mmo.json to be dict with one key"
    lexemes = mmo_json['lexemes']
    print('Loaded', len(lexemes), 'lexemes')

    # Assert some things about the lexemes that we are investigating or
    # depending on.
    lexemes_with_multiple_parts_of_speech = 0
    for l in lexemes:
        lexeme_id = l['id']
        #print(l)
        subentries = l['subentries']
        if len(subentries) != 1:
            #print(lexeme_id, 'has', len(subentries), 'subentries')
            assert len(subentries) == 1, "Only one subentry per word supported"
        subentry = subentries[0]
        parts_of_speech = subentry['partsOfSpeech']
        if len(parts_of_speech) != 1:
            #print(lexeme_id, 'has', len(parts_of_speech), 'parts of speech')
            assert len(parts_of_speech) <= 3, "No more than 3 parts of speech"
            assert len(parts_of_speech) != 0, "word has no parts of speech"
            lexemes_with_multiple_parts_of_speech = lexemes_with_multiple_parts_of_speech + 1

    print(f"{lexemes_with_multiple_parts_of_speech} lexemes with multiple parts of speech")

    # convert to new format
    entries = []
    for src_lexeme in lexemes:
        entries.extend(convert_lexeme_to_entries(src_lexeme))

    # spew new format to JSON
    with open('import-data/entries.json', 'w') as f:
        json.dump(entries, f, sort_keys=False, indent=2, ensure_ascii=False)

    # convert to NestedText (just for a human readable version)
    #nestedtext_content = nt.dumps(entries, indent=2, width=0) + "\n"
    #with open('entries.nt', 'w') as f:
    #    f.write(nestedtext_content)
        
    # spew leftovers to JSON
    with open('import-data/leftovers.json', 'w') as f:
        json.dump(lexemes, f, sort_keys=False, indent=2, ensure_ascii=False)

    # import into database
    import_json_into_db(entries)
        

def import_json_into_db(entries):
    print('Importing entries into db')
    client = MongoClient('localhost', 27000)
    db = client.mmo
    db.entries.drop()
    entries_collection = db.entries
    result = entries_collection.bulk_write([InsertOne(e) for e in entries])
    print('Insert result', result.inserted_count)
    print('DB now has', entries_collection.count_documents({}), 'records')


def convert_lexeme_to_entries(src_lexeme):

    attrs = dict()
    
    date = src_lexeme.pop('date') # TODO put date in.
    lexeme = src_lexeme.pop('name')
    derived_id = src_lexeme.pop('id')
    assert derived_id == lexeme_to_id(lexeme), f"id rederivation inconsistency lex:{lexeme} lex_to_id:{lexeme_to_id(lexeme)} imported_derived_id:{derived_id}"
    note = src_lexeme.pop('note')
    picture = src_lexeme.pop('picture')
    #if picture:
    #    print('picture', picture)
    # TODO status map
    status = src_lexeme.pop('status')
    assert len(src_lexeme.pop('errors')) == 0
    assert not src_lexeme.pop('explicitSfGloss')
    
    src_subentries = src_lexeme['subentries']
    assert len(src_subentries)==1, "Only one subentry per lexeme supported"
    src_subentry = src_subentries[0]
    src_parts_of_speech = src_subentry['partsOfSpeech']
    assert len(src_parts_of_speech) > 0, "Each lexeme must have at least one part of speech"
    recordings = src_subentry.pop('recordings')
    watsonSpelling = src_lexeme.pop('watsonSpelling')
    if watsonSpelling and watsonSpelling != lexeme:
        attrs['watson_spelling'] = watsonSpelling
        
    borrowed_word = src_subentry.pop('borrowedWord')
    assert not src_subentry.pop('label')
    phonetic_form = src_subentry.pop('phoneticForm')

    out_entries = []
    for (idx, pos) in enumerate(src_parts_of_speech):
        part_of_speech_label = pos.pop('label')
        for sense in pos['senses']:
            out_entries.extend(convert_sense(date, lexeme, note, status, borrowed_word, phonetic_form, part_of_speech_label, recordings, sense, attrs, len(out_entries)))

    return out_entries

# for pacific: picture of reference - what refer to

def convert_sense(date, lexeme, note, status, borrowed_word, phonetic_form, part_of_speech_label, recordings, sense, attrs, idx):


    lex_text = dict()
    lex_text['li'] = lexeme
    lex_text['sf'] = ""
    #lex_text['mp'] = ""
    
    entry = dict()
    entry['lexeme'] = lex_text
    # remodel status TODO: skip/done ???
    assert status=='done' or status=='skip', 'unknown status {status}'
    entry['status'] = status
    
    # remodel date TODO toolbox last edit date.
    entry['date'] = date
    entry['internal_note'] = note
    entry['public_note'] = ''
    entry['borrowed_word'] = borrowed_word
    # TODO is phonetic_form a li/sf thing as well?
    # - maybe different by ortho ...
    # - copy li to  ...
    entry['pronunciation_guide'] = { 'li': phonetic_form };
    entry['part_of_speech'] = part_of_speech_label

    # TODO should cross_ref resolve?  Try to resolve?
    # what does it mean anyway?
    # cross ref presently is in li.
    # Are supposed to resolve.
    # confusing cross ortho!!!
    # - Related words.
    # - Related lexemes.
    # - related_entries
    entry['related_entries'] = sense.pop('crossRef')  # TODO should be list of lexes
    entry['definition'] = sense.pop('definition')
    #assert not sense.pop('label')
    assert len(sense.pop('notes')) == 0
    sense.pop('picture')
    scientific_name = sense.pop('scientificName')
    if scientific_name:
        attrs['scientific_name'] = scientific_name

    table = sense.pop('table')
    if table:
        attrs['legacy_alternate_grammatical_forms'] = table
    literally = sense.pop('literally')
    if literally:
        attrs['literally'] = literally
    
    #entry['recordings'] = recordings

    entry['examples'] = [convert_example(ex) for ex in sense['examples']]
        
    entry['glosses'] = [g['text'] for g in sense.pop('glosses')]

    # Example conjugations
    # TODO rename to Alternate Forms
    entry['alternate_grammatical_forms'] = [convert_alternate_form(af) for af in sense['lexicalFunctions']]

    # TODO can I rename to categories?
    entry['categories'] = sense.pop('semanticDomains')
    
    # WTF: 'other_regional_forms', li, sf
    entry['other_regional_forms'] = [f['label'] for f in sense.pop('variantForms')]
    # - text, region, gloss

    entry['attrs'] = attrs

    
    return [entry]

# "lexicalFunctions" : [ {
#     "gloss" : "I'm hanging around",
#     "label" : "1",
#     "lexeme" : "alei",
#     "sfGloss" : ""
#     }, { ... } ]
def convert_alternate_form(src):
    out = dict()
    out['gloss'] = src.pop('gloss')
    out['grammatical_form'] = src.pop('label')
    text = dict()
    text['li'] = src.pop('lexeme') # TODO Is li/sf good names?
    text['sf'] = src.pop('sfGloss')
    out['text'] = text
    return out
    

#          "examples" : [ {
#            "exampleEnglish" : "It's sitting on the bare ground, lay something under it.",
#            "exampleSentence" : "Metaqateg maqamigeg, natgoqwei lame'g lega'tu.",
#            "exampleSf" : "",
#            "recordings" : [ {
#              "filename" : "media/m/metaqateg/phrase1.wav",
#              "recordedBy" : "dmm"
#            } ]
#          } ],

def convert_example(src):
    out = dict()
    out['translation'] = src.pop('exampleEnglish')
    text = dict()
    text['li'] = src.pop('exampleSentence')
    text['sf'] = src.pop('exampleSf')
    out['text'] = text
    #out['recordings'] = src.pop('recordings')
    return out
        
if __name__ == "__main__":
    main()
