# -*- coding: utf-8 -*-
from __future__ import unicode_literals  # unicode by default

import datetime

import deform

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


def example_one():
    form = make_form(User)
    print form.render({'name': 'Luiz Armesto', 'number': 15,
            'birth_date': datetime.datetime.now()})


def example_two():
    user = User(name='Zé', number=13, birth_date=datetime.datetime.now(),
            password='s3cr3t')
    form = make_form(user, column=['name', 'password'],
            widgets={'name': deform.widget.TextAreaWidget()})
    print form.render()
    form = make_form(user)
    print form.render()

if __name__ == '__main__':
    example_two()
