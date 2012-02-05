# -*- coding: utf-8 -*-

from __future__ import unicode_literals  # unicode by default

import unittest


def schema_factory(nodes=None):
    import deform
    from colander import Schema
    from colander import SchemaNode
    from colander import String
    from colander import Integer
    from colander import Float
    from colander import DateTime
    from colander import null

    attributes = {}
    if nodes is None or 'id_column' in nodes:
        attributes['id_column'] = SchemaNode(Integer(),
                widget=deform.widget.HiddenWidget(), description='id_column')
    if nodes is None or 'unicode_column' in nodes:
        attributes['unicode_column'] = SchemaNode(String(),
                description='unicode_column')
    if nodes is None or 'integer_column' in nodes:
        attributes['integer_column'] = SchemaNode(Integer(), missing=null,
                description='integer_column')
    if nodes is None or 'float_column' in nodes:
        attributes['float_column'] = SchemaNode(Float(), missing=null,
                description='float_column')
    if nodes is None or 'datetime_column' in nodes:
        attributes['datetime_column'] = SchemaNode(DateTime(), missing=null,
                description='datetime_column')

    return type(b'Schema', (Schema, ), attributes)


class TestConversion(unittest.TestCase):
    def _makeModel(self):
        """ Make a sqlalchemy model. """
        from sqlalchemy import Column
        from sqlalchemy.types import Unicode
        from sqlalchemy.types import Integer
        from sqlalchemy.types import Float
        from sqlalchemy.types import DateTime
        from sqlalchemy.ext.declarative import declarative_base
        Base = declarative_base()

        class Model(Base):
            __tablename__ = 'model'

            id_column = Column(Integer, primary_key=True, autoincrement=True)
            unicode_column = Column(Unicode, nullable=False,
                    default='Default Text')
            integer_column = Column(Integer, default=10)
            float_column = Column(Float)
            datetime_column = Column(DateTime)

        return Model

    def _makeSchema(self, nodes=None):
        """ Make a colander schema. """
        return schema_factory(nodes)

    def test__get_co_type_by_sa_type(self):
        from sqlalchemy.types import Unicode
        from sqlalchemy.types import Integer
        from sqlalchemy.types import Float
        from sqlalchemy.types import DateTime
        import colander
        import sqlalchemy2deform

        co_type = sqlalchemy2deform._get_co_type_by_sa_type(Unicode)
        self.assertEqual(co_type, colander.String)

        co_type = sqlalchemy2deform._get_co_type_by_sa_type(Integer)
        self.assertEqual(co_type, colander.Integer)

        co_type = sqlalchemy2deform._get_co_type_by_sa_type(Float)
        self.assertEqual(co_type, colander.Float)

        co_type = sqlalchemy2deform._get_co_type_by_sa_type(DateTime)
        self.assertEqual(co_type, colander.DateTime)

        class AnotherUnicode(Unicode):
            pass
        co_type = sqlalchemy2deform._get_co_type_by_sa_type(AnotherUnicode)
        self.assertEqual(co_type, colander.String)

    def test__get_columns_co_types(self):
        import colander
        from sqlalchemy.orm import class_mapper
        import sqlalchemy2deform

        M = self._makeModel()
        mapper = class_mapper(M)
        co_types = sqlalchemy2deform._get_columns_co_types(mapper)
        self.assertEqual(co_types, {'id_column': colander.Integer,
                                    'unicode_column': colander.String,
                                    'integer_column': colander.Integer,
                                    'float_column': colander.Float,
                                    'datetime_column': colander.DateTime})

    def test_get_required_columns(self):
        import sqlalchemy2deform

        M = self._makeModel()
        sa_required = [i for i in sqlalchemy2deform.get_required_columns(M)]
        self.assertEqual(sa_required, ['id_column', 'unicode_column'])

    def test_get_autoincrement_columns(self):
        import sqlalchemy2deform

        M = self._makeModel()
        sa_types = [i for i in sqlalchemy2deform.get_autoincrement_columns(M)]
        self.assertEqual(sa_types, ['id_column'])

    def test_make_schema(self):
        import sqlalchemy2deform

        M = self._makeModel()
        S = self._makeSchema()

        myschema = S()
        schema = sqlalchemy2deform.make_schema(M)

        myschema_nodes = myschema.children
        for i, node in enumerate(schema):
            self.assertEqual(node.typ.__class__,
                    myschema_nodes[i].typ.__class__)
            self.assertEqual(node.required, myschema_nodes[i].required)

        self.assertEqual(schema.typ.__class__, myschema.typ.__class__)

    def test_make_schema_with_columns(self):
        import sqlalchemy2deform

        columns = ['unicode_column', 'datetime_column']

        M = self._makeModel()
        S = self._makeSchema(columns)

        myschema = S()
        schema = sqlalchemy2deform.make_schema(M, columns)

        myschema_nodes = myschema.children
        for i, node in enumerate(schema):
            self.assertEqual(node.typ.__class__,
                    myschema_nodes[i].typ.__class__)
            self.assertEqual(node.required, myschema_nodes[i].required)

        self.assertEqual(schema.typ.__class__, myschema.typ.__class__)

    def test_make_schema_with_widget(self):
        import deform
        import sqlalchemy2deform

        M = self._makeModel()
        S = self._makeSchema()
        W = {'datetime_column': deform.widget.TextInputWidget}

        myschema = S()
        schema = sqlalchemy2deform.make_schema(M, widgets=W)

        myschema_nodes = myschema.children
        for i, node in enumerate(schema):
            self.assertEqual(node.typ.__class__,
                    myschema_nodes[i].typ.__class__)
            self.assertEqual(node.required, myschema_nodes[i].required)
            widget = W.get(node.name)
            if (widget):
                self.assertEqual(node.widget, widget)

        self.assertEqual(schema.typ.__class__, myschema.typ.__class__)

    def test_make_form(self):
        import deform
        import sqlalchemy2deform

        M = self._makeModel()
        S = self._makeSchema()

        myform = deform.Form(S(), buttons=('submit',))
        form = sqlalchemy2deform.make_form(M)

        self.assertEqual(form.render(), myform.render())

    def test_make_form_using_instance(self):
        import deform
        import sqlalchemy2deform

        M = self._makeModel()
        S = self._makeSchema()

        appstruct = {'unicode_column': u'unicode text (áç¢)',
                'float_column': 5.3}
        m = M(**appstruct)

        myform = deform.Form(S(), buttons=('submit',))
        form = sqlalchemy2deform.make_form(m)

        self.assertEqual(form.render(), myform.render(appstruct))


class TestModel(unittest.TestCase):
    def _makeModel(self):
        """ Make a sqlalchemy model. """
        from sqlalchemy2deform import Column
        from sqlalchemy.types import Unicode
        from sqlalchemy.types import Integer
        from sqlalchemy.types import Float
        from sqlalchemy.types import DateTime
        from sqlalchemy.ext.declarative import declarative_base
        Base = declarative_base()

        class Model(Base):
            __tablename__ = 'model'

            id_column = Column(Integer, primary_key=True, autoincrement=True,
                    title='Id number')
            unicode_column = Column(Unicode, nullable=False,
                    default='Default Text', title='Just a Unicode column')
            integer_column = Column(Integer, default=10)
            float_column = Column(Float)
            datetime_column = Column(DateTime)

        return Model

    def _makeSchema(self, nodes=None):
        """ Make a colander schema. """
        return schema_factory(nodes)

    def test_make_schema_with_columns(self):
        import sqlalchemy2deform

        columns = ['unicode_column', 'datetime_column']

        M = self._makeModel()
        S = self._makeSchema(columns)

        myschema = S()
        schema = sqlalchemy2deform.make_schema(M, columns)

        myschema_nodes = myschema.children
        for i, node in enumerate(schema):
            self.assertEqual(node.typ.__class__,
                    myschema_nodes[i].typ.__class__)
            self.assertEqual(node.required, myschema_nodes[i].required)

        self.assertEqual(schema.typ.__class__, myschema.typ.__class__)

    def test_make_schema_with_widget(self):
        import deform
        import sqlalchemy2deform

        M = self._makeModel()
        S = self._makeSchema()
        W = {'datetime_column': deform.widget.TextInputWidget}

        myschema = S()
        schema = sqlalchemy2deform.make_schema(M, widgets=W)

        myschema_nodes = myschema.children
        for i, node in enumerate(schema):
            self.assertEqual(node.typ.__class__,
                    myschema_nodes[i].typ.__class__)
            self.assertEqual(node.required, myschema_nodes[i].required)
            widget = W.get(node.name)
            if (widget):
                self.assertEqual(node.widget, widget)

        self.assertEqual(schema.typ.__class__, myschema.typ.__class__)


class TestColumn(unittest.TestCase):
    def _makeMe(self, type_, *args, **kw):
        from sqlalchemy2deform import Column
        return Column(type_, *args, **kw)

    def test___init__(self):
        from sqlalchemy.types import Unicode
        # TODO: test the arguments and the keywords arguments

        kw = {'title': '',
              'description': '',
              'widget': '',
              'missing': '',
              'preparer': '',
              'validator': '',
              'after_bind': '',
              'name': '',
              'default': ''}
        self._makeMe(Unicode, **kw)

    def test_schema(self):
        from sqlalchemy.types import Unicode
        import colander

        column = self._makeMe(Unicode)
        schema = column.schema

        myschema = colander.SchemaNode(colander.String(),
                missing=colander.null)

        self.assertEqual(schema.typ.__class__, myschema.typ.__class__)
        self.assertEqual(schema.required, myschema.required)

    def test_render(self):
        from sqlalchemy.types import Unicode
        import colander
        import deform

        column = self._makeMe(Unicode, default='Default Value')

        schema = colander.SchemaNode(colander.String(), missing=colander.null,
                default='Default Value')
        field = deform.Field(schema)
        widget = column.widget

        self.assertEqual(column.render(),
                widget.serialize(field, 'Default Value'))
