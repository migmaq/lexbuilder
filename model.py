from deps.bottle import template
from enum import Enum
from textwrap import indent
import sys
import json
import io

class Node:
    """Superclass for content model definition nodes"""
    
    def __init__(self, contents=[]):
        self.contents = contents

        # Contained fields is an alternative way of traversing
        # the Node tree that only includes Fields and Field Containers
        # (which are also fields).
        contained_fields = []
        for c in contents:
            if isinstance(c, Field):
                contained_fields.append(c)
            else:
                contained_fields.extend(c.contained_fields)
        self.contained_fields = contained_fields
        if isinstance(self, Field):
            for contained_field in contained_fields:
                assert contained_field.parent_field == None
                contained_field.parent_field = self

    def dump_layout(self, out, indent=''):
        """Debug dump of this content model"""
        self.dump_layout_header(out, indent)
        out.write('\n')
        indent += '  '
        for c in self.contents:
            c.dump_layout(out, indent)

    def dump_layout_header(self, out, indent=''):
        out.write(f'{indent}{self.__class__.__name__} ')
    
    def render_vue_form(self, out, indent, scope):
        """Render a VUE form that can edit instances of this model."""
        for c in self.contents:
            c.render_vue_form(out, indent, scope)

    def render_vue_script(self, out, indent, scope):
        """Render support script for the VUE form"""
        for c in self.contents:
            c.render_vue_script(out, indent, scope)

    def collect_vue_exports(self, out):
        """ """
        for c in self.contents:
            c.collect_vue_exports(out)
    
class Root(Node):
    def __init__(self, contents=[]):
        super().__init__(contents=contents)
        if len(self.contained_fields) != 1:
            raise ValidationError(self.path(), f'expected model root to have exactly one contained field')
        self.root_field = self.contained_fields[0]

    def render_vue_edit_page(self):
        out = io.StringIO()

        out.write('\n')
        self.render_vue_form(out, '           ', '')
        out.write('\n')
        rendered_form = out.getvalue()

        out = io.StringIO()
        self.root_field.default_value_js(out, '                 ')
        default_value_js = out.getvalue()

        out = io.StringIO()
        out.write('\n')
        self.render_vue_script(out, '                 ', '')
        out.write('\n')
        rendered_script = out.getvalue()

        view_exports = []
        self.collect_vue_exports(view_exports)
        view_exports.append('entry')

        page = """\
<!DOCTYPE html>
<html>
    <head>
        <link href="https://fonts.googleapis.com/css?family=Roboto:100,300,400,500,700,900|Material+Icons" rel="stylesheet" type="text/css">
        <link href="https://cdn.jsdelivr.net/npm/quasar@2.10.1/dist/quasar.prod.css" rel="stylesheet" type="text/css">
        <link href="/resources/mmo.css" rel="stylesheet" type="text/css">
    </head>

    <body>
        <div id="app" class="q-pa-md">

    """+rendered_form+"""

        </div>

        <script src="https://cdn.jsdelivr.net/npm/vue@3/dist/vue.global.prod.js"></script>
        <script src="https://cdn.jsdelivr.net/npm/quasar@2.10.1/dist/quasar.umd.prod.js"></script>
        <script src="/resources/mmo.js"></script>

        <script>
         const { createApp, ref } = Vue;

         const app = createApp({
             setup() {
                 const _entry = """+default_value_js+""";
                 let id = next_id(_entry);
                 const entry = ref(_entry);

    """+rendered_script+"""

                 return {"""+','.join(view_exports)+"""};

         }});

         app.use(Quasar);
         app.mount('#app');

        </script>

    </body>
</html>"""
        
        return page
        
class Quantifier(Enum):
    Optional = 1
    Required = 2
    List = 3

class Field(Node):
    def __init__(self, name, prompt, contents=[]):
        super().__init__(contents=contents)
        self.prompt = prompt
        self.name = name
        self.parent_field = None
        self._path = None

    def dump_layout_header(self, out, indent=''):
        super().dump_layout_header(out, indent)
        out.write(f'name="{self.name}" prompt="{self.prompt}"')

    def render_js_max_id_expr(self):
        return None

    def path(self):
        if self._path == None:
            self._path = f'{self.parent_field.path()}_{self.name}' if self.parent_field else self.name
        return self._path

    def validate(self, value):
        """Validates an instance WRT this model."""
        raise ValidationError(f'validation not implemented for {self.__class__.__name__}')
        
    def dump_schema(self, out, indent=''):
        self.dump_schema_header(out, indent)
        out.write('\n')
        indent += '  '
        for c in self.contained_fields:
            c.dump_schema(out, indent)

    def dump_schema_header(self, out, indent=''):
        self.dump_layout_header(out, indent)

    def default_value(self):
        """Returns the default value for an instance of this model."""
        return None

    def default_value_js(self, out, indent):
        pass

class ObjectField(Field):
    def __init__(self, name, prompt, scope_name, quantifier, *args):
        super().__init__(name, prompt, contents=args)
        self.scope_name = scope_name
        self.quantifier = quantifier

    def validate(self, value):
        if not isinstance(value, dict):
            raise ValidationError(self.path(), f'expected dict for object field got {value}')
        field_keys = set([f.name for f in self.contained_fields])
        value_keys = set(value.keys())
        if field_keys != value_keys:
            extra_keys_in_value = value_keys - field_keys
            keys_missing_in_value = field_keys - value_keys
            raise ValidationError(self.path(), f'object field malformed extra-keys: {extra_keys_in_value}, missing_keys: {keys_missing_in_value}')
        for f in self.contained_fields:
            f.validate(value[f.name])
            
    def default_object_value(self):
        v = dict()
        for f in self.contained_fields:
            v[f.name] = f.default_value()
        return v

    def default_object_value_js(self, out, indent):
        out.write('{\n')
        brace_indent = indent + '  '
        content_indent = brace_indent + '  '
        for (idx, fld) in enumerate(self.contained_fields):
            if idx > 0:
                out.write(',\n')
            out.write(f'{content_indent}{fld.name}: ')
            fld.default_value_js(out, content_indent)
        out.write('\n')
        out.write(f'{brace_indent}}}')

    def default_value_js(self, out, indent):
        self.default_object_value_js(out, indent)
        
class ObjectListField(ObjectField):
    def __init__(self, name, prompt, scope_name, *args):
        super().__init__(name, prompt, scope_name, Quantifier.List, *args)

    def validate(self, value):
        if not isinstance(value, list):
            raise ValidationError(self.path(), f'expected list for list field')
        for v in value:
            super().validate(v)
        
    def render_vue_form(self, out, indent, scope):
        print(f'{indent}<div class="text-h4">{self.prompt}</div>', file=out)
        #print(f'{indent}<ul>', file=out)
        print(f'{indent}  <div v-for="{self.scope_name} in {scope}{self.name}" :key="{self.scope_name}.id">', file=out)
        for c in self.contents:
            c.render_vue_form(out, indent+'    ', f'{self.scope_name}.')
                    
        print(f'{indent}  </div>', file=out)
        print(f'{indent} <button @click="insert_{self.path()}({scope}{self.name}, {self.scope_name})">Add {self.prompt}</button>', file=out)
        #print(f'{indent}</ul>', file=out)


    def render_vue_script(self, out, indent, scope):
        out.write(f'{indent}function insert_{self.path()}(elems, ref_elem) {{\n')
        out.write(f'{indent}  elems.push(')
        self.default_object_value_js(out, indent)
        out.write(f');\n')
        out.write(f'{indent}}}\n\n')
        super().render_vue_script(out, indent, scope)
        
    def collect_vue_exports(self, out):
        out.append(f'insert_{self.path()}')
        super().collect_vue_exports(out)
        
    def default_value(self):
        return []

    def default_value_js(self, out, indent):
        out.write('[]')

class RequiredObjectField(ObjectField):
    def __init__(self, name, prompt, scope_name, *args):
        super().__init__(name, prompt, scope_name, Quantifier.Required, *args)

    def validate(self, value):
        super().validate(value)
        
    def render_vue_form(self, out, indent, scope):
        for c in self.contents:
            c.render_vue_form(out, indent, f'{scope}{self.name}.')

    def default_value(self):
        return self.default_object_value()

class IdField(Field):
    def __init__(self, name='id', prompt='Id', **kwargs):
        super().__init__(name, prompt, **kwargs)

    def validate(self, value):
        # TODO: should also check uniqueness within document.
        #if isinstance(value, str):
        #    raise ValidationError(self.path(), f'expected str for text field')
        # TODO
        pass
        
    def render_vue_form(self, out, indent, scope):
        pass

    def default_value(self):
        return '' # XXX TODO ???

    def default_value_js(self, out, indent):
        out.write('id++') # TEMP HACK - FIX

    def render_js_max_id_expr(self):
        return None
        
        
class TextField(Field):
    def __init__(self, name, prompt, width=None, **kwargs):
        super().__init__(name, prompt, **kwargs)
        self.width = width

    def validate(self, value):
        if not isinstance(value, str):
            raise ValidationError(self.path(), f'expected str for text field')
        
    def render_vue_form(self, out, indent, scope):
        print(f'{indent}<q-input v-model="{scope}{self.name}" label="{self.prompt}"></q-input>', file=out)

    def default_value(self):
        return ''

    def default_value_js(self, out, indent):
        out.write('""')
    
class TextAreaField(TextField):
    def __init__(self, name, prompt, width=None, **kwargs):
        super().__init__(name, prompt, **kwargs)
        self.width = width

    def default_value(self):
        return ''

    def default_value_js(self, out, indent):
        out.write('""')
    
class EnumField(Field):
    def __init__(self, name, prompt, **kwargs):
        super().__init__(name, prompt, **kwargs)

    def validate(self, value):
        if not isinstance(value, str):
            raise ValidationError(self.path(), f'expected str for enum field')
        
    def default_value(self):
        return ''

    def default_value_js(self, out, indent):
        out.write('""')
    
class Decoration(Node):
    def __init__(self, contents=[]):
        super().__init__(contents)
    
class Heading(Decoration):
    def __init__(self, title):
        super().__init__()
        self.title = title

class Row(Decoration):
    def __init__(self, *args):
        super().__init__(contents=args)

    def render_vue_form(self, out, indent, scope):
        print(f'{indent}<div class="row">', file=out)
        for c in self.contents:
            print(f'{indent}  <div class="col">', file=out)
            c.render_vue_form(out, indent+'    ', scope)
            print(f'{indent}  </div>', file=out)
        print(f'{indent}</div>', file=out)
        
class ValidationError(Exception):
    pass

class NotImplementedError(Exception):
    pass

class Model:
    def __init__(self, root):
        self.root = root

class ModelFactory:
    def __init__(self, root_fn):
        self.root_fn = root_fn
        self._model = None

    def model(self):
        if self._model == None:
            self._model = self.root_fn()
        return self._model


