import pytest
from pytest import importorskip

pytest.skip([1,2])  ## error, does not exist
importorskip()  ## bad, wrong number of args
