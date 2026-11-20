"""Neural subsystem — classical models (MLP, Hopfield, …)."""

from .hopfield import HopfieldNetwork, demo_hopfield
from .mlp import MLP, demo_xor

__all__ = ["HopfieldNetwork", "demo_hopfield", "MLP", "demo_xor"]
