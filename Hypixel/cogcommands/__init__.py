from .stats import StatsCommands
from .modules import ModuleCommands
from .compare import CompareCommands
from .autostats import AutoStatsCommands
from .change_config import ChangeConfig
from .summary_stats import SummaryStatsCommands

from ..utils.abc import CompositeMetaClass

class CogCommands(StatsCommands, ModuleCommands, CompareCommands, AutoStatsCommands, ChangeConfig, SummaryStatsCommands, metaclass=CompositeMetaClass):
    """Joining commands"""