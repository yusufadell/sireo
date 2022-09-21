import sys

sys.path.append("../sireo/")
import sireo
from sireo.runner import ARunner


@sireo.track("yusuf")
def my_experiment(one, two):
    print(one, two)
    return one + two


sireo.init(
    path="./my-results",
)

my_experiment(1, 3)
