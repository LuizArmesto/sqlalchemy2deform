# -*- coding: utf-8 -*-
""" Create a colander Schema and a deform Form from sqlalchemy Models. """

from __future__ import unicode_literals  # unicode by default

from collections import OrderedDict

from sqlalchemy import types as sa_types
from sqlalchemy import Column as SAColumn
from sqlalchemy import ForeignKey as SAForeignKey
from sqlalchemy.orm import class_mapper

import colander
import deform

# TODO: * Map the sqlalchemy types to deform widgets
#       * Work with relationships

__all__ = ['Column', 'get_required_columns', 'get_autoincrement_columns',
    'make_schema', 'make_form']

# Map sqlalchemy types to colander types.
_TYPES = {
    sa_types.BigInteger: colander.Integer,
    sa_types.Boolean: colander.Boolean,
    sa_types.Date: colander.Date,
    sa_types.DateTime: colander.DateTime,
    sa_types.Enum: colander.String,
    sa_types.Float: colander.Float,
    sa_types.Integer: colander.Integer,
    sa_types.Numeric: colander.Decimal,
    sa_types.SmallInteger: colander.Integer,
    sa_types.String: colander.String,
    sa_types.Text: colander.String,
    sa_types.Time: colander.Time,
    sa_types.Unicode: colander.String,
    sa_types.UnicodeText: colander.String,
}

# Map sqlalchemy types to deform widgets.
_WIDGETS = {
    sa_types.BigInteger: deform.widget.TextInputWidget,
    sa_types.Boolean: deform.widget.CheckboxWidget,
    sa_types.Date: deform.widget.DateInputWidget,
    sa_types.DateTime: deform.widget.DateTimeInputWidget,
    sa_types.Enum: deform.widget.SelectWidget,
    sa_types.Float: deform.widget.TextInputWidget,
    sa_types.Integer: deform.widget.TextInputWidget,
    sa_types.Numeric: deform.widget.TextInputWidget,
    sa_types.SmallInteger: deform.widget.TextInputWidget,
    sa_types.String: deform.widget.TextInputWidget,
    sa_types.Text: deform.widget.TextAreaWidget,
    sa_types.Time: deform.widget.TextInputWidget,
    sa_types.Unicode: deform.widget.TextInputWidget,
    sa_types.UnicodeText: deform.widget.TextAreaWidget,
}


class Column(SAColumn):
    """ Extends 'sqlalchemy.Column'. """

    def __init__(self, *args, **kw):
        co_kw = {}
        # Look for colander arguments.
        for key in ['title', 'description', 'widget', 'missing', 'preparer',
                'validator', 'after_bind', 'name', 'default']:
            if key in kw:
                if key in ['name', 'default']:
                    # 'name' and 'default' are also sqlalchemy valid arguments.
                    co_kw[key] = kw.get(key, None)
                else:
                    # sqlalchemy invalid arguments must be removed.
                    co_kw[key] = kw.pop(key)
        # Initialize the sqlalchemy Column.
        super(Column, self).__init__(*args, **kw)
        sa_type = self.type.__class__
        # Get some sqlalchemy mapper info to pass the appropriate arguments
        # to colander.
        if not 'missing' in co_kw:
            co_kw['missing'] = colander.null if self.nullable else \
                    colander.required
        if not 'widget' in co_kw:
            co_kw['widget'] = deform.widget.HiddenWidget() if \
                    self.autoincrement and self.primary_key else \
                    _get_widget_by_sa_type(sa_type)()
        co_type = _get_co_type_by_sa_type(sa_type)
        self.schema = colander.SchemaNode(co_type(), **co_kw)
        self.widget = co_kw['widget']
        self.__co_kw = co_kw

    def render(self, appstruct=colander.null, readonly=False, **kw):
        """ Create a deform.Field than render that. """
        appstruct = appstruct or self.__co_kw['default']
        field = deform.Field(self.schema, **kw)
        return self.widget.serialize(field, appstruct, readonly=readonly)


class ForeignKey(SAForeignKey):
    pass


class Form(deform.Form):
    """ Extends 'deform.Form' to allow autofill using sqlalchemy object. """
    def __init__(self, schema, object_=None, *args, **kw):
        super(Form, self).__init__(schema, *args, **kw)
        if object_:
            # Create the appstruct using the sqlalchemy 'object_' values.
            appstruct = schema.serialize()
            for attr, default in appstruct.items():
                # TODO: avoid fill password fields
                appstruct[attr] = getattr(object_, attr) or default
            self.appstruct = appstruct

    def render(self, appstruct=colander.null, readonly=False, *args, **kw):
        if not appstruct and hasattr(self, 'appstruct'):
            appstruct = self.appstruct
        return super(Form, self).render(appstruct, readonly, *args, **kw)


def _get_co_type_by_sa_type(type_):
    """ Returns the colander type that correspondents to the sqlalchemy type
    'type_'. """
    return _TYPES.get(type_) or _TYPES.get(type_.__bases__[0])


def _get_widget_by_sa_type(type_):
    """ Returns the deform widget that correspondents to the sqlalchemy type
    'type_'. """
    # Don't cover because widgets can be changed any time.
    return _WIDGETS.get(type_) or \
            _WIDGETS.get(type_.__bases__[0])  # pragma: no cover


def _get_columns_co_types(mapper):
    """ Returns an OrderedDict with the colander type for each column from
    'mapper'. """
    sa_columns = mapper.columns
    return OrderedDict(((sa_column.name,
                _get_co_type_by_sa_type(sa_column.type.__class__)) \
            for sa_column in sa_columns))


def is_required(column):
    return not column.nullable


def get_required_columns(model):
    """ Returns a list containing the names of required columns. """
    mapper = class_mapper(model)
    columns = mapper.columns
    return (column.name for column in columns if is_required(column))


def is_autoincrement(column):
    return column.autoincrement and column.primary_key


def get_autoincrement_columns(model):
    """ Returns a list containing the names of columns with autoincrement
    property. """
    mapper = class_mapper(model)
    columns = mapper.columns
    return (column.name for column in columns if is_autoincrement(column))


def make_schema(model, columns=None, widgets=None):
    """ Returns a colander.Schema created from the sqlalchemy 'model'. """
    if widgets is None:
        widgets = {}
    mapper = class_mapper(model)
    sa_columns = sa_columns_ = mapper.columns
    if columns is not None:
        sa_columns = (sa_columns_.get(column) for column in columns)
    schemanodes = {}
    for sa_column in sa_columns:
        column = sa_column.name
        if isinstance(sa_column, Column):
            schemanodes[column] = sa_column.schema
            # Use the widget passed as argument, otherwise use the default.
            widget = widgets.get(column)
            if widget:
                schemanodes[column].widget = widget
            else:
                schemanodes[column].widget = sa_column.widget
        else:
            # TODO: DRY
            sa_type = sa_column.type.__class__
            co_type = _get_co_type_by_sa_type(sa_type)
            missing = colander.required if is_required(sa_column) \
                    else colander.null
            widget = deform.widget.HiddenWidget() if \
                    is_autoincrement(sa_column) else widgets.get(column)
            schemanodes[column] = colander.SchemaNode(co_type(),
                    description=column, missing=missing, widget=widget)
    schema = type(b'Schema', (colander.Schema, ), schemanodes)
    return schema()


def make_form(model, *args, **kw):
    """ Returns a deform.Form using the colander.Schema created from
    'model'. """
    object_ = None
    # If we got an instance get the class
    if not isinstance(model, type):
        object_ = model
        model = model.__class__
    schema = make_schema(model, kw.get('column'), kw.get('widgets'))
    if not 'buttons' in kw:
        kw['buttons'] = ('submit',)
    return Form(schema, object_, *args, **kw)
