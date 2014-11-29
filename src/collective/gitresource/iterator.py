# -*- coding: utf-8 -*-
from io import BytesIO
from ZPublisher.Iterators import IStreamIterator
from zope.interface import implementer


@implementer(IStreamIterator)
class BytesIterator(BytesIO):
    """Resource iterator that allows (inefficient) coercion to str/unicode.

    This is needed for ResourceRegistries support, for example.
    """

    def __init__(self, data, stream_size=1 << 16):
        super(BytesIterator, self).__init__(data)
        self.stream_size = stream_size

    def next(self):
        data = self.read(self.stream_size)
        if not data:
            raise StopIteration
        return data

    def __len__(self):
        cur_pos = self.tell()
        self.seek(0, 2)
        size = self.tell()
        self.seek(cur_pos, 0)

        return size

    def __str__(self):
        return self.read()

    def __unicode__(self):
        return self.read().decode('utf-8')