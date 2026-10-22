import bee
from bee.models import EnterpriseSize


def test_package_imports():
    assert bee.__version__
    assert EnterpriseSize.QSE.value == "QSE"
