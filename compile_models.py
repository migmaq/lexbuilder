from model import *
from entry_model import entry_model_factory

def main():
    entry_model = entry_model_factory.model()
    edit_form = entry_model.render_vue_edit_page()
    print(edit_form)
    with open("resources/lexi.html", "w") as text_file:
        text_file.write(edit_form)

main()
