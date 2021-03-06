"""Helper functions and classes for users.

They should not be used in skorch directly.

"""
from functools import partial
from skorch.utils import _make_split
from skorch.utils import _make_optimizer


class SliceDict(dict):
    """Wrapper for Python dict that makes it sliceable across values.

    Use this if your input data is a dictionary and you have problems
    with sklearn not being able to slice it. Wrap your dict with
    SliceDict and it should usually work.

    Note: SliceDict cannot be indexed by integers, if you want one
    row, say row 3, use `[3:4]`.

    Examples
    --------
    >>> X = {'key0': val0, 'key1': val1}
    >>> search = GridSearchCV(net, params, ...)
    >>> search.fit(X, y)  # raises error
    >>> Xs = SliceDict(key0=val0, key1=val1)  # or Xs = SliceDict(**X)
    >>> search.fit(Xs, y)  # works

    """
    def __init__(self, **kwargs):
        lengths = [value.shape[0] for value in kwargs.values()]
        lengths_set = set(lengths)
        if lengths_set and (len(lengths_set) != 1):
            raise ValueError(
                "Initialized with items of different lengths: {}"
                "".format(', '.join(map(str, sorted(lengths_set)))))

        if not lengths:
            self._len = 0
        else:
            self._len = lengths[0]

        super(SliceDict, self).__init__(**kwargs)

    def __len__(self):
        return self._len

    def __getitem__(self, sl):
        if isinstance(sl, int):
            # Indexing with integers is not well-defined because that
            # recudes the dimension of arrays by one, messing up
            # lengths and shapes.
            raise ValueError("SliceDict cannot be indexed by integers.")
        if isinstance(sl, str):
            return super(SliceDict, self).__getitem__(sl)
        return SliceDict(**{k: v[sl] for k, v in self.items()})

    def __setitem__(self, key, value):
        if not isinstance(key, str):
            raise TypeError("Key must be str, not {}.".format(type(key)))

        length = value.shape[0]
        if not self.keys():
            self._len = length

        if self._len != length:
            raise ValueError(
                "Cannot set array with shape[0] != {}"
                "".format(self._len))

        super(SliceDict, self).__setitem__(key, value)

    def update(self, kwargs):
        for key, value in kwargs.items():
            self.__setitem__(key, value)

    def __repr__(self):
        out = super(SliceDict, self).__repr__()
        return "SliceDict(**{})".format(out)

    @property
    def shape(self):
        return (self._len,)


def filter_requires_grad(pgroups):
    """Returns parameter groups where parameters
    that don't require a gradient are filtered out.

    Parameters
    ----------
    pgroups : dict
      Parameter groups to be filtered

    """
    for pgroup in pgroups:
        output = {k: v for k, v in pgroup.items() if k != 'params'}
        output['params'] = (p for p in pgroup['params'] if p.requires_grad)
        yield output


def filtered_optimizer(optimizer, filter_fn):
    """Wraps an optimizer that filters out parameters where
    ``filter_fn`` over ``pgroups`` returns ``False``.
    This function can be used, for example, to filter parameters
    that do not require a gradient:

    >>> from skorch.helper import filtered_optimizer, filter_requires_grad
    >>> optimizer = filtered_optimizer(torch.optim.SGD, filter_requires_grad)
    >>> net = NeuralNetClassifier(module, optimizer=optimizer)

    Parameters
    ----------
    optimizer : torch optim (class)
      The uninitialized optimizer that is wrapped

    filter_fn : function
      Use this function to filter parameter groups before passing
      it to ``optimizer``.

    """
    return partial(_make_optimizer, optimizer=optimizer, filter_fn=filter_fn)


def predefined_split(dataset):
    """Uses ``dataset`` for validiation in ``NeutralNet``.

    Examples
    --------
    >>> valid_ds = skorch.Dataset(X, y)
    >>> net = NeutralNet(..., train_split=predefined_split(valid_ds))

    Parameters
    ----------
    dataset: torch Dataset
       Validiation dataset

    """
    return partial(_make_split, valid_ds=dataset)
