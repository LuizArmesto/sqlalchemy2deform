# -*- coding: utf-8 -*-
from __future__ import unicode_literals  # unicode by default

import datetime

import deform
from colander import Schema
from colander import SchemaNode
from colander import String as CoString
from colander import Integer as CoInteger
from colander import DateTime as CoDateTime

from sqlalchemy.types import Unicode
from sqlalchemy.types import Integer
from sqlalchemy.types import DateTime
from sqlalchemy.ext.declarative import declarative_base

from sqlalchemy2deform import Column
from sqlalchemy2deform import make_form

Base = declarative_base()


class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Unicode, nullable=False, title='Full Name')
    number = Column(Integer, default=10, title='Your Number',
            description='Tell us any number you like')
    birth_date = Column(DateTime)
    password = Column(Unicode, nullable=False,
            widget=deform.widget.PasswordWidget(size=20))


class UserColander(Schema):
    id = SchemaNode(CoInteger())
    name = SchemaNode(CoString(), title='Full Name')
    number = SchemaNode(CoInteger(), missing=10, title='Your Number',
            description='Tell us any number you like')
    birth_date = SchemaNode(CoDateTime())
    password = SchemaNode(CoString(),
            widget=deform.widget.PasswordWidget(size=20))


def example():
    form = make_form(User)
    form.render({'name': 'Luiz Armesto', 'number': 15,
            'birth_date': datetime.datetime.now()})


def deform_only():
    form = deform.Form(UserColander(), buttons=('submit',))
    form.render({'name': 'Luiz Armesto', 'number': 15,
            'birth_date': datetime.datetime.now()})


if __name__ == '__main__':
    from timeit import Timer
    number = 1000

    example()

    t = Timer(example)
    m = (1000 * min(t.repeat(number=number)) / number)
    print ('sqlalchemy2deform', "%.2f msec/pass" % m)

    t = Timer(deform_only)
    d = (1000 * min(t.repeat(number=number)) / number)
    print ('Deform only', "%.2f msec/pass" % d)

    print (m / d)
